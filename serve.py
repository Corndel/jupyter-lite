#!/usr/bin/env python3
"""Local dev server with headers required by JupyterLite.

JupyterLite's Pyodide kernel needs SharedArrayBuffer to access files,
which browsers only enable with these cross-origin isolation headers.
Netlify sets them via netlify.toml; this script does the same locally.

Uses ThreadingHTTPServer so concurrent requests (JS bundles, service
worker registration, kernel file-access XHRs) don't block each other.

Usage:
    python serve.py              # serves dist/ on port 8000
    python serve.py 3000         # custom port
"""

import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    # Bind to localhost — service workers and SharedArrayBuffer require a
    # secure context, which browsers only grant to https:// or
    # http://localhost.  Using 0.0.0.0 or 127.0.0.1 will silently break
    # the Pyodide kernel's file access.
    server = ThreadingHTTPServer(
        ("localhost", port), partial(Handler, directory="dist")
    )
    print(f"Serving dist/ at http://localhost:{port}")
    print(f"  ** You MUST open http://localhost:{port} (not 127.0.0.1 or 0.0.0.0) **")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()
