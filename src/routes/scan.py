from flask import Blueprint, request, jsonify, session
from flask_login import current_user
from ai.planner import plan_scan
from ai.analyzer import analyze_output
from executor.runner import run_command_async, check_reachability, normalize_target
from models import db, ScanHistory, ChatSession
import json
import psutil
import os
from datetime import datetime, timezone # Import datetime and timezone
from executor.runner import TIMEOUTS # Import TIMEOUTS dictionary
import uuid

WORDLISTS_DIR = "data/wordlists"
UPLOAD_WORDLISTS_DIR = os.path.join(WORDLISTS_DIR, "uploads")
DEFAULT_WORDLIST = os.path.join(WORDLISTS_DIR, "default_common.txt")

# Ensure directories exist
os.makedirs(UPLOAD_WORDLISTS_DIR, exist_ok=True)

# Helper function to clean up temporary files
def _cleanup_temp_files(scan: ScanHistory):
    """Helper to clean up temporary files."""
    if scan.stdout_path and os.path.exists(scan.stdout_path):
        os.remove(scan.stdout_path)
    if scan.stderr_path and os.path.exists(scan.stderr_path):
        os.remove(scan.stderr_path)
    
    scan.pid = None
    scan.stdout_path = None
    scan.stderr_path = None
    # No db.session.commit() here, as it's typically called by the caller

# Helper for user/guest detection (same as session.py)
def get_current_user_or_guest():
    if current_user.is_authenticated:
        return current_user.id, None
    elif "anon_id" in session:
        return None, session["anon_id"]
    return None, None

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scans", methods=["POST"])
def start_scan():
    """
    Starts a new scan asynchronously.
    """
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.get_json()
    if not data or "target" not in data:
        return jsonify({"error": "missing target"}), 400

    target = data["target"].strip()
    use_ai = data.get("use_ai", True)
    tool = data.get("tool")
    deep_scan = data.get("deep_scan", False)

    # 1. Normalize Target Input based on Tool
    if tool:
        target = normalize_target(target, tool)

    # 0. Reachability Check
    is_up, reason = check_reachability(target)
    if not is_up:
        return jsonify({
            "error": "Target unreachable",
            "details": reason,
            "status": "failed"
        }), 400

    # 1. Handle Session (Create or Verify) - SKIP for guests
    session_id = data.get("session_id")
    chat_session = None
    
    if user_id:
        # Authenticated user - use database sessions
        if session_id:
            chat_session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
            if not chat_session:
                return jsonify({"error": "Session not found"}), 404
        else:
            chat_session = ChatSession(user_id=user_id, title=f"Scan: {target}")
            db.session.add(chat_session)
            db.session.commit()
    # else: guest mode - no persistent session

    # 2. Planning (Adaptive)
    history_context = ""
    if chat_session:
        # Pull last 3 scans for context
        prev_scans = ScanHistory.query.filter_by(session_id=chat_session.id).order_by(ScanHistory.created_at.desc()).limit(3).all()
        for ps in prev_scans:
            history_context += f"- Tool: {ps.tool}, Status: {ps.status}, Risk: {ps.risk_level}\n"

    try:
        plan = plan_scan(target, use_ai=use_ai, tool=tool, history=history_context, deep_scan=deep_scan)
        
        # 2.5 Wordlist Injection / Handling
        if plan.get("tool") == "gobuster":
            custom_wordlist_content = data.get("custom_wordlist")
            command = plan.get("command", [])
            
            # If user provided raw wordlist content, save it
            if custom_wordlist_content:
                filename = f"custom_{uuid.uuid4().hex[:8]}.txt"
                filepath = os.path.join(UPLOAD_WORDLISTS_DIR, filename)
                with open(filepath, "w") as f:
                    f.write(custom_wordlist_content)
                
                # Replace or Add -w argument
                if "-w" in command:
                    idx = command.index("-w")
                    if idx + 1 < len(command):
                        command[idx + 1] = filepath
                else:
                    command.extend(["-w", filepath])
            
            # Ensure -w exists even if not provided by AI, fallback to default
            if "-w" not in command:
                command.extend(["-w", DEFAULT_WORDLIST])
            
            plan["command"] = command
            
    except Exception as e:
        return jsonify({"error": f"Planner failed: {str(e)}"}), 500

    # 3. Create initial record in DB
    new_scan = ScanHistory(
        target=target,
        tool=plan.get("tool"),
        command=json.dumps(plan.get("command")), 
        rationale=plan.get("rationale"), # Store AI's reasoning
        status='running',
        start_time=datetime.now(timezone.utc),
        user_id=user_id,
        session_id=chat_session.id if chat_session else None
    )
    db.session.add(new_scan)
    db.session.commit()

    # 3. Execution (Async)
    try:
        exec_data = run_command_async(plan["command"])
        if not exec_data.get("ok"):
            new_scan.status = 'failed'
            new_scan.analysis_result = json.dumps({"error": exec_data.get("error")})
            db.session.commit()
            return jsonify({"error": f"Failed to start scan: {exec_data.get('error')}"}), 500

        # Update record with PID and temp file paths
        new_scan.pid = exec_data["pid"]
        new_scan.stdout_path = exec_data["stdout_path"]
        new_scan.stderr_path = exec_data["stderr_path"]
        db.session.commit()

        # 4. Immediate Response
        return jsonify({
            "message": "Scan started successfully",
            "scan_id": new_scan.id,
            "session_id": chat_session.id if chat_session else None
        }), 202

    except Exception as e:
        new_scan.status = 'failed'
        new_scan.analysis_result = json.dumps({"error": str(e)})
        db.session.commit()
        return jsonify({"error": f"Failed to execute command: {str(e)}"}), 500


