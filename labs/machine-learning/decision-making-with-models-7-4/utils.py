# =============================================================================
#
#   🚂  Unit 7.4 — From Metrics to Decisions
#   📦  Utility functions for the bearing inspection notebook
#
# =============================================================================
#
#   This file contains all helper functions used in the lab notebook.
#   Keeping them here means the notebook cells stay short and readable.
#
#   Contents
#   ────────
#   📊  plot_confusion_matrices(cm_a, cm_b)
#           Visual side-by-side confusion matrices with colour-coded cells
#           and a red border on the false negative cell for each model.
#
#   📈  plot_pr_curves(y, prob_a, prob_b)
#           Annotated precision-recall curves for both models, with the
#           default threshold 0.5 operating point marked on each.
#
#   🔢  operational_summary(y, pred_a, pred_b, images_per_week=2000)
#           Translates holdout set false negative rates into missed defects
#           per week and per year on a busy route.
#
#   🛑  check_response(label, text, min_words)
#           Validates an inline answer written in a code cell.
#           Raises ValueError if the response is a placeholder or too short.
#
#   ✅  validate_recommendation(path, sections, min_words)
#           Checks that specified sections of recommendation.md have been
#           filled in with at least min_words words each.
#           Anchors on the ANSWER: prefix inside each fenced block.
#
# =============================================================================

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display, Markdown


# ── Palette ──────────────────────────────────────────────────────────────────

_BLUE  = "#2a6ebb"
_AMBER = "#e67e22"
_RED   = "#c0392b"
_GREEN = "#27ae60"
_DARK  = "#1a1a2e"
_GREY  = "#666666"


# ── 📊 Confusion matrices ─────────────────────────────────────────────────────

def plot_confusion_matrices(cm_a, cm_b):
    """
    Display side-by-side colour-coded confusion matrices for Model A and B.
    The false negative cell (bottom-left) is highlighted with a red border.
    """
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle(
        "Confusion matrices at threshold 0.5  —  500-image holdout set",
        fontsize=12, fontweight="bold", y=1.02,
    )

    cell_labels = [
        ["True Negative\n(correctly cleared)", "False Positive\n(unnecessary flag)"],
        ["False Negative\n(missed defect)",    "True Positive\n(defect caught)"],
    ]
    cell_colours = [
        ["#f0f7f0", "#e8f4fd"],
        ["#fdecea", "#e8f8f0"],
    ]

    for ax, cm, name in zip(axes, [cm_a, cm_b], ["Model A", "Model B"]):
        tn, fp, fn, tp = cm.ravel()
        grid = [[tn, fp], [fn, tp]]

        for i in range(2):
            for j in range(2):
                rect = plt.Rectangle(
                    [j - 0.5, i - 0.5], 1, 1,
                    linewidth=2, edgecolor="#cccccc",
                    facecolor=cell_colours[i][j],
                )
                ax.add_patch(rect)

                if i == 1 and j == 0:
                    rect_fn = plt.Rectangle(
                        [j - 0.5, i - 0.5], 1, 1,
                        linewidth=3, edgecolor=_RED,
                        facecolor="none", zorder=5,
                    )
                    ax.add_patch(rect_fn)

                val_colour = (
                    _RED   if (i == 1 and j == 0) else
                    _GREEN if (i == 1 and j == 1) else
                    _DARK
                )
                ax.text(j, i, str(grid[i][j]),
                        ha="center", va="center",
                        fontsize=20, fontweight="bold", color=val_colour)
                ax.text(j, i + 0.32, cell_labels[i][j],
                        ha="center", va="center",
                        fontsize=7.5, color=_GREY)

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0
        acc  = (tp + tn) / cm.sum()

        ax.set_xlim(-0.5, 1.5)
        ax.set_ylim(-0.5, 1.5)
        ax.set_xticks([0, 1])
        ax.set_yticks([0, 1])
        ax.set_xticklabels(["Predicted\nno defect", "Predicted\ndefect"], fontsize=9)
        ax.set_yticklabels(["Actual\nno defect", "Actual\ndefect"], fontsize=9)
        ax.set_title(
            f"{name}\nAcc {acc:.1%}  |  Prec {prec:.1%}  |  Rec {rec:.1%}",
            fontsize=10, pad=8,
        )
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)

    fig.text(
        0.5, -0.04,
        "Red border = false negative (missed defect). "
        "This is the cell that matters most in this domain.",
        ha="center", fontsize=9, color=_RED, style="italic",
    )
    plt.tight_layout()
    plt.show()


