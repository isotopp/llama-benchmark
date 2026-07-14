#!/usr/bin/env python3
"""Minimal llama-server HTTP boundary for benchmark integration specs."""

import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any


class Handler(BaseHTTPRequestHandler):
    """Serve health and deterministic completion responses."""

    completion_status = 200

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
        if self.completion_status != 200:
            self._send_json(
                {"error": "configured completion failure"},
                status=self.completion_status,
            )
            return
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

    def _send_json(self, body: object, *, status: int = 200) -> None:
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--state-file", type=Path)
    parser.add_argument("--completion-status", type=int, default=200)
    args, _ = parser.parse_known_args()
    Handler.completion_status = args.completion_status
    if args.state_file is not None:
        args.state_file.write_text(
            json.dumps(
                {"turbo_auto_asymmetric": os.environ.get("TURBO_AUTO_ASYMMETRIC")}
            ),
            encoding="utf-8",
        )
    HTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
