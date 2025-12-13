import json

def plan_scan(target: str):
    """
    AI LOGIC PLACEHOLDER
    nanti diganti Groq API
    """

    if target.startswith("http"):
        tool = "nikto"
        command = f"nikto -h {target}"
        reason = "Web vulnerability scan"
    else:
        tool = "nmap"
        command = f"nmap -sV -T4 {target}"
        reason = "Network service scan"

    return {
        "tool": tool,
        "command": command,
        "reason": reason
    }
