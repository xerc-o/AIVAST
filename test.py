import sys
from pathlib import Path

# Add src directory to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.ai.orchestrator import orchestrate_scan

if __name__ == "__main__":
    target = "https://faazamu.my.id/"
    print("Starting scan...")
    print(f"Target: {target}\n")
    
    result = orchestrate_scan(target)
    
    if result.get("ok"):
        print("✅ Scan completed successfully!")
        print(f"\nTool: {result['plan']['tool']}")
        print(f"Command: {result['plan']['command']}")
        print(f"\nAnalysis Risk: {result['analysis'].get('risk', 'unknown')}")
        print(f"Summary: {result['analysis'].get('summary', 'N/A')}")
        
        # Print findings jika ada
        if 'findings' in result['analysis']:
            print(f"\nFindings: {len(result['analysis']['findings'])} items")
        if 'issues' in result['analysis']:
            print(f"\nIssues: {len(result['analysis']['issues'])} items")
    else:
        print("❌ Scan failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        if 'details' in result:
            print(f"Details: {result['details']}")