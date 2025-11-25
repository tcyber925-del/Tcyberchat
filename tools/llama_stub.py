#!/usr/bin/env python3
"""
A tiny HTTP stub that implements /v1/models used by the backend's Llama.cpp client probe.
Runs on 127.0.0.1:8080 and returns a small JSON payload.
"""
import json
import logging
from http.server import BaseHTTPRequestHandler
from socketserver import TCPServer

PORT = 8080


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        logging.info("GET %s", self.path)
        if self.path == "/v1/models":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            payload = {"models": [{"id": "llama-stub", "description": "stub model"}]}
            self.wfile.write(json.dumps(payload).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        logging.info(format % args)


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    addr = ("127.0.0.1", PORT)
    with TCPServer(addr, Handler) as httpd:
        logging.info("llama_stub serving at http://%s:%d", addr[0], addr[1])
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("llama_stub shutting down")


if __name__ == "__main__":
    main()
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST = "127.0.0.1"
PORT = 8080

class Handler(BaseHTTPRequestHandler):
    def _set_json(self, payload, code=200):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/v1/models":
            payload = {"models": [{"id": "stub-model", "name": "stub-model"}]}
            self._set_json(payload)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # keep output minimal
        print("[llama_stub] " + (format % args))

if __name__ == "__main__":
    print(f"Starting llama stub on http://{HOST}:{PORT}")
    server = HTTPServer((HOST, PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down llama stub")
        server.shutdown()
