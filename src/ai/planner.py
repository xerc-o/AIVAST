from typing import Dict


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
            "command": f"nikto -h {target}",
            "reason": "Web vulnerability scan (rule-based)"
        }

    return {
        "tool": "nmap",
        "command": f"nmap -sV -T4 {target}",
        "reason": "Network service scan (rule-based)"
    }


# ==========================================================
# AI PLANNER (OPTIONAL - FUTURE USE)
# ==========================================================
def plan_scan_ai(target: str) -> Dict[str, str]:
    """
    Placeholder AI planner.
    Saat ini BELUM aktif karena LLM belum ada.
    """

    raise NotImplementedError("LLM planner not implemented yet")


# ==========================================================
# PUBLIC API (DIPANGGIL ORCHESTRATOR)
# ==========================================================
def plan_scan(target: str, use_ai: bool = False) -> Dict[str, str]:
    """
    Entry point planner.

    use_ai=False -> rule-based
    use_ai=True  -> AI (jika tersedia)
    """

    if use_ai:
        try:
            return plan_scan_ai(target)
        except Exception:
            # fallback keras
            return plan_scan_rule_based(target)

    return plan_scan_rule_based(target)
