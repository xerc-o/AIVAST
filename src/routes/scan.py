from flask import Blueprint, request, jsonify
from ai.planner import plan_scan
from ai.analyzer import analyze_output
from executor.runner import run_command

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True)
    if not data or "target" not in data:
        return jsonify({"error": "missing target"}), 400

    target = data["target"]

    plan = plan_scan(target)
    if not plan or "command" not in plan:
        return jsonify({"error": "planner failed"}), 500

    execution = run_command(plan["command"])

    analysis = analyze_output(
        plan["tool"],
        execution
    )

    return jsonify({
        "target": target,
        "tool": plan["tool"],
        "command": plan["command"],
        "execution": execution,
        "analysis": analysis
    })
