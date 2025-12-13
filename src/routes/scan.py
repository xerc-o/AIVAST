from flask import Blueprint, request, jsonify
from ai.planner import plan_scan
from executor.runner import run_command

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True)
    if not data or "target" not in data:
        return jsonify({"error": "missing target"}), 400

    target = data["target"]

    # safe: validate target format here (url/ip)
    plan = plan_scan(target)
    if not plan or "command" not in plan:
        return jsonify({"error": "planner failed"}), 500

    output = run_command(plan["command"])

    # if runner returns ok False, convert to 502/400 depending on error type
    status = 200 if output.get("ok") else 502

    return jsonify({
        "target": target,
        "tool": plan.get("tool"),
        "reason": plan.get("reason"),
        "command": plan.get("command"),
        "output": output
    }), status
