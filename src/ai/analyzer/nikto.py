from typing import Dict, List
from .base import BaseAnalyzer
from .structured_parser import extract_structured_data
import json

class NiktoAnalyzer(BaseAnalyzer):
    tool_name = "nikto"

    def build_prompt(self, data: dict) -> str:
        execution = data.get("execution", {})
        stdout = execution.get("stdout", "")
        stderr = execution.get("stderr", "")
        target = data.get("target", "Unknown")
        
        # Coba extract structured data
        structured = extract_structured_data("nikto", stdout, stderr)
        
        if structured.get("parsed"):
            nikto_data = json.dumps(structured, indent=2)
        else:
            nikto_data = self.truncate_text(f"Stdout: {stdout}\n\nStderr: {stderr}")

        return f"""
You are a Web Security Expert. Analyze the Nikto scan results with a critical and thorough eye.

Target: {target}
Nikto Output:
{nikto_data}

TASK:
Generate a high-quality, professional web application security analysis in JSON format.
You must be CRITICAL, DETAILED, and provide STRATEGIC next steps.

JSON schema:
{{
  "metadata": {{
    "target": "{target}",
    "confidence": "Low|Medium|High"
  }},
  "analysis": "In-depth technical analysis of the findings. Explain the vulnerabilities found, their context in a modern web environment, and how they contribute to the overall attack surface.",
  "issue": {{
    "type": "Primary web vulnerability (e.g. CSRF, XSS, Outdated Software, Security Header Missing)",
    "severity": "info|low|medium|high|critical",
    "endpoint": "Affected URI/Path",
    "parameter": "Specific header or field if applicable",
    "owasp": "Relevant OWASP Top 10 category"
  }},
  "evidence": {{
    "payload": "N/A or specific test URI used",
    "response_behavior": "Server response or behavior confirming the vulnerability"
  }},
  "impact": "Detailed assessment of the risk to the business and data integrity.",
  "recommendations": ["List of specific, actionable mitigation steps with priority"],
  "next_actions": ["Strategic next steps for a penetration tester to validate or exploit further"],
  "summary": "One-sentence executive summary of the finding."
}}

RULES:
- Return ONLY valid JSON.
- **Tool Self-Awareness**: You ONLY have access to these internal tools: `nmap`, `gobuster`, `nikto`, `sqlmap`. NEVER suggest Burp Suite or external software.
- **Strategic Chaining**: In 'next_actions', suggest `sqlmap` if parameters or injection hints are found.
- Focus on the most impactful vulnerabilities first.
- Be precise about versions and CVEs if they appear in the output.
"""