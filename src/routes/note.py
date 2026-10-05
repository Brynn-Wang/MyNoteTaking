import json
import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from openai import APIError, OpenAI
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from src.extensions import db
from src.models.note import Note

note_bp = Blueprint("notes", __name__)
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "translate_prompt.md"
DEFAULT_TRANSLATION_MODEL = "qwen/qwen3.8-27b:free"


def _note_input(data):
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Request body must be a JSON object."}), 400)

    title = data.get("title", "")
    content = data.get("content", "")
    if not isinstance(title, str) or not isinstance(content, str):
        return None, (jsonify({"error": "Title and content must be strings."}), 400)

    if len(title) > 300:
        return None, (jsonify({"error": "Title must be 300 characters or fewer."}), 400)

    return {"title": title, "content": content}, None


@note_bp.get("/notes")
def get_notes():
    search = request.args.get("q", "").strip()
    query = Note.query
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(Note.title.ilike(pattern), Note.content.ilike(pattern)))

    notes = query.order_by(Note.updated_at.desc(), Note.id.desc()).all()
    return jsonify([note.to_dict() for note in notes])


@note_bp.post("/notes")
def create_note():
    values, error = _note_input(request.get_json(silent=True))
    if error:
        return error

    note = Note(**values)
    db.session.add(note)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Failed to create note")
        return jsonify({"error": "Could not save the note."}), 500

    return jsonify(note.to_dict()), 201


@note_bp.put("/notes/<int:note_id>")
def update_note(note_id):
    note = db.session.get(Note, note_id)
    if note is None:
        return jsonify({"error": "Note not found."}), 404

    values, error = _note_input(request.get_json(silent=True))
    if error:
        return error

    note.title = values["title"]
    note.content = values["content"]
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Failed to update note %s", note_id)
        return jsonify({"error": "Could not save the note."}), 500

    return jsonify(note.to_dict())


@note_bp.delete("/notes/<int:note_id>")
def delete_note(note_id):
    note = db.session.get(Note, note_id)
    if note is None:
        return jsonify({"error": "Note not found."}), 404

    db.session.delete(note)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Failed to delete note %s", note_id)
        return jsonify({"error": "Could not delete the note."}), 500

    return jsonify({"deleted": True})


@note_bp.post("/notes/translate")
def translate_note():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400

    title = data.get("title")
    content = data.get("content")
    target_lang = data.get("target_lang")
    if not all(isinstance(value, str) for value in (title, content, target_lang)):
        return jsonify(
            {"error": "Title, content, and target_lang must be strings."}
        ), 400
    if not target_lang.strip():
        return jsonify({"error": "target_lang cannot be empty."}), 400

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        return jsonify({"error": "Translation is unavailable: OPENROUTER_API_KEY is not set."}), 503

    try:
        system_prompt = PROMPT_PATH.read_text(encoding="utf-8")
    except OSError:
        current_app.logger.exception("Could not read translation prompt")
        return jsonify({"error": "Translation service is not configured correctly."}), 500

    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        completion = client.chat.completions.create(
            model=DEFAULT_TRANSLATION_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "title": title,
                            "content": content,
                            "target_lang": target_lang.strip(),
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            response_format={"type": "json_object"},
        )
        response_content = completion.choices[0].message.content
        if not response_content:
            raise ValueError("Translation provider returned an empty response.")

        translated = json.loads(response_content)
        if not isinstance(translated, dict):
            raise ValueError("Translation response must be a JSON object.")
        translated_title = translated.get("title")
        translated_content = translated.get("content")
        if not isinstance(translated_title, str) or not isinstance(translated_content, str):
            raise ValueError("Translation response must contain string title and content.")
    except (json.JSONDecodeError, ValueError) as error:
        current_app.logger.warning("Invalid translation response: %s", error)
        return jsonify({"error": "Translation provider returned an invalid response."}), 502
    except APIError:
        current_app.logger.exception("Translation request failed")
        return jsonify({"error": "Translation request failed. Please try again later."}), 502

    return jsonify({"title": translated_title, "content": translated_content})
