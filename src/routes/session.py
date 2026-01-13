from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from models import db, ChatSession, ScanHistory, ChatMessage
from datetime import datetime, timezone
from ai.chat import ai_chat_response

session_bp = Blueprint("session", __name__)

@session_bp.route("/sessions", methods=["POST"])
@login_required
def create_session():
    data = request.get_json()
    title = data.get("title", "New Conversation")
    
    new_session = ChatSession(
        user_id=current_user.id,
        title=title
    )
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify(new_session.to_dict()), 201

@session_bp.route("/sessions", methods=["GET"])
@login_required
def list_sessions():
    sessions = ChatSession.query.filter_by(user_id=current_user.id).order_by(ChatSession.updated_at.desc()).all()
    return jsonify({"sessions": [s.to_dict() for s in sessions]})

@session_bp.route("/sessions/<int:session_id>", methods=["GET"])
@login_required
def get_session(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    # Get scans associated with this session
    scans = ScanHistory.query.filter_by(session_id=session_id).all()
    # Get messages associated with this session
    messages = ChatMessage.query.filter_by(session_id=session_id).all()
    
    # Merge and sort by creation time
    timeline = []
    for s in scans:
        item = s.to_dict()
        # Ensure timestamp is comparable (ISO string or datetime object)
        # s.to_dict() returns ISO string 'created_at'.
        item['timestamp'] = item['created_at']
        timeline.append(item)
        
    for m in messages:
        timeline.append(m.to_dict())
        
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    return jsonify({
        "session": session.to_dict(),
        "timeline": timeline
    })

@session_bp.route("/chat", methods=["POST"])
@login_required
def send_chat_message():
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400
        
    content = data["message"]
    session_id = data.get("session_id")
    
    # 1. Handle Session
    if session_id:
        session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
        if not session:
            return jsonify({"error": "Session not found"}), 404
    else:
        # Create new session if not provided
        # Use first few words as title
        title = content[:30] + "..." if len(content) > 30 else content
        session = ChatSession(user_id=current_user.id, title=title)
        db.session.add(session)
        db.session.commit()
    
    # 2. Save User Message
    user_msg = ChatMessage(session_id=session.id, role='user', content=content)
    db.session.add(user_msg)
    db.session.commit()
    
    # 3. Call AI (Groq) with Context
    try:
        # Fetch unified timeline
        scans = ScanHistory.query.filter_by(session_id=session.id).all()
        messages = ChatMessage.query.filter_by(session_id=session.id).all()
        timeline = []
        for s in scans:
            timeline.append({'role': 'system', 'content': f"Scan executed: {s.command}. Result: {s.analysis_result or s.status}"})
        for m in messages:
            timeline.append({'role': m.role, 'content': m.content})
        
        # Sort by id (proxy for time if created_at is strictly sequential, roughly)
        # Better to sort by timestamp if models have it clean, but lists are separate.
        # Simplest: Just re-query all messages? Or pass raw list.
        # ai_chat.py expects list of dicts with role/content.
        
        # Let's simplify: existing ai_chat.py takes session_history.
        # We'll just pass the timeline we construct in get_session, reused here.
        # But for now, let's just pass the messages for conversational context.
        # The AI needs to know about scans too.
        
        session_history = sorted(timeline, key=lambda x: x.get('id', 0)) # Naive sort
        
        ai_response_content = ai_chat_response(content, session_history=session_history)
        
    except Exception as e:
         ai_response_content = f"Error processing AI response: {str(e)}"

    # 4. Save AI Response
    ai_msg = ChatMessage(session_id=session.id, role='assistant', content=ai_response_content)
    db.session.add(ai_msg)
    
    # Update session timestamp
    session.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        "session_id": session.id,
        "user_message": user_msg.to_dict(),
        "ai_message": ai_msg.to_dict()
    })

@session_bp.route("/sessions/<int:session_id>", methods=["PUT"])
@login_required
def rename_session(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.get_json()
    new_title = data.get("title")
    if not new_title:
        return jsonify({"error": "Title is required"}), 400
        
    session.title = new_title
    session.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify(session.to_dict())

@session_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
@login_required
def delete_session(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=current_user.id).first()
    if not session:
        return jsonify({"error": "Session not found"}), 404
        
    db.session.delete(session)
    db.session.commit()
    
    return jsonify({"message": "Session deleted"})
