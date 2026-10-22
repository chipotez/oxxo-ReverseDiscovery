"""Loopback-only local preview with production-equivalent security headers."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial
import argparse

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Content-Security-Policy', "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', default=4173, type=int)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1] / 'dist'
    if not (root / 'index.html').exists():
        parser.error('Run python3 scripts/build.py first')
    print(f'Local: http://127.0.0.1:{args.port}', flush=True)
    ThreadingHTTPServer(('127.0.0.1', args.port), partial(Handler, directory=str(root))).serve_forever()
