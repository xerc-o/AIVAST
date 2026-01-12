import shlex
import shutil
import subprocess
import tempfile
from typing import Dict

ALLOWED_TOOLS = {"nmap", "nikto"}
FORBIDDEN_ARGS = {"--script", "--datadir", "-oA", "-oN", "-oX"}
TIMEOUTS = {
    "nmap": 180,
    "nikto": 300
}
MAX_OUTPUT = 20000

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

    # Build sanitized arg list (simply copy args[1:] as checks already performed)
    sanitized_args = args[1:]

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
