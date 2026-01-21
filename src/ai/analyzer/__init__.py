from .nmap import NmapAnalyzer
from .nikto import NiktoAnalyzer
from .gobuster import GobusterAnalyzer
from .sqlmap import SQLMapAnalyzer

_ANALYZERS = {
    "nmap": NmapAnalyzer(),
    "nikto": NiktoAnalyzer(),
    "gobuster": GobusterAnalyzer(),
    "sqlmap": SQLMapAnalyzer(),
}

def analyze_output(tool: str, execution_data: dict, target: str = None) -> dict:
    """
    Analyze output dari tool execution menggunakan AI.
    
    Args:
        tool: Nama tool
        execution_data: Dict dari run_command()
        target: Target address (IP/Domain/URL)
    
    Returns:
        dict: Analysis result dari LLM (sudah parsed JSON)
    """
    # Validasi tool
    tool = (tool or "").lower()
    analyzer = _ANALYZERS.get(tool)
    
    if not analyzer:
        return {
            "risk": "info",
            "summary": f"No analyzer for tool: {tool}",
            "error": "unknown_tool"
        }
    
    # Validasi execution data
    if not execution_data or not execution_data.get("ok"):
        return {
            "risk": "unknown",
            "summary": "Execution failed or invalid",
            "error": "execution_failed",
            "execution_details": execution_data
        }
    
    try:
        result = analyzer.analyze({
            "tool": tool,
            "execution": execution_data,
            "target": target
        })
        return result
    except Exception as e:
        return {
            "risk": "unknown",
            "summary": f"Analysis failed: {str(e)}",
            "error": "analysis_exception"
        }