from executor.runner import run_command


def analyze_output(tool: str, output: str):
    findings = []
    recommendations = []

    if tool == "nmap":
        if "22/tcp" in output:
            findings.append("SSH service exposed (port 22)")
            recommendations.append("Check SSH version and disable root login")

        if "80/tcp" in output:
            findings.append("HTTP service detected (port 80)")
            recommendations.append("Run Nikto for web vulnerability scan")

        if "31337/tcp" in output:
            findings.append("Suspicious port 31337 open")
            recommendations.append("Investigate potential backdoor service")

    risk = "Low"
    if len(findings) >= 3:
        risk = "Medium"

    return {
        "risk_level": risk,
        "findings": findings,
        "recommendations": recommendations
    }
