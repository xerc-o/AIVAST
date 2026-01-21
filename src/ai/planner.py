from typing import Dict
from .llm.groq import call_groq
from .analyzer.parser import safe_parse_json
import json
import shlex


# ==========================================================
# RULE-BASED PLANNER (DEFAULT & SAFE)
# ==========================================================
def plan_scan_rule_based(target: str, forced_tool: str = None) -> Dict[str, str]:
    """
    Planner tanpa AI.
    Aman, deterministik, cocok untuk testing awal.
    """

    target = target.strip()

    # Respect user choice if provided
    if forced_tool:
        tool = forced_tool.lower()
        if tool == "nikto":
            return {
                "tool": "nikto",
                "command": ["nikto", "-h", target, "-Format", "xml"],
                "reason": "User selected Nikto"
            }
        elif tool == "nmap":
            return {
                "tool": "nmap",
                "command": ["nmap", "-sV", "-T4", "-oX", "-", target],
                "reason": "User selected Nmap"
            }

    # Default logic
    if target.startswith("http://") or target.startswith("https://"):
        return {
            "tool": "nikto",
            "command": ["nikto", "-h", target, "-Format", "xml"],
            "reason": "Web vulnerability scan (rule-based, xml output)"
        }

    return {
        "tool": "nmap",
        "command": ["nmap", "-sV", "-T4", "-oX", "-", target],
        "reason": "Network service scan (rule-based, xml stdout)"
    }


# ==========================================================
# AI PLANNER (IMPLEMENTASI LENGKAP)
# ==========================================================
def plan_scan_ai(target: str, forced_tool: str = None, history: str = None, deep_scan: bool = False) -> Dict[str, str]:
    """
    AI-powered planner yang menggunakan LLM untuk menentukan tool terbaik.
    Dapat beradaptasi berdasarkan history scan sebelumnya.
    """
    
    tool_instruction = ""
    if forced_tool:
        tool_instruction = f"User has explicitly selected {forced_tool}. YOU MUST USE {forced_tool}."

    scan_mode = "Deep & Comprehensive" if deep_scan else "Standard / Adaptive"

    prompt = f"""You are a Lead Cybersecurity Penetration Tester. Your goal is to plan an effective scanning strategy.
Mode: {scan_mode}
{tool_instruction}

Target: {target}

PREVIOUS SCAN CONTEXT (if any):
{history if history else "No previous history for this target."}

TASK:
1. Select the best tool from the available list.
2. Generate the exact command string. 
3. Provide a 'rationale' explaining why this tool and these specific flags were chosen.

AVAILABLE TOOLS:
- nmap: Network scanner. Use for IPs/Hostnames. Standard: `nmap -sV -T4 -oX - [target]`. Aggressive: `nmap -A -T4 -oX - [target]`.
- nikto: Web vulnerability scanner. Use for http/https. Command: `nikto -h [target]`.
- gobuster: Directory/File brute-forcing. Use for web targets. Command: `gobuster dir -u [target] -w data/wordlists/default_common.txt`.
- sqlmap: Automated SQL injection discovery. Use if target likely has parameters. Command: `sqlmap -u [target] --batch --random-agent`. (ALWAYS use --batch for automated mode).

ADAPTIVITY RULES:
- If MODE is 'Deep & Comprehensive', choose the most aggressive flags.
- If PREVIOUS CONTEXT shows a tool failed or results were sparse, CHOOSE A DIFFERENT TOOL or DIFFERENT FLAGS to find vulnerabilities.
- If target is 'alot' (difficult/stubborn), use stealthier or more exhaustive options.

Return ONLY valid JSON (no markdown):
{{
  "tool": "tool_name",
  "command": "full command string",
  "rationale": "Expert explanation of why this was chosen and how it adapts to the target."
}}
"""

    try:
        response = call_groq(prompt)
        plan = safe_parse_json(response)
        
        if "error" in plan and "tool" not in plan:
             # If parsing failed, return default
             return plan_scan_rule_based(target, forced_tool)

        # Validate tool
        allowed = ["nmap", "nikto", "gobuster", "dirb", "sqlmap"]
        if plan.get("tool") not in allowed:
             if forced_tool and forced_tool in allowed:
                  return plan_scan_rule_based(target, forced_tool)
             plan["tool"] = "nmap" # Default fallback
        
        command_str = plan.get("command")
        if not command_str:
             default_plan = plan_scan_rule_based(target, forced_tool)
             plan["command"] = default_plan["command"]
             plan["rationale"] = "Fallback to default due to empty AI command."
        else:
             # Security: Parse with shlex
             plan["command"] = shlex.split(command_str)
        
        # Logging
        print(f"✅ AI Expert Planner selected: {plan.get('tool')} - {plan.get('rationale')}")
            
        return plan
    except Exception as e:
        print(f"❌ AI Expert Planner Error: {str(e)}")
        # Fallback to rule based with forced tool
        return plan_scan_rule_based(target, forced_tool)


# ==========================================================
# PUBLIC API (DIPANGGIL ORCHESTRATOR)
# ==========================================================
def plan_scan(target: str, use_ai: bool = False, tool: str = None, history: str = None, deep_scan: bool = False) -> Dict[str, str]:
    """
    Entry point planner.

    use_ai=False -> rule-based (default, aman)
    use_ai=True  -> AI-powered (lebih fleksibel)
    tool         -> Optional forced tool name (nmap/nikto)
    """

    if use_ai:
        try:
            print(f"🤖 Using AI Expert Planner for target: {target} (Mode: {'Deep' if deep_scan else 'Standard'})")
            result = plan_scan_ai(target, forced_tool=tool, history=history, deep_scan=deep_scan)
            return result
        except Exception as e:
            # Fallback ke rule-based jika AI gagal
            print(f"⚠️ Warning: AI planner failed ({str(e)}), falling back to rule-based")
            return plan_scan_rule_based(target, forced_tool=tool)
    else:
        print(f"📋 Using Rule-Based Planner for target: {target} (Tool: {tool})")

    return plan_scan_rule_based(target, forced_tool=tool)