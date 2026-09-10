"""Local-only static export preview with API proxy; production uses Nginx."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import http.client
import os

class Handler(SimpleHTTPRequestHandler):
    def proxy(self) -> None:
        client = http.client.HTTPConnection('127.0.0.1', 8000, timeout=60)
        try:
            body = self.rfile.read(int(self.headers.get('Content-Length', 0)))
            headers = {k: v for k, v in self.headers.items() if k.lower() not in ('host','connection','content-length')}
            client.request(self.command, self.path, body=body, headers=headers)
            response = client.getresponse()
            self.send_response(response.status)
            for key, value in response.getheaders():
                if key.lower() not in ('transfer-encoding','connection','server','date'): self.send_header(key,value)
            self.end_headers()
            self.wfile.write(response.read())
        except OSError:
            self.send_error(502, 'Start the FastAPI backend on port 8000')
        finally: client.close()

    def do_GET(self) -> None:
        if self.path.startswith('/api/') or self.path == '/health': self.proxy()
        else: super().do_GET()

    def do_POST(self) -> None:
        if self.path.startswith('/api/'): self.proxy()
        else: self.send_error(404)

if __name__ == '__main__':
    os.chdir(Path(__file__).resolve().parents[1] / 'frontend' / 'out')
    print('Preview: http://localhost:3000 (backend must run on :8000)', flush=True)
    ThreadingHTTPServer(('0.0.0.0', 3000), Handler).serve_forever()
