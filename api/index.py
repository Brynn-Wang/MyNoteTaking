import sys
import os
from urllib.parse import urlsplit

# 将 src 目录加入 Python 寻址路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app

class VercelPathMiddleware:
    """
    修复 Vercel Serverless 重写导致的 PATH_INFO 丢失问题：
    优先使用真实的请求 URI，避免 Vercel 的泛化 matched-path（如 /api）覆盖实际 API 路径。
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def _get_request_path(self, environ):
        for key in ('HTTP_X_NOTETAKER_PATH', 'HTTP_X_ORIGINAL_URI', 'HTTP_X_FORWARDED_URI', 'HTTP_X_MATCHED_PATH', 'RAW_URI', 'REQUEST_URI'):
            value = environ.get(key)
            if not value:
                continue
            path = urlsplit(value).path if key in {'RAW_URI', 'REQUEST_URI', 'HTTP_X_FORWARDED_URI', 'HTTP_X_ORIGINAL_URI'} else value.split('?', 1)[0]
            if key == 'HTTP_X_NOTETAKER_PATH':
                if path.startswith('/api/'):
                    return path
                continue
            if path and path not in ('/', '/api', '/api/index.py'):
                return path
        return None

    def __call__(self, environ, start_response):
        request_path = self._get_request_path(environ)
        if request_path:
            environ['PATH_INFO'] = request_path
        return self.wsgi_app(environ, start_response)

# 挂载中间件
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
