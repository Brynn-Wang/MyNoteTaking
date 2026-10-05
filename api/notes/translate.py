import json
from http.server import BaseHTTPRequestHandler

from translator import translate_note_content


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(content_length))
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"error": "Request body must be valid JSON"})
            return

        if (
            not isinstance(data, dict)
            or not isinstance(data.get("title"), str)
            or not isinstance(data.get("content"), str)
        ):
            self._send_json(400, {"error": "Title and content are required"})
            return

        target_lang = data.get("target_lang", "Chinese")
        if not isinstance(target_lang, str) or not target_lang.strip():
            self._send_json(400, {"error": "Target language is required"})
            return

        try:
            translated = translate_note_content(
                data["title"],
                data["content"],
                target_lang.strip(),
            )
        except Exception as error:
            self._send_json(502, {"error": str(error)})
            return

        self._send_json(200, translated)

    def do_GET(self):
        self._send_json(405, {"error": "Method not allowed"})
