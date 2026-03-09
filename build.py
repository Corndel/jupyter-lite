#!/usr/bin/env python3
"""
Multi-module JupyterLite build script.

Builds JupyterLite once (expensive), then stamps out a complete per-module
copy with only that module's content. Each module is a self-contained
JupyterLite instance with no path rewriting needed.

Usage:
    python build.py                          # build all labs
    python build.py --labs python-foundations # build one lab
    python build.py --skip-base              # reuse existing _base/
    python build.py --output-dir dist        # custom output directory
"""

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).parent
LABS_DIR = REPO_ROOT / "labs"
SHARED_DIR = LABS_DIR / "_shared"
BASE_BUILD_DIR = REPO_ROOT / "_base"
LANDING_TEMPLATE = REPO_ROOT / "landing" / "index.html"


def build_base():
    """Run the expensive JupyterLite build once, with no content."""
    print("==> Building JupyterLite base (no content)...")

    if BASE_BUILD_DIR.exists():
        shutil.rmtree(BASE_BUILD_DIR)

    # Clean stale doit state and default _output/ that jupyter-lite leaves
    # behind — they confuse the task runner when --output-dir is overridden.
    for stale in [REPO_ROOT / ".jupyterlite.doit.db", REPO_ROOT / "_output"]:
        if stale.is_dir():
            shutil.rmtree(stale)
        elif stale.exists():
            stale.unlink()

    subprocess.run(
        [
            sys.executable, "-m", "jupyter", "lite", "build",
            "--output-dir", str(BASE_BUILD_DIR),
        ],
        check=True,
        cwd=str(REPO_ROOT),
    )

    # Remove default content artifacts from the base (we inject per-module)
    for artifact in ["files", "api/contents"]:
        p = BASE_BUILD_DIR / artifact
        if p.exists():
            shutil.rmtree(p)

    print(f"==> Base build complete: {BASE_BUILD_DIR}")


def get_labs(filter_list=None):
    """Discover lab directories under labs/ (supports course nesting).

    A lab is any directory containing a lab.json file.  Its course (programme)
    is read from course.json in the parent directory, if present.
    """
    labs = []
    for lab_json in sorted(LABS_DIR.rglob("lab.json")):
        lab_dir = lab_json.parent
        if any(part.startswith(("_", ".")) for part in lab_dir.relative_to(LABS_DIR).parts):
            continue
        if filter_list is None or lab_dir.name in filter_list:
            labs.append(lab_dir)
    return labs


def get_lab_meta(lab_dir):
    """Load lab metadata, inheriting the course title from course.json."""
    lab_json = lab_dir / "lab.json"
    meta = json.loads(lab_json.read_text()) if lab_json.exists() else {}
    meta["_slug"] = lab_dir.name
    meta.setdefault("title", lab_dir.name.replace("-", " ").title())
    meta.setdefault("description", "")

    # Inherit programme from parent course.json
    course_json = lab_dir.parent / "course.json"
    if course_json.exists() and "programme" not in meta:
        course = json.loads(course_json.read_text())
        meta["programme"] = course.get("title", "")

    return meta


def generate_manifests(files_dir, module_output):
    """
    Generate Jupyter Contents API all.json manifests for a directory tree.

    Replicates what `jupyter lite build` does for content indexing: each
    directory gets an all.json with metadata-only entries (content: null)
    for its children.
    """
    now = datetime.now(timezone.utc).isoformat()
    api_base = module_output / "api" / "contents"

    def make_entry(file_path, rel_path):
        name = file_path.name
        if file_path.is_dir():
            return {
                "content": None,
                "created": now,
                "format": None,
                "hash": None,
                "hash_algorithm": None,
                "last_modified": now,
                "mimetype": None,
                "name": name,
                "path": rel_path,
                "size": None,
                "type": "directory",
                "writable": True,
            }
        else:
            size = file_path.stat().st_size
            ftype = "notebook" if name.endswith(".ipynb") else "file"
            return {
                "content": None,
                "created": now,
                "format": None,
                "hash": None,
                "hash_algorithm": None,
                "last_modified": now,
                "mimetype": None,
                "name": name,
                "path": rel_path,
                "size": size,
                "type": ftype,
                "writable": True,
            }

    def process_dir(dir_path, rel_prefix):
        entries = []
        for child in sorted(dir_path.iterdir()):
            if child.name.startswith("."):
                continue
            child_rel = f"{rel_prefix}/{child.name}" if rel_prefix else child.name
            entries.append(make_entry(child, child_rel))
            if child.is_dir():
                process_dir(child, child_rel)

        manifest = {
            "content": entries,
            "created": now,
            "format": "json",
            "hash": None,
            "hash_algorithm": None,
            "last_modified": now,
            "mimetype": None,
            "name": Path(rel_prefix).name if rel_prefix else "",
            "path": rel_prefix,
            "size": None,
            "type": "directory",
            "writable": True,
        }

        manifest_dir = api_base / rel_prefix if rel_prefix else api_base
        manifest_dir.mkdir(parents=True, exist_ok=True)
        with open(manifest_dir / "all.json", "w") as f:
            json.dump(manifest, f, indent=2)

    process_dir(files_dir, "")


