from .base import BaseAnalyzer

class NmapAnalyzer(BaseAnalyzer):
    tool_name = "nmap"

    def build_prompt(self, data: dict) -> str:
        return f"""
You are a cybersecurity analyst.

ONLY return valid JSON.
DO NOT include explanations.
DO NOT use markdown.

JSON schema:
{{
  "risk": "info|low|medium|high",
  "summary": "string",
  "findings": [
    {{
      "port": "string",
      "service": "string",
      "note": "string"
    }}
  ],
  "recommendations": ["string"]
}}

Nmap output:
{data['execution']['stdout']}
"""