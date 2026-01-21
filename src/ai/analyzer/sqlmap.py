from .base import BaseAnalyzer
from .structured_parser import extract_structured_data
import json

class SQLMapAnalyzer(BaseAnalyzer):
    tool_name = "sqlmap"

    def build_prompt(self, data: dict) -> str:
        execution = data.get("execution", {})
        stdout = execution.get("stdout", "")
        stderr = execution.get("stderr", "")
        target = data.get("target", "Unknown")
        
        # Extract structured data
        structured = extract_structured_data("sqlmap", stdout, stderr)
        if structured.get("parsed"):
            sqlmap_data = f"Vulnerable: {structured.get('vulnerable')}\nPayloads: {json.dumps(structured.get('payloads', []), indent=2)}"
        else:
            sqlmap_data = self.truncate_text(stdout)

        return f"""
You are a Database Security Expert. Analyze the SQLMap automated injection test results with extreme detail and critical thinking.

Target: {target}
SQLMap Data:
{sqlmap_data}

TASK:
Provide a PROFESSIONAL and DEEP technical analysis in JSON format.
Identify the exact nature of the vulnerability, its scope, and the critical path for remediation.

JSON schema:
{{
  "metadata": {{
    "target": "{target}",
    "confidence": "Low|Medium|High"
  }},
  "analysis": "In-depth technical analysis of the SQL injection results. Explain how the application handles parameters and why it is (or isn't) susceptible to specific injection types (Boolean, Error, Time-based, etc.).",
  "issue": {{
    "type": "Specific SQL Injection type (e.g. 'Boolean-based blind', 'Error-based', 'Union-query')",
    "severity": "critical|high|medium|low",
    "endpoint": "Affected URL/endpoint",
    "parameter": "Vulnerable parameter name",
    "owasp": "A03:2021 – Injection"
  }},
  "evidence": {{
    "payload": "The working payload that confirmed the vulnerability",
    "response_behavior": "Server response or behavior (e.g. 'Database error revealed in response', 'Fixed time delay observed')"
  }},
  "impact": "Clinical assessment of what an attacker can steal (data extraction), modify (data integrity), or the potential for OS-level access if DBA privileges are found.",
  "recommendations": ["List of specific, actionable mitigation steps (Prepared Statements, Parameterized Queries, etc.)"],
  "next_actions": ["Next steps: Check for more vulnerable parameters, test for data dump capabilities, evaluate WAF bypasses."],
  "summary": "One-sentence executive summary of the SQL injection vulnerability."
}}

RULES:
- Return ONLY valid JSON.
- **Tool Self-Awareness**: You ONLY have access to these internal tools: `nmap`, `gobuster`, `nikto`, `sqlmap`. NEVER suggest external software like Burp Suite.
- Be very specific about the 'Impact'.
- If no vulnerability is confirmed, analysis should still be detailed about what was tested and why it failed.
"""
