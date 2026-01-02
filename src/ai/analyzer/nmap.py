from .base import BaseAnalyzer
from .structured_parser import extract_structured_data

class NmapAnalyzer(BaseAnalyzer):
    tool_name = "nmap"

    def build_prompt(self, data: dict) -> str:
        execution = data.get("execution", {})
        stdout = execution.get("stdout", "")
        
        # Coba extract structured data
        structured = extract_structured_data("nmap", stdout)
        
        # Jika berhasil parse, gunakan structured data
        if structured.get("parsed"):
            structured_summary = f"""
Parsed Nmap Data:
- Hosts found: {len(structured.get('hosts', []))}
- Ports found: {len(structured.get('ports', []))}
- Services: {len(structured.get('services', []))}

Ports and Services:
{json.dumps(structured.get('ports', [])[:20], indent=2)}
"""
            nmap_data = structured_summary
        else:
            nmap_data = stdout
        
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
{nmap_data}
"""