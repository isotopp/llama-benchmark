#!/usr/bin/env python3
"""Minimal llama-server HTTP boundary for benchmark integration specs."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any


class Handler(BaseHTTPRequestHandler):
    """Serve health and deterministic completion responses."""

    def do_GET(self) -> None:
        if self.path != "/health":
            self.send_error(404)
            return
        self._send_json({"status": "ok"})

    def do_POST(self) -> None:
        if self.path != "/completion":
            self.send_error(404)
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        json.loads(self.rfile.read(content_length))
        self._send_json(
            {
                "content": "fake completion",
                "timings": {
                    "prompt_n": 100,
                    "prompt_ms": 50.0,
                    "prompt_per_second": 2000.0,
                    "predicted_n": 10,
                    "predicted_ms": 100.0,
                    "predicted_per_second": 100.0,
                },
            }
        )

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _send_json(self, body: object) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args, _ = parser.parse_known_args()
    HTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
