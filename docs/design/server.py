# -*- coding: utf-8 -*-
"""docs/design 静态服务 + 笔记持久化 API（零依赖，Python 标准库）。

- GET  /                → docs/design/index.html
- GET  /flows/*.svg     → 流程图
- GET  /api/notes       → 返回 notes.json 的全部内容 {"key": "text", ...}
- POST /api/notes       → body {"key": "text"}，合并写入 notes.json（落盘，永久保留）

用法：python docs/design/server.py [端口]   默认 8080
"""
from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTES = ROOT / "notes.json"
_lock = threading.Lock()
CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def load_notes() -> dict:
    if not NOTES.is_file():
        return {}
    try:
        return json.loads(NOTES.read_text(encoding="utf-8"))
    except Exception:
        return {}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):  # 静音默认日志
        pass

    def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        for k, v in {**CORS, **(extra or {})}.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/notes":
            self._json(load_notes())
            return
        if path in ("/", "/index.html"):
            self._serve(ROOT / "index.html")
            return
        # 仅允许访问本目录内的静态文件，防目录穿越
        target = (ROOT / path.lstrip("/")).resolve()
        if target.is_file() and ROOT in target.parents:
            ctype = "image/svg+xml" if target.suffix == ".svg" else "application/octet-stream"
            self._send(200, target.read_bytes(), ctype)
        else:
            self._send(404, b"not found", "text/plain")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path != "/api/notes":
            self._send(404, b"not found", "text/plain")
            return
        try:
            n = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(n).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("body 必须是 {key: text} 对象")
        except Exception as e:
            self._json({"ok": False, "error": str(e)}, 400)
            return
        with _lock:
            notes = load_notes()
            for k, v in payload.items():
                k = str(k)[:64]
                v = "" if v is None else str(v)
                if v.strip():
                    notes[k] = v
                else:
                    notes.pop(k, None)  # 清空即删除
            NOTES.write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding="utf-8")
        self._json({"ok": True, "keys": len(notes)})

    def _serve(self, fp: Path):
        if not fp.is_file():
            self._send(404, b"index.html not found", "text/plain")
            return
        self._send(200, fp.read_bytes(), "text/html; charset=utf-8")


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"设计文档服务已启动：http://localhost:{port}/  （笔记落盘：{NOTES}）")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
