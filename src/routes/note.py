from flask import Blueprint, jsonify, request
from src.models.note import Note, db
import json
from translator import llm_generate

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes/translate', methods=['POST'])
def translate_note():
    """Translate a note title and content without saving it."""
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get('title'), str) or not isinstance(data.get('content'), str):
        return jsonify({'error': 'Title and content are required'}), 400

    target_lang = data.get('target_lang', 'Chinese')
    if not isinstance(target_lang, str) or not target_lang.strip():
        return jsonify({'error': 'Target language is required'}), 400

    try:
        result = llm_generate(
            json.dumps({'title': data['title'], 'content': data['content']}, ensure_ascii=False),
            target_lang.strip(),
        )
        translated = json.loads(result)
        if not isinstance(translated, dict) or not isinstance(translated.get('title'), str) or not isinstance(translated.get('content'), str):
            raise ValueError('Translation response must contain string title and content fields')
        return jsonify({'title': translated['title'], 'content': translated['content']})
    except Exception as e:
        return jsonify({'error': str(e)}), 502

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400
        
        note = Note(title=data['title'], content=data['content'])
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])

