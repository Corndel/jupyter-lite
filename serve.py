#!/usr/bin/env python3
"""Local dev server with headers required by JupyterLite.

JupyterLite's Pyodide kernel needs SharedArrayBuffer to access files,
which browsers only enable with these cross-origin isolation headers.
Netlify sets them via netlify.toml; this script does the same locally.

Usage:
    python serve.py              # serves dist/ on port 8000
    python serve.py 3000         # custom port
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, test


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    test(HandlerClass=partial(Handler, directory="dist"), port=port)
