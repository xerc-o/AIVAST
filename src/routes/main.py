from flask import Blueprint, request, jsonify, render_template
from executor.runner import run_command_async
from flask_login import login_required

main_bp = Blueprint("main", __name__)

@main_bp.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@main_bp.route("/chat-page")
def chat_page():
    return render_template("chat.html")


