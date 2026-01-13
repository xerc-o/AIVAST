from typing import Dict
from .llm.groq import call_groq
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
def plan_scan_ai(target: str, forced_tool: str = None) -> Dict[str, str]:
    """
    AI-powered planner yang menggunakan LLM untuk menentukan tool terbaik.
    """
    
    # If forced_tool is provided, we can skip AI or guide it to just generate params?
    # For now, let's just force the tool in the prompt to ensure correct command generation for that tool.
    
    tool_instruction = ""
    if forced_tool:
        tool_instruction = f"User has explicitly selected {forced_tool}. YOU MUST USE {forced_tool}."

    prompt = f"""You are a cybersecurity expert. Given a target, determine the best scanning tool and command.
{tool_instruction}

Target: {target}

Return ONLY valid JSON with this exact schema (no markdown, no explanations, no code blocks):
{{
  "tool": "nmap|nikto",
  "command": "full command string",
  "reason": "brief explanation"
}}

Available tools:
- nmap: Network port and service scanner. Use for IP addresses, hostnames, or when you need to discover open ports and services.
- nikto: Web vulnerability scanner. Use ONLY for http:// or https:// URLs.

Rules:
- If target starts with http:// or https://, use nikto
- If target is IP address or hostname (without http/https), use nmap
- For nmap, use: "nmap -sV -T4 -oX - [target]"
- For nikto, use: "nikto -h [target]"
- IF USER SELECTED A TOOL, IGNORE DEFAULT RULES AND USE THAT TOOL.

Target: {target}"""

    try:
        response = call_groq(prompt)
        
        # Clean response (remove markdown code blocks if any)
        response = response.strip()
        if response.startswith("on"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        plan = json.loads(response)
        
        # Validate and sanitize
        if plan.get("tool") not in ["nmap", "nikto"]:
             # If AI hallucinated or refused, fallback to forced tool if present
             if forced_tool:
                 return plan_scan_rule_based(target, forced_tool)
             raise ValueError(f"Invalid tool: {plan.get('tool')}. Must be 'nmap' or 'nikto'")
        
        command_str = plan.get("command")
        if not command_str:
            raise ValueError("Missing 'command' in AI response")
            
        # Security: Use shlex to parse the command string
        command_list = shlex.split(command_str)
        plan["command"] = command_list
        
        # Override tool name just in case
        if forced_tool and plan.get("tool") != forced_tool:
             print(f"⚠️ AI returned {plan.get('tool')} but user forced {forced_tool}. Fallback to rule-based.")
             return plan_scan_rule_based(target, forced_tool)

        # Log untuk debugging
        print(f"✅ AI Planner selected: {plan.get('tool')} - {plan.get('reason', 'N/A')}")
            
        return plan
    except Exception as e:
        print(f"❌ AI Planner Error: {str(e)}")
        # Fallback to rule based with forced tool
        return plan_scan_rule_based(target, forced_tool)


# ==========================================================
# PUBLIC API (DIPANGGIL ORCHESTRATOR)
# ==========================================================
def plan_scan(target: str, use_ai: bool = False, tool: str = None) -> Dict[str, str]:
    """
    Entry point planner.

    use_ai=False -> rule-based (default, aman)
    use_ai=True  -> AI-powered (lebih fleksibel)
    tool         -> Optional forced tool name (nmap/nikto)
    """

    if use_ai:
        try:
            print(f"🤖 Using AI Planner for target: {target} (Tool: {tool})")
            result = plan_scan_ai(target, forced_tool=tool)
            print(f"✅ AI Planner result: {result.get('tool')} - {result.get('command')}")
            return result
        except Exception as e:
            # Fallback ke rule-based jika AI gagal
            print(f"⚠️ Warning: AI planner failed ({str(e)}), falling back to rule-based")
            return plan_scan_rule_based(target, forced_tool=tool)
    else:
        print(f"📋 Using Rule-Based Planner for target: {target} (Tool: {tool})")

    return plan_scan_rule_based(target, forced_tool=tool)