def strip_notebook_outputs(files_dir):
    """Remove cell outputs from all notebooks so learners start fresh."""
    for nb_path in files_dir.rglob("*.ipynb"):
        nb = json.loads(nb_path.read_text())
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
        nb_path.write_text(json.dumps(nb, indent=1) + "\n")


def patch_custom_css(module_output):
    """
    Inject a <link> to custom.css into every entry-point index.html.
    The CSS file is copied to the module output root during stamp_module.
    """
    for html_file in module_output.rglob("index.html"):
        html = html_file.read_text()
        if "custom.css" in html:
            continue
        marker = "</head>"
        if marker not in html:
            continue
        rel = html_file.parent.relative_to(module_output)
        depth = len(rel.parts)
        css_path = "../" * depth + "custom.css" if depth else "./custom.css"
        link_tag = f'    <link rel="stylesheet" href="{css_path}" />\n  '
        html = html.replace(marker, link_tag + marker)
        html_file.write_text(html)


def patch_service_worker_ready(module_output):
    """
    Patch every entry-point index.html to pre-register the service worker
    and wait for it to be active BEFORE booting JupyterLite.

    The Pyodide kernel accesses files via synchronous XHR that the service
    worker must intercept.  Without this patch there is a race: JupyterLite
    can open a notebook and start the kernel before the SW is active,
    causing every `open()` call to fail with FileNotFoundError.
    """
    for html_file in module_output.rglob("index.html"):
        html = html_file.read_text()

        # Each entry-point loads config-utils.js relative to its own depth.
        # Match "await import(\n  '<dots>/config-utils.js" regardless of
        # the relative prefix, and insert the SW gate just before it.
        marker = "await import("
        if marker not in html or "config-utils.js" not in html:
            continue

        # Find the exact indented line so we preserve formatting.
        idx = html.index(marker)
        # Walk backwards to find the start of the line (for indentation).
        line_start = html.rfind("\n", 0, idx) + 1
        indent = html[line_start:idx]

        # Determine the relative path to service-worker.js from this file.
        rel = html_file.parent.relative_to(module_output)
        depth = len(rel.parts)  # e.g. lab/ → 1, consoles/ → 1, root → 0
        sw_path = "../" * depth + "service-worker.js" if depth else "./service-worker.js"

        sw_gate = (
            f"{indent}// Ensure the service worker is active before JupyterLite boots.\n"
            f"{indent}// The Pyodide kernel relies on the SW to relay file-system requests;\n"
            f"{indent}// without it every open() in a notebook would fail.\n"
            f"{indent}if ('serviceWorker' in navigator) {{\n"
            f"{indent}  try {{\n"
            f"{indent}    await navigator.serviceWorker.register('{sw_path}');\n"
            f"{indent}    await navigator.serviceWorker.ready;\n"
            f"{indent}  }} catch (_e) {{ /* proceed without SW */ }}\n"
            f"{indent}}}\n"
        )

        # Insert before the "await import" line, keeping original indent.
        html = html[:line_start] + sw_gate + html[line_start:]
        html_file.write_text(html)


def stamp_lab(lab_dir, output_dir):
    """
    Create a lab-specific JupyterLite instance by:
    1. Copying the entire base build (self-contained, no path tricks)
    2. Copying lab content into files/
    3. Generating api/contents/ manifests
    4. Patching index.html so the service worker is ready before boot
    """
    lab_name = lab_dir.name
    lab_output = output_dir / lab_name

    print(f"  -> Stamping lab: {lab_name}")

    # Copy the entire base build as-is
    if lab_output.exists():
        shutil.rmtree(lab_output)
    shutil.copytree(BASE_BUILD_DIR, lab_output)

    # Copy lab content into files/
    files_dir = lab_output / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    # Shared content first (if _shared/ exists)
    if SHARED_DIR.is_dir():
        shutil.copytree(SHARED_DIR, files_dir, dirs_exist_ok=True)

    # Lab-specific content (overwrites shared on conflict)
    for item in lab_dir.iterdir():
        if item.name in ("lab.json",):
            continue
        dest = files_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    # Strip saved outputs from notebooks so learners step through fresh
    strip_notebook_outputs(files_dir)

    # Generate api/contents/ manifests
    generate_manifests(files_dir, lab_output)

    # Copy custom stylesheet and fonts into lab root
    custom_css = REPO_ROOT / "custom.css"
    if custom_css.exists():
        shutil.copy2(custom_css, lab_output / "custom.css")
        patch_custom_css(lab_output)
    fonts_dir = REPO_ROOT / "fonts"
    if fonts_dir.is_dir():
        shutil.copytree(fonts_dir, lab_output / "fonts", dirs_exist_ok=True)

    # Ensure service worker is active before JupyterLite boots
    patch_service_worker_ready(lab_output)

    print(f"     Done: {lab_output}")


