import shlex
import shutil
import subprocess
import signal
from typing import Dict

ALLOWED_TOOLS = {"nmap", "nikto"}
FORBIDDEN_ARGS = {"--script", "--datadir", "-oA", "-oN", "-oX"}
TIMEOUTS = {
    "nmap": 180,
    "nikto": 300
}
MAX_OUTPUT = 20000
DEFAULT_TIMEOUT = 120


def _add_structured_output_args(args: list, tool: str) -> list:
    """
    Tambahkan argument untuk output terstruktur ke command.
    Output akan ke stdout, bukan file (aman).
    """
    if tool == "nmap":
        # nmap: gunakan -oJ untuk JSON output ke stdout
        # Note: -oJ output ke file, jadi kita gunakan kombinasi
        # Kita akan parse dari stdout biasa, atau gunakan -o- untuk XML ke stdout
        # Tapi untuk keamanan, kita tetap gunakan stdout biasa dan parse dengan parser
        # Alternatif: gunakan nmap dengan format yang lebih terstruktur
        pass  # Akan dihandle oleh parser
    elif tool == "nikto":
        # nikto: gunakan -Format xml untuk XML output
        if "-Format" not in args and "-format" not in args:
            args.extend(["-Format", "xml"])
    return args


def run_command(command: str, timeout: int = None, use_structured_output: bool = True) -> Dict:
    """
    Execute command dengan security controls dan timeout protection.
    
    Args:
        command: Command string untuk dieksekusi
        timeout: Custom timeout dalam detik (optional)
        use_structured_output: Jika True, tambahkan arg untuk output terstruktur
    
    Returns:
        Dict dengan hasil eksekusi
    """
    args = shlex.split(command)
    if not args:
        return {"ok": False, "error": "Empty command"}

    tool = args[0]

    # Whitelist tool + PATH validation
    tool_path = shutil.which(tool)
    if tool not in ALLOWED_TOOLS or tool_path is None:
        return {"ok": False, "error": "Tool not allowed or not found"}

    # Forbidden arguments (tapi izinkan output terstruktur ke stdout)
    # Periksa apakah ada attempt untuk write ke file
    for arg in args:
        arg_base = arg.split("=", 1)[0]
        if arg_base in FORBIDDEN_ARGS:
            # Izinkan -Format untuk nikto (output ke stdout)
            if tool == "nikto" and arg_base in ["-Format", "-format"]:
                continue
            return {"ok": False, "error": "Forbidden argument detected"}

    # Tambahkan structured output jika diminta
    if use_structured_output:
        args = _add_structured_output_args(args, tool)

    # Determine timeout
    if timeout is None:
        timeout = TIMEOUTS.get(tool, DEFAULT_TIMEOUT)

    try:
        # Start process dengan timeout
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
            returncode = proc.returncode
            
        except subprocess.TimeoutExpired:
            # Kill process jika timeout
            proc.kill()
            proc.wait()
            return {
                "ok": False,
                "error": "timeout",
                "timeout_seconds": timeout,
                "tool": tool
            }

        return {
            "ok": True,
            "tool": tool,
            "returncode": returncode,
            "stdout": stdout[:MAX_OUTPUT] if stdout else "",
            "stderr": stderr[:MAX_OUTPUT] if stderr else "",
            "timeout_used": timeout,
            "structured_output": use_structured_output
        }

    except FileNotFoundError as fnf:
        return {"ok": False, "error": "executable not found", "details": str(fnf)}
    except Exception as e:
        return {"ok": False, "error": "exception", "details": str(e)}