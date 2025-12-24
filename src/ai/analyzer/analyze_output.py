from .nmap import NmapAnalyzer
from .nikto import NiktoAnalyzer

_ANALYZERS = {
    "nmap": NmapAnalyzer(),
    "nikto": NiktoAnalyzer(),
}

def analyze_output(tool: str, execution_data: dict) -> dict:
    analyzer = _ANALYZERS.get(tool)

    if not analyzer:
        return {
            "risk": "info",
            "summary": f"No analyzer for tool: {tool}"
        }

    return analyzer.analyze({
        "tool": tool,
        "execution": execution_data
    })