# src/ai/orchestrator.py
from .planner import plan_scan
from executor.runner import run_command
from .analyzer import analyze_output

def orchestrate_scan(target: str) -> dict:
    """
    Orchestrator utama yang menggabungkan planning, execution, dan analysis.
    """
    # 1. Planning
    plan = plan_scan(target)
    if not plan or "command" not in plan:
        return {"ok": False, "error": "planner failed"}
    
    # 2. Execution
    execution = run_command(plan["command"])
    if not execution.get("ok"):
        return {
            "ok": False,
            "error": "execution failed",
            "details": execution
        }
    
    # 3. Analysis
    analysis = analyze_output(plan["tool"], execution)
    
    return {
        "ok": True,
        "target": target,
        "plan": plan,
        "execution": execution,
        "analysis": analysis
    }