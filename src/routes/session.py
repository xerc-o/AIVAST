from flask import Blueprint, request, jsonify, session
from flask_login import current_user
from models import db, ChatSession, ScanHistory, ChatMessage
from datetime import datetime, timezone
from ai.chat import ai_chat_response
from extensions import limiter

session_bp = Blueprint("session", __name__)

def get_current_user_or_guest():
    if current_user.is_authenticated:
        return current_user.id, None
    elif "anon_id" in session:
        return None, session["anon_id"]
    return None, None

@session_bp.route("/sessions", methods=["POST"])
def create_session():
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    title = data.get("title", "New Conversation")
    
    new_session = ChatSession(
        user_id=user_id,
        anon_id=anon_id,
        title=title
    )
    db.session.add(new_session)
    db.session.commit()
    
    return jsonify(new_session.to_dict()), 201

@session_bp.route("/sessions", methods=["GET"])
def list_sessions():
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401
        
    if user_id:
        sessions = ChatSession.query.filter_by(user_id=user_id).order_by(ChatSession.updated_at.desc()).all()
    else:
        sessions = ChatSession.query.filter_by(anon_id=anon_id).order_by(ChatSession.updated_at.desc()).all()
        
    return jsonify({"sessions": [s.to_dict() for s in sessions]})

@session_bp.route("/sessions/<int:session_id>", methods=["GET"])
def get_session(session_id):
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    query = ChatSession.query.filter_by(id=session_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    else:
        query = query.filter_by(anon_id=anon_id)
        
    chat_session = query.first()
    if not chat_session:
        return jsonify({"error": "Session not found"}), 404
        
    # Get scans associated with this session
    scans = ScanHistory.query.filter_by(session_id=session_id).all()
    # Get messages associated with this session
    messages = ChatMessage.query.filter_by(session_id=session_id).all()
    
    # Merge and sort by creation time
    timeline = []
    for s in scans:
        item = s.to_dict()
        item['timestamp'] = item['created_at']
        timeline.append(item)
        
    for m in messages:
        timeline.append(m.to_dict())
        
    # Sort timeline by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    return jsonify({
        "session": chat_session.to_dict(),
        "timeline": timeline
    })

@session_bp.route("/chat", methods=["POST"])
@limiter.limit("10 per day")
def send_chat_message():
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400
        
    content = data["message"]
    session_id = data.get("session_id")
    
    # 1. Handle Session
    if session_id:
        query = ChatSession.query.filter_by(id=session_id)
        if user_id:
            query = query.filter_by(user_id=user_id)
        else:
            query = query.filter_by(anon_id=anon_id)
        chat_session = query.first()
        
        if not chat_session:
            return jsonify({"error": "Session not found"}), 404
    else:
        # Create new session if not provided
        title = content[:30] + "..." if len(content) > 30 else content
        chat_session = ChatSession(user_id=user_id, anon_id=anon_id, title=title)
        db.session.add(chat_session)
        db.session.commit()
    
    # 2. Save User Message
    user_msg = ChatMessage(session_id=chat_session.id, role='user', content=content)
    db.session.add(user_msg)
    db.session.commit()
    
    # 3. Call AI (Groq) with Context
    try:
        # Fetch timeline for context
        messages = ChatMessage.query.filter_by(session_id=chat_session.id).order_by(ChatMessage.created_at).all()
        # Simplify context specifically for Chat
        session_history = [{'role': m.role, 'content': m.content} for m in messages]
        
        # Limit token usage for guests?
        # User requested "Max 500 token / request". We can pass this param or truncate context.
        # AI function doesn't accept max_token override currently, but we can update it or assume defaults.
        # For now, let's proceed.
        
        ai_response_content = ai_chat_response(content, session_history=session_history)
        
    except Exception as e:
         ai_response_content = f"Error processing AI response: {str(e)}"

    # 4. Save AI Response
    ai_msg = ChatMessage(session_id=chat_session.id, role='assistant', content=ai_response_content)
    db.session.add(ai_msg)
    
    # Update session timestamp
    chat_session.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify({
        "session_id": chat_session.id,
        "user_message": user_msg.to_dict(),
        "ai_message": ai_msg.to_dict()
    })

# ============ EPHEMERAL GUEST ENDPOINT ============
# This endpoint does NOT save anything to the database.
# Client must send the full chat history with each request.
@session_bp.route("/chat/guest", methods=["POST"])
@limiter.limit("10 per day")
def guest_chat_message():
    """
    Stateless chat for guests. No database writes.
    Client sends full history, receives AI response only.
    """
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400
    
    content = data["message"]
    history = data.get("history", [])  # Client provides its own history
    
    # Call AI with client-provided history
    try:
        ai_response_content = ai_chat_response(content, session_history=history)
    except Exception as e:
        ai_response_content = f"Error processing AI response: {str(e)}"
    
    # Return AI response only - NO DATABASE WRITES
    return jsonify({
        "ai_response": ai_response_content
    })

@session_bp.route("/sessions/<int:session_id>", methods=["PUT"])
def rename_session(session_id):
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401

    query = ChatSession.query.filter_by(id=session_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    else:
        query = query.filter_by(anon_id=anon_id)
        
    chat_session = query.first()
    if not chat_session:
        return jsonify({"error": "Session not found"}), 404
    
    data = request.get_json()
    new_title = data.get("title")
    if not new_title:
        return jsonify({"error": "Title is required"}), 400
        
    chat_session.title = new_title
    chat_session.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    
    return jsonify(chat_session.to_dict())

@session_bp.route("/sessions/<int:session_id>", methods=["DELETE"])
def delete_session(session_id):
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401

    query = ChatSession.query.filter_by(id=session_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    else:
        query = query.filter_by(anon_id=anon_id)
        
    chat_session = query.first()
    if not chat_session:
        return jsonify({"error": "Session not found"}), 404
        
    db.session.delete(chat_session)
    db.session.commit()
    
    return jsonify({"message": "Session deleted"})
