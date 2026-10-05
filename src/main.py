import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, abort, send_from_directory
from flask_cors import CORS

from src.extensions import db

ROOT_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = Path(__file__).resolve().parent / "static"

load_dotenv(ROOT_DIR / ".env")

app = Flask(__name__)
if os.environ.get("VERCEL"):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/app.db"
else:
    database_dir = ROOT_DIR / "database"
    database_dir.mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{database_dir / 'app.db'}"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})

from src.models.note import Note  # noqa: E402,F401
from src.models.user import User  # noqa: E402,F401
from src.routes.note import note_bp  # noqa: E402

app.register_blueprint(note_bp, url_prefix="/api")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if path == "api" or path.startswith("api/"):
        abort(404)

    if path:
        requested_file = STATIC_DIR / path
        if requested_file.is_file():
            return send_from_directory(STATIC_DIR, path)

    return send_from_directory(STATIC_DIR, "index.html")


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
