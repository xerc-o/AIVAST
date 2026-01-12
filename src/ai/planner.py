from typing import Dict
from .llm.groq import call_groq
import json
import shlex


# ==========================================================
# RULE-BASED PLANNER (DEFAULT & SAFE)
# ==========================================================
def plan_scan_rule_based(target: str) -> Dict[str, str]:
    """
    Planner tanpa AI.
    Aman, deterministik, cocok untuk testing awal.
    """

    target = target.strip()

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
def plan_scan_ai(target: str) -> Dict[str, str]:
    """
    AI-powered planner yang menggunakan LLM untuk menentukan tool terbaik.
    """
    prompt = f"""You are a cybersecurity expert. Given a target, determine the best scanning tool and command.

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
            raise ValueError(f"Invalid tool: {plan.get('tool')}. Must be 'nmap' or 'nikto'")
        
        command_str = plan.get("command")
        if not command_str:
            raise ValueError("Missing 'command' in AI response")
            
        # Security: Use shlex to parse the command string
        command_list = shlex.split(command_str)
        plan["command"] = command_list

        # Log untuk debugging
        print(f"✅ AI Planner selected: {plan.get('tool')} - {plan.get('reason', 'N/A')}")
            
        return plan
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse AI response as JSON: {str(e)}. Response: {response[:200]}"
        print(f"❌ AI Planner JSON Error: {error_msg}")
        raise ValueError(error_msg)
    except KeyError as e:
        error_msg = f"Missing required field in AI response: {str(e)}"
        print(f"❌ AI Planner KeyError: {error_msg}")
        raise ValueError(error_msg)
    except Exception as e:
        error_msg = f"AI planner failed: {str(e)}"
        print(f"❌ AI Planner Exception: {error_msg}")
        raise ValueError(error_msg)


# ==========================================================
# PUBLIC API (DIPANGGIL ORCHESTRATOR)
# ==========================================================
def plan_scan(target: str, use_ai: bool = False) -> Dict[str, str]:
    """
    Entry point planner.

    use_ai=False -> rule-based (default, aman)
    use_ai=True  -> AI-powered (lebih fleksibel)
    """

    if use_ai:
        try:
            print(f"🤖 Using AI Planner for target: {target}")
            result = plan_scan_ai(target)
            print(f"✅ AI Planner result: {result.get('tool')} - {result.get('command')}")
            return result
        except Exception as e:
            # Fallback ke rule-based jika AI gagal
            print(f"⚠️ Warning: AI planner failed ({str(e)}), falling back to rule-based")
            return plan_scan_rule_based(target)
    else:
        print(f"📋 Using Rule-Based Planner for target: {target}")

    return plan_scan_rule_based(target)