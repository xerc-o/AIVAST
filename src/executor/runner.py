import shlex
import shutil
import subprocess
from typing import Dict

ALLOWED_TOOLS = {"nmap", "nikto"}
FORBIDDEN_ARGS = {"--script", "--datadir", "-oA", "-oN", "-oX"}
TIMEOUTS = {
    "nmap": 180,
    "nikto": 300
}
MAX_OUTPUT = 20000


def run_command(command: str) -> Dict:
    args = shlex.split(command)
    if not args:
        return {"ok": False, "error": "Empty command"}

    tool = args[0]

    # Whitelist tool + PATH validation
    tool_path = shutil.which(tool)
    if tool not in ALLOWED_TOOLS or tool_path is None:
        return {"ok": False, "error": "Tool not allowed or not found"}

    # Forbidden arguments
    if any(arg.split("=", 1)[0] in FORBIDDEN_ARGS or any(arg.startswith(p) for p in FORBIDDEN_ARGS)
           for arg in args):
        return {"ok": False, "error": "Forbidden argument detected"}

    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=TIMEOUTS.get(tool, 120),
            check=False
        )

        return {
            "ok": True,
            "tool": tool,
            "returncode": proc.returncode,
            "stdout": proc.stdout[:MAX_OUTPUT],
            "stderr": proc.stderr[:MAX_OUTPUT],
        }

    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout"}
    except FileNotFoundError as fnf:
        return {"ok": False, "error": "executable not found", "details": str(fnf)}
    except Exception as e:
        return {"ok": False, "error": "exception", "details": str(e)}
