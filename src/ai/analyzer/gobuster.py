from .base import BaseAnalyzer
from .structured_parser import extract_structured_data
import json

class GobusterAnalyzer(BaseAnalyzer):
    tool_name = "gobuster"

    def build_prompt(self, data: dict) -> str:
        execution = data.get("execution", {})
        stdout = execution.get("stdout", "")
        stderr = execution.get("stderr", "")
        target = data.get("target", "Unknown")
        
        # Extract structured data
        structured = extract_structured_data("gobuster", stdout, stderr)
        if structured.get("parsed"):
            gobuster_data = json.dumps(structured.get('findings', []), indent=2)
        else:
            gobuster_data = self.truncate_text(stdout)

        return f"""
You are a penetration testing expert. Analyze the Gobuster directory/file brute-forcing results.

Target: {target}
Gobuster Findings:
{gobuster_data}

TASK:
Provide a PROFESSIONAL and CRITICAL analysis of the discovered paths in JSON format.
Consider the context of each path (e.g., admin panels, config files, backups).

JSON schema:
{{
  "metadata": {{
    "target": "{target}",
    "confidence": "Medium|High"
  }},
  "analysis": "Technical overview of the discovered directory structure. Explain the significance of found paths and what they reveal about the application's configuration or hidden features.",
  "issue": {{
    "type": "Information Disclosure / Exposed Management Interface / Sensitive File Found",
    "severity": "info|low|medium|high|critical",
    "endpoint": "Most critical path found",
    "parameter": "N/A",
    "owasp": "A01:2021 – Broken Access Control or A05:2021 – Security Misconfiguration"
  }},
  "evidence": {{
    "payload": "Wordlist used (if known) or discovery method",
    "response_behavior": "Status codes and content lengths that indicate valid paths"
  }},
  "impact": "Potential for unauthorized access, data theft, or system compromise based on the found paths.",
  "recommendations": ["List of specific steps to secure the discovered paths (e.g. 'Restrict access to /admin', 'Remove .bak files')"],
  "next_actions": ["Next logical steps for a red teamer (e.g. 'Brute force login at /login', 'Inspect /config for secrets')"],
  "summary": "One-sentence executive summary of the directory scan results."
}}

RULES:
- Return ONLY valid JSON.
- **Tool Self-Awareness**: You ONLY have access to these internal tools: `nmap`, `gobuster`, `nikto`, `sqlmap`. NEVER suggest Burp Suite or external software.
- **Strategic Chaining**: In 'next_actions', suggest `nikto` for vulnerability analysis of found paths or `sqlmap` if endpoints with parameters are discovered.
- Be extremely specific about the risks of the found paths.
"""
