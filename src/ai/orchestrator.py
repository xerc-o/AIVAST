from .planner import plan_scan
from ..executor.runner import run_command
from .analyzer import analyze_output


def orchestrate_scan(target: str, use_ai_planner: bool = False) -> dict:
    """
    Orchestrator utama yang menggabungkan planning, execution, dan analysis.
    
    Args:
        target: Target untuk di-scan (URL atau IP/hostname)
        use_ai_planner: Jika True, gunakan AI planner (jika tersedia)
    
    Returns:
        dict dengan struktur:
        {
            "ok": bool,
            "target": str,
            "plan": dict,
            "execution": dict,
            "analysis": dict,
            "error": str (jika ok=False)
        }
    """
    # 1. Planning
    try:
        plan = plan_scan(target, use_ai=use_ai_planner)
        if not plan or "command" not in plan:
            return {
                "ok": False,
                "error": "planner failed",
                "target": target
            }
    except Exception as e:
        return {
            "ok": False,
            "error": f"planner exception: {str(e)}",
            "target": target
        }
    
    # 2. Execution
    try:
        execution = run_command(plan["command"])
        if not execution.get("ok"):
            return {
                "ok": False,
                "error": "execution failed",
                "target": target,
                "plan": plan,
                "details": execution
            }
    except Exception as e:
        return {
            "ok": False,
            "error": f"execution exception: {str(e)}",
            "target": target,
            "plan": plan
        }
    
    # 3. Analysis
    try:
        analysis = analyze_output(plan["tool"], execution)
    except Exception as e:
        return {
            "ok": False,
            "error": f"analysis exception: {str(e)}",
            "target": target,
            "plan": plan,
            "execution": execution
        }
    
    return {
        "ok": True,
        "target": target,
        "plan": plan,
        "execution": execution,
        "analysis": analysis
    }