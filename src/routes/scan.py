from flask import Blueprint, request, jsonify
from ai.planner import plan_scan
from ai.analyzer import analyze_output
from executor.runner import run_command

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scan", methods=["POST"])
def scan():
    # 1. Parse JSON safely
    data = request.get_json(silent=True)
    if not data or "target" not in data:
        return jsonify({"error": "missing target"}), 400

    target = data["target"]

    # 2. AI Planner (decide tool + command)
    plan = plan_scan(target)
    if not plan or "command" not in plan:
        return jsonify({"error": "planner failed"}), 500

    # 3. Execute command
    output = run_command(plan["command"])

    if not isinstance(output, dict):
        return jsonify({"error": "executor failure"}), 502

    # 4. AI Analyzer (INTI AIVAST)
    analysis = analyze_output(
        plan.get("tool"),
        output.get("stdout", "")
    )

    status = 200 if output.get("ok") else 502

    # 5. Unified response
    return jsonify({
        "target": target,
        "tool": plan.get("tool"),
        "reason": plan.get("reason"),
        "command": plan.get("command"),
        "analysis": analysis,          # 👈 hasil AI
        "raw_output": output.get("stdout", "") # 👈 output mentah (safe access)
    }), status
