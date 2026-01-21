import shlex
import shutil
import subprocess
import tempfile
import socket
from urllib.parse import urlparse
from typing import Dict, Union, Tuple

ALLOWED_TOOLS = {"nmap", "nikto", "gobuster", "dirb", "sqlmap"}
FORBIDDEN_ARGS = {"--script", "--datadir", "-oA", "-oN"} # Removed -oX and -oN from strictly forbidden if we want flexibility
TIMEOUTS = {
    "nmap": 600,   # Increased to 10 minutes
    "nikto": 1200, # Increased to 20 minutes
    "gobuster": 600,
    "dirb": 600,
    "sqlmap": 1200
}
MAX_OUTPUT = 50000 

def normalize_target(target: str, tool: str) -> str:
    """
    Normalizes a target based on the tool.
    - Nikto/Gobuster/SQLMap (Web): Adds http:// if missing.
    - Nmap (Network): Strips protocol if present.
    """
    target = (target or "").strip()
    if not target: return target

    tool = (tool or "").lower()
    parsed = urlparse(target)
    
    # Web tools: Need protocol
    if tool in ["nikto", "gobuster", "dirb", "sqlmap"]:
        if not parsed.scheme:
            # Check if it's already an IP or domain-like
            return f"http://{target}"
        return target
        
    # Network tools: Need raw host/IP
    elif tool == "nmap":
        if parsed.scheme:
            # Strip scheme and return hostname
            return parsed.hostname or target
        return target
        
    return target

def check_reachability(target: str) -> Tuple[bool, str]:
    """
    Checks if the target is up/reachable before scanning.
    Supports IPs, domains, and URLs.
    """
    try:
        # 1. Parsing target
        parsed = urlparse(target)
        host = parsed.hostname or target
        port = parsed.port
        
        # Determine port if not specified
        if not port:
            if parsed.scheme == "https": port = 443
            elif parsed.scheme == "http": port = 80
            else: port = 80 # Default to 80 for raw IPs/hostnames in reachability check
            
        # 2. Try simple socket connection
        # Resolve hostname first
        ip = socket.gethostbyname(host)
        
        # Try connect
        with socket.create_connection((ip, port), timeout=5):
            return True, "Target is reachable"
            
    except socket.timeout:
        return False, f"Connection timeout to {target} (Host up but port {port} filtered?)"
    except Exception as e:
        return False, f"Target unreachable: {str(e)}"

def run_command_async(command: list) -> Dict:
    """
    Executes a command as a background process, redirecting output to temp files.
    This is non-blocking.
    """
    if not command:
        return {"ok": False, "error": "Empty command"}

    tool = command[0]
    args = command

    # Security Check: Whitelist tool
    tool_path = shutil.which(tool)
    if tool not in ALLOWED_TOOLS or tool_path is None:
        return {"ok": False, "error": "Tool not allowed or not found"}

    # Security Check: Forbidden arguments (simple check)
    for i, arg in enumerate(args):
        arg_base = arg.split("=", 1)[0]
        if arg_base in FORBIDDEN_ARGS:
            # allow safe special-case: nmap '-oX -' (output XML to stdout)
            if arg_base == "-oX" and tool == "nmap":
                next_arg = args[i+1] if i+1 < len(args) else None
                if next_arg == "-":
                    continue
            return {"ok": False, "error": "Forbidden argument detected"}

    try:
        # Create temporary files for stdout and stderr
        stdout_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', prefix=f'{tool}-', suffix='-stdout.log')
        stderr_file = tempfile.NamedTemporaryFile(delete=False, mode='w+', prefix=f'{tool}-', suffix='-stderr.log')

        if tool == "sqlmap":
            if "--batch" not in args:
                args.append("--batch")
            if "--random-agent" not in args:
                args.append("--random-agent")

        proc = subprocess.Popen(
            args,
            stdout=stdout_file,
            stderr=stderr_file,
            text=True,
            close_fds=True
        )

        return {
            "ok": True,
            "pid": proc.pid,
            "stdout_path": stdout_file.name,
            "stderr_path": stderr_file.name,
            "tool": tool,
        }

    except FileNotFoundError as fnf:
        return {"ok": False, "error": "executable not found", "details": str(fnf)}
    except Exception as e:
        return {"ok": False, "error": "exception", "details": str(e)}


def run_command(command: list) -> Dict:
    """
    Executes a command synchronously and returns structured result.
    Uses absolute executable path (shutil.which) and sanitizes args.
    """
    if not command:
        return {"ok": False, "error": "Empty command"}

    tool = command[0]
    args = command

    # Resolve executable path and whitelist tool
    tool_path = shutil.which(tool)
    if tool not in ALLOWED_TOOLS or tool_path is None:
        return {"ok": False, "error": "Tool not allowed or not found"}

    # Forbidden arguments check with safe exception for 'nmap -oX -'
    for i, arg in enumerate(args):
        key = arg.split("=", 1)[0]
        if key in FORBIDDEN_ARGS:
            if key == "-oX" and tool == "nmap":
                # allow '-oX -' (XML to stdout) only
                next_arg = args[i+1] if i+1 < len(args) else None
                if next_arg == "-":
                    continue
            return {"ok": False, "error": "Forbidden argument detected"}

    # Build sanitized arg list
    sanitized_args = args[1:]
    if tool == "sqlmap":
        if "--batch" not in sanitized_args:
            sanitized_args.append("--batch")
        if "--random-agent" not in sanitized_args:
            sanitized_args.append("--random-agent")

    try:
        result = subprocess.run(
            [tool_path, *sanitized_args],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUTS.get(tool, 120)
        )

        return {
            "ok": True,
            "tool": tool,
            "returncode": result.returncode,
            "stdout": (result.stdout or "")[:MAX_OUTPUT],
            "stderr": (result.stderr or "")[:MAX_OUTPUT],
        }

    except subprocess.TimeoutExpired as te:
        return {
            "ok": False,
            "error": "timeout",
            "details": str(te),
            "stdout": (getattr(te, "output", "") or "")[:MAX_OUTPUT],
            "stderr": (getattr(te, "stderr", "") or "")[:MAX_OUTPUT],
        }
    except FileNotFoundError as fnf:
        return {"ok": False, "error": "executable not found", "details": str(fnf)}
    except Exception as e:
        return {"ok": False, "error": "exception", "details": str(e)}
