import sys
import os

# 将 src 目录加入 Python 寻址路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app

class VercelPathMiddleware:
    """
    修复 Vercel Serverless 重写导致的 PATH_INFO 丢失问题：
    从 Vercel 的 x-matched-path 请求头中还原客户端真正访问的 URL 路径
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        matched_path = (
            environ.get('HTTP_X_MATCHED_PATH')
            or environ.get('HTTP_X_FORWARDED_URI')
            or environ.get('HTTP_X_ORIGINAL_URI')
        )
        if matched_path:
            # 剥离 URL 问号后的查询参数，确保路由精准匹配
            environ['PATH_INFO'] = matched_path.split('?')[0]
        return self.wsgi_app(environ, start_response)

# 挂载中间件
app.wsgi_app = VercelPathMiddleware(app.wsgi_app)