def generate_landing_page(labs, output_dir):
    """Generate the landing page grouped by programme, with sandbox at the top."""
    # Load lab metadata (course title inherited from course.json)
    lab_metas = []
    for lab_dir in labs:
        lab_metas.append(get_lab_meta(lab_dir))

    # Load programme list (defines order and allows empty programmes)
    programmes_path = REPO_ROOT / "programmes.json"
    if programmes_path.exists():
        programmes = json.loads(programmes_path.read_text())
    else:
        programmes = sorted({m.get("programme") for m in lab_metas if m.get("programme")})

    # Split sandbox modules from programme modules
    sandboxes = [m for m in lab_metas if m.get("sandbox")]
    programme_labs = [m for m in lab_metas if not m.get("sandbox")]

    # Group modules by programme
    by_programme = {}
    for prog in programmes:
        by_programme[prog] = sorted(
            [m for m in programme_labs if m.get("programme") == prog],
            key=lambda m: (m.get("order", 999), m.get("title", "")),
        )

    # Build sandbox section HTML
    sandbox_html = ""
    for m in sandboxes:
        sandbox_html += f"""    <div class="sandbox-section">
      <a class="sandbox-card" href="/{m['_slug']}/lab/index.html">
        <div class="sandbox-icon">
          <svg viewBox="0 0 24 24"><path d="M20 6h-8l-2-2H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-6 10h-4v-4H8l4-4 4 4h-2v4z"/></svg>
        </div>
        <div class="sandbox-text">
          <h2>{m['title']}</h2>
          <p>{m['description']}</p>
        </div>
      </a>
    </div>
"""

    # Build programme sections HTML
    programmes_html = ""
    for prog_name in programmes:
        mods = by_programme.get(prog_name, [])
        programmes_html += f"""    <div class="programme-section">
      <div class="programme-heading">{prog_name}</div>
      <div class="lab-grid">
"""
        if mods:
            for m in mods:
                order = m.get("order", "")
                number_html = f'<span class="lab-card-number">Lab {order}</span>\n          ' if order else ""
                programmes_html += f"""        <a class="lab-card" href="/{m['_slug']}/lab/index.html">
          {number_html}<h3>{m['title']}</h3>
          <p>{m['description']}</p>
        </a>
"""
        else:
            programmes_html += """        <div class="programme-empty">No labs yet</div>
"""
        programmes_html += """      </div>
    </div>
"""

    # Inject into template
    if LANDING_TEMPLATE.exists():
        html = LANDING_TEMPLATE.read_text()
        html = html.replace("<!-- SANDBOX_SECTION -->", sandbox_html)
        html = html.replace("<!-- PROGRAMME_SECTIONS -->", programmes_html)
    else:
        html = f"<html><body>{sandbox_html}{programmes_html}</body></html>"

    (output_dir / "index.html").write_text(html)

    # Copy static assets from landing/ (fonts, images, etc.)
    landing_dir = LANDING_TEMPLATE.parent
    for item in landing_dir.iterdir():
        if item.name == "index.html":
            continue
        dest = output_dir / item.name
        if item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
        else:
            shutil.copy2(item, dest)

    print(f"==> Landing page: {output_dir / 'index.html'}")


def main():
    parser = argparse.ArgumentParser(description="Multi-module JupyterLite build")
    parser.add_argument(
        "--labs",
        help="Comma-separated lab names to build (default: all)",
    )
    parser.add_argument(
        "--output-dir",
        default="dist",
        help="Output directory (default: dist)",
    )
    parser.add_argument(
        "--skip-base",
        action="store_true",
        help="Skip the base JupyterLite build (reuse existing _base/)",
    )
    args = parser.parse_args()

    output_dir = REPO_ROOT / args.output_dir
    filter_list = args.labs.split(",") if args.labs else None

    # Clean dist/ first so `jupyter lite build` doesn't find stale
    # jupyter-lite.json files from a previous build
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Step 1: Build base (expensive, ~60-90s)
    if args.skip_base:
        if not BASE_BUILD_DIR.exists():
            print("Error: --skip-base specified but _base/ does not exist.")
            print("Run without --skip-base first.")
            sys.exit(1)
        print("==> Skipping base build (reusing _base/)")
    else:
        build_base()

    # Step 2: Set up output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 3: Stamp each lab (full copy of base + lab content)
    labs = get_labs(filter_list)
    if not labs:
        print("Warning: No labs found in labs/")
        sys.exit(1)

    print(f"==> Building {len(labs)} lab(s)...")
    for lab_dir in labs:
        stamp_lab(lab_dir, output_dir)

    # Step 4: Generate landing page
    all_labs = get_labs()  # always list all labs on landing page
    generate_landing_page(all_labs, output_dir)

    print(f"\n==> Build complete! Output: {output_dir}")
    print(f"    Serve with: python serve.py")


if __name__ == "__main__":
    main()
