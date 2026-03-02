#!/usr/bin/env python3
"""
Multi-module JupyterLite build script.

Builds JupyterLite once (expensive), then stamps out a complete per-module
copy with only that module's content. Each module is a self-contained
JupyterLite instance with no path rewriting needed.

Usage:
    python build.py                          # build all modules
    python build.py --modules python-101     # build one module
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
MODULES_DIR = REPO_ROOT / "modules"
SHARED_DIR = MODULES_DIR / "_shared"
BASE_BUILD_DIR = REPO_ROOT / "_base"
LANDING_TEMPLATE = REPO_ROOT / "landing" / "index.html"


def build_base():
    """Run the expensive JupyterLite build once, with no content."""
    print("==> Building JupyterLite base (no content)...")

    if BASE_BUILD_DIR.exists():
        shutil.rmtree(BASE_BUILD_DIR)

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


def get_modules(filter_list=None):
    """Discover module directories under modules/."""
    modules = []
    for entry in sorted(MODULES_DIR.iterdir()):
        if entry.is_dir() and not entry.name.startswith(("_", ".")):
            if filter_list is None or entry.name in filter_list:
                modules.append(entry)
    return modules


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


def stamp_module(module_dir, output_dir):
    """
    Create a module-specific JupyterLite instance by:
    1. Copying the entire base build (self-contained, no path tricks)
    2. Copying module content into files/
    3. Generating api/contents/ manifests
    4. Patching lab/index.html so the service worker is ready before boot
    """
    module_name = module_dir.name
    module_output = output_dir / module_name

    print(f"  -> Stamping module: {module_name}")

    # Copy the entire base build as-is
    if module_output.exists():
        shutil.rmtree(module_output)
    shutil.copytree(BASE_BUILD_DIR, module_output)

    # Copy module content into files/
    files_dir = module_output / "files"
    files_dir.mkdir(parents=True, exist_ok=True)

    # Shared content first (if _shared/ exists)
    if SHARED_DIR.is_dir():
        shutil.copytree(SHARED_DIR, files_dir, dirs_exist_ok=True)

    # Module-specific content (overwrites shared on conflict)
    for item in module_dir.iterdir():
        if item.name in ("module.json",):
            continue
        dest = files_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)

    # Generate api/contents/ manifests
    generate_manifests(files_dir, module_output)

    # Ensure service worker is active before JupyterLite boots
    patch_service_worker_ready(module_output)

    print(f"     Done: {module_output}")


def generate_landing_page(modules, output_dir):
    """Generate the landing page grouped by programme, with sandbox at the top."""
    # Load module metadata
    module_metas = []
    for module_dir in modules:
        meta_path = module_dir / "module.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        meta["_slug"] = module_dir.name
        meta.setdefault("title", module_dir.name.replace("-", " ").title())
        meta.setdefault("description", "")
        module_metas.append(meta)

    # Load programme list (defines order and allows empty programmes)
    programmes_path = REPO_ROOT / "programmes.json"
    if programmes_path.exists():
        programmes = json.loads(programmes_path.read_text())
    else:
        programmes = sorted({m.get("programme") for m in module_metas if m.get("programme")})

    # Split sandbox modules from programme modules
    sandboxes = [m for m in module_metas if m.get("sandbox")]
    programme_modules = [m for m in module_metas if not m.get("sandbox")]

    # Group modules by programme
    by_programme = {}
    for prog in programmes:
        by_programme[prog] = [m for m in programme_modules if m.get("programme") == prog]

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
      <div class="module-grid">
"""
        if mods:
            for m in mods:
                programmes_html += f"""        <a class="module-card" href="/{m['_slug']}/lab/index.html">
          <h3>{m['title']}</h3>
          <p>{m['description']}</p>
        </a>
"""
        else:
            programmes_html += """        <div class="programme-empty">No modules yet</div>
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
    print(f"==> Landing page: {output_dir / 'index.html'}")


def main():
    parser = argparse.ArgumentParser(description="Multi-module JupyterLite build")
    parser.add_argument(
        "--modules",
        help="Comma-separated module names to build (default: all)",
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
    filter_list = args.modules.split(",") if args.modules else None

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

    # Step 3: Stamp each module (full copy of base + module content)
    modules = get_modules(filter_list)
    if not modules:
        print("Warning: No modules found in modules/")
        sys.exit(1)

    print(f"==> Building {len(modules)} module(s)...")
    for module_dir in modules:
        stamp_module(module_dir, output_dir)

    # Step 4: Generate landing page
    all_modules = get_modules()  # always list all modules on landing page
    generate_landing_page(all_modules, output_dir)

    print(f"\n==> Build complete! Output: {output_dir}")
    print(f"    Serve with: python serve.py")


if __name__ == "__main__":
    main()
