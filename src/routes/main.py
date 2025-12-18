from flask import Blueprint, request, jsonify
from executor.runner import run_command  # sesuaikan path runner kamu

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET"])
def index():
    return jsonify({"status": "AIVAST running"})

@main_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    message = data.get("message")

    if not message:
        return jsonify({"error": "message is required"}), 400

    try:
        response = run_command(message)
        return jsonify({
            "input": message,
            "output": response
        })
    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500
