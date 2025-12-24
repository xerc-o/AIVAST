from typing import Dict, List
from .base import BaseAnalyzer

class NiktoAnalyzer(BaseAnalyzer):
    tool_name = "nikto"

    def build_prompt(self, data: dict) -> str:
        stdout = data["execution"].get("stdout", "")
        stderr = data["execution"].get("stderr", "")

        return f"""
You are a web security analyst.

ONLY return valid JSON.
DO NOT include explanations.
DO NOT use markdown.

JSON schema:
{{
  "risk": "info|low|medium|high",
  "issues": ["string"],
  "info": ["string"],
  "recommendations": ["string"]
}}

Nikto stdout:
{stdout}

Nikto stderr:
{stderr}
"""