from typing import Dict
from .llm.groq import call_groq
import json


# ==========================================================
# RULE-BASED PLANNER (DEFAULT & SAFE)
# ==========================================================
def plan_scan_rule_based(target: str) -> Dict[str, str]:
    """
    Planner tanpa AI.
    Aman, deterministik, cocok untuk testing awal.
    """

    target = target.strip()

    if target.startswith("http://") or target.startswith("https://"):
        return {
            "tool": "nikto",
            "command": f"nikto -h {target} -Format xml",
            "reason": "Web vulnerability scan (rule-based, xml output)"
        }

    return {
        "tool": "nmap",
        "command": f"nmap -sV -T4 -oX - {target}",
        "reason": "Network service scan (rule-based, xml stdout)"
    }


# ==========================================================
# AI PLANNER (IMPLEMENTASI LENGKAP)
# ==========================================================
def plan_scan_ai(target: str) -> Dict[str, str]:
    """
    AI-powered planner yang menggunakan LLM untuk menentukan tool terbaik.
    """
    prompt = f"""You are a cybersecurity expert. Given a target, determine the best scanning tool and command.

Target: {target}

Return ONLY valid JSON with this exact schema (no markdown, no explanations, no code blocks):
{{
  "tool": "nmap|nikto",
  "command": "full command string",
  "reason": "brief explanation"
}}

Available tools:
- nmap: Network port and service scanner. Use for IP addresses, hostnames, or when you need to discover open ports and services.
- nikto: Web vulnerability scanner. Use ONLY for http:// or https:// URLs.

Rules:
- If target starts with http:// or https://, use nikto
- If target is IP address or hostname (without http/https), use nmap
- For nmap, use: "nmap -sV -T4 [target]"
- For nikto, use: "nikto -h [target]"

Target: {target}"""

    try:
        response = call_groq(prompt)
        
        # Clean response (remove markdown code blocks if any)
        response = response.strip()
        if response.startswith("on"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Parse JSON response
        plan = json.loads(response)
        
        # Validate
        if plan.get("tool") not in ["nmap", "nikto"]:
            raise ValueError(f"Invalid tool: {plan.get('tool')}. Must be 'nmap' or 'nikto'")
        if "command" not in plan:
            raise ValueError("Missing 'command' in AI response")
        if not plan.get("command"):
            raise ValueError("Command is empty")
        
        # Log untuk debugging
        print(f"✅ AI Planner selected: {plan.get('tool')} - {plan.get('reason', 'N/A')}")
            
        return plan
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse AI response as JSON: {str(e)}. Response: {response[:200]}"
        print(f"❌ AI Planner JSON Error: {error_msg}")
        raise ValueError(error_msg)
    except KeyError as e:
        error_msg = f"Missing required field in AI response: {str(e)}"
        print(f"❌ AI Planner KeyError: {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"AI planner failed: {str(e)}"
        print(f"❌ AI Planner Exception: {error_msg}")
        raise ValueError(error_msg)


# ==========================================================
# PUBLIC API (DIPANGGIL ORCHESTRATOR)
# ==========================================================
def plan_scan(target: str, use_ai: bool = False) -> Dict[str, str]:
    """
    Entry point planner.

    use_ai=False -> rule-based (default, aman)
    use_ai=True  -> AI-powered (lebih fleksibel)
    """

    if use_ai:
        try:
            print(f"🤖 Using AI Planner for target: {target}")
            result = plan_scan_ai(target)
            print(f"✅ AI Planner result: {result.get('tool')} - {result.get('command')}")
            return result
        except Exception as e:
            # Fallback ke rule-based jika AI gagal
            print(f"⚠️ Warning: AI planner failed ({str(e)}), falling back to rule-based")
            return plan_scan_rule_based(target)
    else:
        print(f"📋 Using Rule-Based Planner for target: {target}")

    return plan_scan_rule_based(target)## Update `src/routes/scan.py` (tambahkan field planner)

from flask import Blueprint, request, jsonify
from ai.planner import plan_scan
from ai.analyzer import analyze_output
from executor.runner import run_command
from models import db, ScanHistory
import json

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scan", methods=["POST"])
def scan():
    try:
        data = request.get_json(silent=True)
        if not data or "target" not in data:
            return jsonify({"error": "missing target"}), 400

        target = data["target"]
        use_ai_planner = data.get("use_ai", False)

        # Validasi target
        if not target or not isinstance(target, str) or len(target.strip()) == 0:
            return jsonify({"error": "invalid target"}), 400

        target = target.strip()

        # 1. Planning (dengan opsi AI)
        try:
            plan = plan_scan(target, use_ai=use_ai_planner)
            if not plan or "command" not in plan:
                return jsonify({"error": "planner failed"}), 500
        except Exception as e:
            return jsonify({"error": f"planner exception: {str(e)}"}), 500
        
        # 2. Execution
        try:
            execution = run_command(plan["command"])
            if not isinstance(execution, dict):
                return jsonify({"error": "invalid execution result"}), 502

            if not execution.get("ok"):
                return jsonify({
                    "error": "execution failed",
                    "details": execution
                }), 500
        except Exception as e:
            return jsonify({"error": f"execution exception: {str(e)}"}), 500

        # 3. Analysis
        try:
            analysis = analyze_output(plan.get("tool"), execution)
        except Exception as e:
            return jsonify({"error": f"analysis exception: {str(e)}"}), 500

        # 4. Save to database (log failure but don't break response)
        try:
            risk_level = analysis.get("risk") or analysis.get("risk_level") or "unknown"
            scan_record = ScanHistory(
                target=target,
                tool=plan.get("tool"),
                command=plan.get("command"),
                execution_result=json.dumps(execution),
                analysis_result=json.dumps(analysis),
                risk_level=risk_level
            )
            db.session.add(scan_record)
            db.session.commit()
        except Exception as e:
            print(f"Warning: Failed to save to database: {str(e)}")

        # 5. Unified response
        return jsonify({
            "target": target,
            "tool": plan.get("tool"),
            "command": plan.get("command"),
            "planner": "ai" if use_ai_planner else "rule-based",
            "reason": plan.get("reason", "N/A"),
            "execution": execution,
            "analysis": analysis
        }), 200

    except Exception as e:
        import traceback
        print(f"Unexpected error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({
            "error": "internal_server_error",
            "message": str(e)
        }), 500## Perubahan yang dilakukan
