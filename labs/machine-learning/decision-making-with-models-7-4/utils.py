import mistune


def validate_recommendation(path="recommendation.md", min_words=15):
    """Check that every H2 section in the recommendation has at least `min_words` words."""
    with open(path) as f:
        text = f.read()

    md = mistune.create_markdown(renderer=None)
    tokens = md(text)

    sections = {}
    current_heading = None

    for token in tokens:
        if token["type"] == "heading" and token["attrs"]["level"] == 2:
            current_heading = _extract_text(token)
            sections[current_heading] = []
        elif current_heading is not None and token["type"] not in ("blank_line",):
            sections[current_heading].append(_extract_text(token))

    if not sections:
        print("ERROR: No H2 sections found in the file.")
        return False

    all_ok = True
    for heading, parts in sections.items():
        body = " ".join(parts)
        count = len(body.split())
        if count < min_words:
            print(f'NEEDS MORE: "{heading}" has {count} word(s) (minimum {min_words}).\n')
            all_ok = False
        else:
            print(f'OK: "{heading}" ({count} words)\n')

    if all_ok:
        print("All sections look good! 👍")
    else:
        print(
            f"Some sections need more detail. Aim for at least {min_words} words per section."
        )

    return all_ok


def _extract_text(token):
    """Recursively extract plain text from a mistune token."""
    if "raw" in token:
        return token["raw"]
    if "children" in token and token["children"]:
        return " ".join(_extract_text(child) for child in token["children"])
    if "text" in token:
        return token["text"]
    return ""
