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
        
        # Coba extract structured data
        structured = extract_structured_data("nikto", stdout, stderr)
        
        # Jika berhasil parse, gunakan structured data
        if structured.get("parsed"):
            structured_summary = f"""
Parsed Nikto Data:
- Target: {structured.get('target', {}).get('targetip', 'N/A')}
- Items found: {len(structured.get('items', []))}
- Statistics: {json.dumps(structured.get('statistics', {}), indent=2)}

Vulnerabilities/Issues:
{json.dumps(structured.get('items', [])[:20], indent=2)}
"""
            nikto_data = structured_summary
        else:
            nikto_data = f"Stdout: {stdout}\n\nStderr: {stderr}"

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

Nikto output:
{nikto_data}
"""