from flask import Blueprint, request, jsonify
from ai.planner import plan_scan
from ai.analyzer import analyze_output
from executor.runner import run_command
from models import db, ScanHistory
import json

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scan", methods=["POST"])
def scan():
    data = request.get_json(silent=True)
    if not data or "target" not in data:
        return jsonify({"error": "missing target"}), 400

    target = data["target"]
    
    # Validasi target
    if not target or not isinstance(target, str) or len(target.strip()) == 0:
        return jsonify({"error": "invalid target"}), 400
    
    target = target.strip()

    # 1. Planning
    try:
        plan = plan_scan(target)
        if not plan or "command" not in plan:
            return jsonify({"error": "planner failed"}), 500
    except Exception as e:
        return jsonify({"error": f"planner exception: {str(e)}"}), 500

    # 2. Execution
    try:
        execution = run_command(plan["command"])
        if not execution.get("ok"):
            return jsonify({
                "error": "execution failed",
                "details": execution
            }), 500
    except Exception as e:
        return jsonify({"error": f"execution exception: {str(e)}"}), 500

    # 3. Analysis
    try:
        analysis = analyze_output(plan["tool"], execution)
    except Exception as e:
        return jsonify({"error": f"analysis exception: {str(e)}"}), 500

    # 4. Save to database
    try:
        risk_level = analysis.get("risk", "unknown")
        scan_record = ScanHistory(
            target=target,
            tool=plan["tool"],
            command=plan["command"],
            execution_result=json.dumps(execution),
            analysis_result=json.dumps(analysis),
            risk_level=risk_level
        )
        db.session.add(scan_record)
        db.session.commit()
    except Exception as e:
        # Log error tapi jangan gagalkan response
        print(f"Warning: Failed to save to database: {str(e)}")

    return jsonify({
        "target": target,
        "tool": plan["tool"],
        "command": plan["command"],
        "execution": execution,
        "analysis": analysis
    })