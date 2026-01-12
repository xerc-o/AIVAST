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
{json.dumps(structured.get('ports', []), indent=2)}
"""
            nmap_data = structured_summary
        else:
            nmap_data = stdout
        
        return f"""
You are a cybersecurity analyst. Your goal is to analyze the Nmap scan results and provide a clear, concise, and actionable security report.

Return ONLY valid JSON.
DO NOT include explanations outside the JSON.
DO NOT use markdown formatting (e.g., ```json).

JSON schema:
{{
  "risk": "info|low|medium|high|critical",
  "summary": "A comprehensive summary of the key findings, potential vulnerabilities, and the overall security posture based on the Nmap output. This summary should clearly state the most important security implications.",
  "findings": [
    {{
      "port": "string",
      "service": "string",
      "vulnerability": "string (e.g., 'Outdated software', 'Weak configuration', 'Unnecessary service')",
      "severity": "low|medium|high|critical",
      "details": "string (e.g., 'FTP service version X.Y.Z is known to have vulnerability CVE-YYYY-NNNN')",
      "recommendation": "string (e.g., 'Update FTP server to latest version', 'Disable anonymous FTP access')"
    }}
  ],
  "recommendations": [
    "string (general high-level recommendations, e.g., 'Implement a robust patching strategy', 'Review exposed services', 'Configure firewall rules more strictly')",
    "string"
  ]
}}

Nmap output (structured data or raw text if parsing failed):
{nmap_data}

Based on the Nmap output provided, generate the JSON response. Pay close attention to the version numbers of services, common misconfigurations, and known vulnerabilities associated with detected services. If specific CVEs or detailed recommendations are not immediately apparent from the Nmap output alone, provide general security best practices relevant to the identified services.
"""