# ── 📈 Precision-recall curves ────────────────────────────────────────────────

def plot_pr_curves(y, prob_a, prob_b):
    """
    Plot annotated precision-recall curves for both models.
    The default threshold 0.5 operating point is marked on each curve.
    """
    from sklearn.metrics import precision_recall_curve, precision_score, recall_score

    prec_a, rec_a, _ = precision_recall_curve(y, prob_a)
    prec_b, rec_b, _ = precision_recall_curve(y, prob_b)

    pred_a = (prob_a >= 0.5).astype(int)
    pred_b = (prob_b >= 0.5).astype(int)

    pa_05 = precision_score(y, pred_a)
    ra_05 = recall_score(y, pred_a)
    pb_05 = precision_score(y, pred_b)
    rb_05 = recall_score(y, pred_b)

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(rec_a, prec_a, color=_BLUE,  linewidth=2,   label="Model A", alpha=0.85)
    ax.plot(rec_b, prec_b, color=_AMBER, linewidth=2.5, label="Model B")

    ax.scatter([ra_05], [pa_05], color=_BLUE,  s=90, zorder=6)
    ax.scatter([rb_05], [pb_05], color=_AMBER, s=90, zorder=6)

    ax.annotate(
        f"Model A at 0.5\n({pa_05:.0%} prec, {ra_05:.0%} rec)",
        xy=(ra_05, pa_05), xytext=(ra_05 - 0.28, pa_05 - 0.1),
        fontsize=8, color=_BLUE,
        arrowprops=dict(arrowstyle="->", color=_BLUE, lw=1),
    )
    ax.annotate(
        f"Model B at 0.5\n({pb_05:.0%} prec, {rb_05:.0%} rec)",
        xy=(rb_05, pb_05), xytext=(rb_05 - 0.25, pb_05 - 0.13),
        fontsize=8, color=_AMBER,
        arrowprops=dict(arrowstyle="->", color=_AMBER, lw=1),
    )

    ax.set_xlabel("Recall  (fraction of actual defects caught)", fontsize=11)
    ax.set_ylabel("Precision  (fraction of flags that are real defects)", fontsize=11)
    ax.set_title("Precision vs recall at every possible threshold",
                 fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.set_xlim(0, 1.05)
    ax.set_ylim(0, 1.08)
    ax.grid(True, alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()
    plt.show()


# ── 🔢 Operational summary ────────────────────────────────────────────────────

def operational_summary(y, pred_a, pred_b, images_per_week=2000):
    """
    Translate holdout set false negative rates into missed defects per week
    and per year. Uses default threshold predictions for a fair comparison.
    """
    from sklearn.metrics import confusion_matrix

    defect_rate      = y.mean()
    expected_defects = images_per_week * defect_rate

    fn_rate_a = confusion_matrix(y, pred_a)[1, 0] / y.sum()
    fn_rate_b = confusion_matrix(y, pred_b)[1, 0] / y.sum()

    missed_a = expected_defects * fn_rate_a
    missed_b = expected_defects * fn_rate_b
    diff     = missed_a - missed_b

    print(f"At {images_per_week:,} images per week "
          f"(both models at default threshold 0.5):")
    print(f"  Expected defects per week          : {expected_defects:.0f}")
    print()
    print(f"  Model A  missed defects per week   : {missed_a:.1f}")
    print(f"  Model B  missed defects per week   : {missed_b:.1f}")
    print()
    print(f"  Extra missed defects/week  with A  : {diff:.1f}")
    print(f"  Extra missed defects/year  with A  : {diff * 52:.0f}")


# ── 🛑 Inline response checker ────────────────────────────────────────────────

def check_response(label, text, min_words):
    """
    Validate an inline response written in a notebook code cell.
    Raises ValueError if the response is a placeholder or below min_words.
    """
    placeholder_phrases = [
        "replace this", "your answer", "write here",
        "answer here", "type here", "enter your", "insert your",
    ]
    lower = text.lower().strip()

    if not lower:
        raise ValueError(
            f"\n[{label}] Response is empty. "
            f"Write your answer before running this cell."
        )
    for phrase in placeholder_phrases:
        if phrase in lower:
            raise ValueError(
                f"\n[{label}] The placeholder text is still there. "
                f"Replace it with your own writing."
            )
    word_count = len(text.split())
    if word_count < min_words:
        raise ValueError(
            f"\n[{label}] Your response is {word_count} word(s). "
            f"This question needs at least {min_words} words. "
            f"Be more specific."
        )
    return text.strip()


# ── ✅ Recommendation validator ───────────────────────────────────────────────

def validate_recommendation(path="recommendation.md", sections=None, min_words=15):
    """
    Check that specified sections of recommendation.md have been filled in.

    Each section must contain a fenced block with a line starting 'ANSWER:'.
    The validator strips the 'ANSWER:' prefix before counting words.

    Parameters
    ----------
    path      : str       — path to the recommendation file
    sections  : list[int] — section numbers to check (1-indexed). None = all.
    min_words : int       — minimum word count required per section answer.

    Raises ValueError if any required section is missing, untouched, or brief.
    """
    with open(path, encoding="utf-8") as f:
        text = f.read()

    raw_sections = []
    current_num  = None
    current_head = None
    in_fence     = False
    fence_lines  = []
    body_lines   = []

    for line in text.splitlines():
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_fence:
                in_fence = False
                if current_head is not None:
                    body_lines.extend(fence_lines)
                fence_lines = []
            else:
                in_fence = True
            continue

        if in_fence:
            fence_lines.append(stripped)
            continue

        if stripped.startswith("## "):
            if current_head is not None:
                raw_sections.append(
                    (current_num, current_head, " ".join(body_lines).strip())
                )
            heading_text = stripped[3:].strip()
            try:
                current_num = int(heading_text.split(".")[0].strip())
            except ValueError:
                current_num = None
            current_head = heading_text
            body_lines   = []

        elif current_head is not None and stripped:
            if not (stripped.startswith("*") or stripped.startswith("_")
                    or stripped == "---"):
                body_lines.append(stripped)

    if current_head is not None:
        raw_sections.append(
            (current_num, current_head, " ".join(body_lines).strip())
        )

    raw_sections = [(n, h, b) for n, h, b in raw_sections if n is not None]

    if not raw_sections:
        raise ValueError(
            "\n[recommendation.md] No numbered sections found. "
            "Make sure each heading starts with its number, "
            "e.g. '## 1. Who is most at risk...'"
        )

    to_check = (
        [s for s in raw_sections if s[0] in sections]
        if sections else raw_sections
    )

    PLACEHOLDER = "replace this line with your answer"
    problems = []

    for num, heading, body in to_check:
        answer = body
        if answer.upper().startswith("ANSWER:"):
            answer = answer[len("ANSWER:"):].strip()

        if not answer or answer.lower().strip() == PLACEHOLDER:
            problems.append(
                f"\n  Section {num}: not started yet.\n"
                f"  Open recommendation.md and replace the ANSWER: line."
            )
            continue

        if PLACEHOLDER in answer.lower():
            problems.append(
                f"\n  Section {num}: still contains the placeholder text.\n"
                f"  Replace the entire ANSWER: line with your own writing."
            )
            continue

        word_count = len(answer.split())
        if word_count < min_words:
            problems.append(
                f"\n  Section {num}: {word_count} word(s) — aim for at "
                f"least {min_words}. Be more specific."
            )
        else:
            print(f"  ✓  Section {num}: {word_count} words")

    if problems:
        raise ValueError(
            "\nSome sections need more work before you can continue:"
            + "".join(problems)
            + "\n\nOpen recommendation.md in the file browser on the left "
              "(click the folder icon if you cannot see it), update those "
              "sections, save the file, then re-run this cell."
        )

    print("\nAll checked sections look good. Continue to the next cell.")
