#!/usr/bin/env python3
"""Static server with COOP/COEP headers for ffmpeg.wasm (SharedArrayBuffer)."""
import http.server, socketserver, functools, os, sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 12000
DIR = sys.argv[2] if len(sys.argv) > 2 else "."

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=DIR, **kw)
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        super().end_headers()
    def log_message(self, *a): pass

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True

with Server(("0.0.0.0", PORT), Handler) as s:
    s.daemon_threads = True
    print(f"serving {DIR} on :{PORT} (COOP/COEP)")
    s.serve_forever()