@scan_bp.route("/scans/<int:scan_id>/status", methods=["GET"])
def get_scan_status(scan_id):
    """
    Polls the status of a running scan. If completed, returns the result.
    """
    user_id, anon_id = get_current_user_or_guest()
    if not user_id and not anon_id:
        return jsonify({"error": "Unauthorized"}), 401
    
    scan = ScanHistory.query.get_or_404(scan_id)

    # Ownership check - allow if user matches OR if guest scan (user_id is None)
    if scan.user_id is not None and scan.user_id != user_id:
        return jsonify({"error": "forbidden"}), 403

    if scan.status != 'running':
        return jsonify(scan.to_dict())

    # Get expected timeout from runner.py
    max_timeout = TIMEOUTS.get(scan.tool, 120) # Default to 120 seconds

    # Check for timeout
    if scan.start_time and (datetime.now(timezone.utc) - scan.start_time.replace(tzinfo=timezone.utc)).total_seconds() > max_timeout:
        if scan.pid and psutil.pid_exists(scan.pid):
            try:
                proc = psutil.Process(scan.pid)
                proc.terminate() # or proc.kill() if terminate fails
                proc.wait(timeout=5) # Wait for process to terminate
                print(f"Process {scan.pid} for scan {scan.id} killed due to timeout.")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                print(f"Could not terminate process {scan.pid} for scan {scan.id} due to NoSuchProcess or AccessDenied.")
            except psutil.TimeoutExpired:
                proc.kill()
                print(f"Process {scan.pid} for scan {scan.id} killed forcefully due to timeout (terminate failed).")
        
        scan.status = 'failed'
        scan.analysis_result = json.dumps({"error": f"Scan timed out after {max_timeout} seconds."})
        db.session.commit()
        # Cleanup temp files immediately
        _cleanup_temp_files(scan)
        return jsonify(scan.to_dict()), 200

    # Check if the process is still running or is a zombie
    if scan.pid:
        try:
            proc = psutil.Process(scan.pid)
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                return jsonify({"status": "running", "target": scan.target, "tool": scan.tool})
            # If we reach here, PID exists, but proc.is_running() is False or it's a zombie.
            # This means the process has terminated (or is a zombie that needs reaping).
            # Proceed to process results.
        except psutil.NoSuchProcess:
            # PID no longer exists, process has definitely finished.
            # Proceed to process results.
            pass # Continue to the processing logic below
    else:
        # No PID stored (e.g., if process failed to start), but status is 'running'.
        # This is an inconsistent state, assume finished and proceed to process results.
        pass

    # --- Process is finished, let's process the results ---
    try:
        # Read output from temp files
        try:
            with open(scan.stdout_path, 'r') as f:
                stdout = f.read()
            with open(scan.stderr_path, 'r') as f:
                stderr = f.read()
        except (FileNotFoundError, TypeError): # TypeError if path is None
            stdout = ""
            stderr = "Log files not found or path is invalid. The process may have crashed or failed to write output."

        execution_result = {
            "ok": True,
            "tool": scan.tool,
            "stdout": stdout,
            "stderr": stderr
        }

        # Analysis
        analysis = analyze_output(scan.tool, execution_result, target=scan.target)
        
        # New Structured Risk Level Extraction
        risk_level = analysis.get("issue", {}).get("severity") or analysis.get("risk") or analysis.get("risk_level") or "unknown"
        
        # Update Database
        scan.status = 'completed'
        scan.execution_result = json.dumps(execution_result)
        scan.analysis_result = json.dumps(analysis)
        scan.risk_level = risk_level
        
        db.session.commit()
        return jsonify(scan.to_dict())

    except Exception as e:
        # Handle exceptions during result processing
        scan.status = 'failed'
        scan.analysis_result = json.dumps({"error": "Failed to process results", "details": str(e)})
        db.session.commit()
        return jsonify({"status": "failed", "error": str(e)}), 200
    
    finally:
        # Cleanup temp files
        _cleanup_temp_files(scan)