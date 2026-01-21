from .base import BaseAnalyzer
from .structured_parser import extract_structured_data
import json


class NmapAnalyzer(BaseAnalyzer):
    tool_name = "nmap"

    def build_prompt(self, data: dict) -> str:
        execution = data.get("execution", {})
        stdout = execution.get("stdout", "")
        target = data.get("target", "Unknown")
        
        # Coba extract structured data
        structured = extract_structured_data("nmap", stdout)
        
        if structured.get("parsed"):
            nmap_data = json.dumps(structured, indent=2)
        else:
            nmap_data = self.truncate_text(stdout)
        
        return f"""
You are a Senior Cybersecurity Analyst. Analyze the Nmap scan results with clinical precision and deep technical insight.

Target: {target}
Nmap Output:
{nmap_data}

TASK:
Generate a high-quality, professional security analysis in JSON format.
Your analysis must be CRITICAL, DETAILED, and ACTIONABLE.

JSON schema:
{{
  "metadata": {{
    "target": "{target}",
    "confidence": "Low|Medium|High"
  }},
  "analysis": "Detailed technical analysis of what was observed. Explain the state of the target based ONLY on the data.",
  "issue": {{
    "type": "Primary vulnerability class or configuration issue",
    "severity": "info|low|medium|high|critical",
    "endpoint": "Affected port/service",
    "parameter": "N/A or specific service detail",
    "owasp": "Relevant OWASP category if applicable"
  }},
  "evidence": {{
    "payload": "N/A or specific probe/flag used",
    "response_behavior": "Observation that confirms the status (e.g. 'Server responded with version X')"
  }},
  "impact": "High-level professional assessment of what an attacker could achieve.",
  "recommendations": ["List of specific, actionable mitigation steps"],
  "next_actions": ["Strategic next steps for further testing or investigation"],
  "summary": "One-sentence executive summary of the finding."
}}

RULES:
- Return ONLY valid JSON.
- **Tool Awareness**: You ONLY have access to these internal tools: `nmap`, `gobuster`, `nikto`, `sqlmap`. NEVER suggest Burp Suite.
- **Strategic Chaining**: If web services are found, suggest `gobuster` or `nikto` in 'next_actions'.
- Be technical and professional.
- Avoid generic advice; be specific to the versions or services found.
- If multiple issues exist, focus on the most critical one in the 'issue' block, but mention others in 'analysis'.
"""