from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from ai.planner import plan_scan
from ai.analyzer import analyze_output
from executor.runner import run_command_async
from models import db, ScanHistory
import json
import psutil
import os
from datetime import datetime, timezone # Import datetime and timezone
from executor.runner import TIMEOUTS # Import TIMEOUTS dictionary

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

scan_bp = Blueprint("scan", __name__)

@scan_bp.route("/scans", methods=["POST"])
@login_required
def start_scan():
    """
    Starts a new scan asynchronously.
    """
    data = request.get_json()
    if not data or "target" not in data:
        return jsonify({"error": "missing target"}), 400

    target = data["target"].strip()
    use_ai = data.get("use_ai", True)

    # 1. Planning
    try:
        plan = plan_scan(target, use_ai=use_ai)
    except Exception as e:
        return jsonify({"error": f"Planner failed: {str(e)}"}), 500

    # 2. Create initial record in DB
    new_scan = ScanHistory(
        target=target,
        tool=plan.get("tool"),
        command=json.dumps(plan.get("command")),  # Serialize command list to JSON string
        status='running',
        start_time=datetime.now(timezone.utc), # Record start time
        user_id=current_user.id # Associate with current user
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
            "scan_id": new_scan.id
        }), 202

    except Exception as e:
        new_scan.status = 'failed'
        new_scan.analysis_result = json.dumps({"error": str(e)})
        db.session.commit()
        return jsonify({"error": f"Failed to execute command: {str(e)}"}), 500


@scan_bp.route("/scans/<int:scan_id>/status", methods=["GET"])
@login_required
def get_scan_status(scan_id):
    """
    Polls the status of a running scan. If completed, returns the result.
    """
    scan = ScanHistory.query.get_or_404(scan_id)

    # Ownership check
    if scan.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    if scan.status != 'running':
        return jsonify({"status": scan.status, "analysis": json.loads(scan.analysis_result or '{}')})

    # Get expected timeout from runner.py
    max_timeout = TIMEOUTS.get(scan.tool, 120) # Default to 120 seconds

    # Check for timeout
    if scan.start_time and (datetime.now(timezone.utc) - scan.start_time).total_seconds() > max_timeout:
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
        return jsonify({"status": "failed", "error": f"Scan timed out after {max_timeout} seconds."}), 200

    # Check if the process is still running or is a zombie
    if scan.pid:
        try:
            proc = psutil.Process(scan.pid)
            if proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE:
                return jsonify({"status": "running"})
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
        analysis = analyze_output(scan.tool, execution_result)
        risk_level = analysis.get("risk") or analysis.get("risk_level") or "unknown"
        
        # Update Database
        scan.status = 'completed'
        scan.execution_result = json.dumps(execution_result)
        scan.analysis_result = json.dumps(analysis)
        scan.risk_level = risk_level
        
        db.session.commit()

        return jsonify({"status": "completed", "analysis": analysis})

    except Exception as e:
        # Handle exceptions during result processing
        scan.status = 'failed'
        scan.analysis_result = json.dumps({"error": "Failed to process results", "details": str(e)})
        db.session.commit()
        return jsonify({"status": "failed", "error": str(e)}), 200
    
    finally:
        # Cleanup temp files
        _cleanup_temp_files(scan)