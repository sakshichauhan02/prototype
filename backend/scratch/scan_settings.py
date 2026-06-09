import sys

# Force UTF-8 encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def scan_file():
    filepath = r"c:\Users\saksh\Downloads\prototype\prototype\backend\app\services\agent_service.py"
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print("--- Occurrences of 'settings' in agent_service.py ---")
    for idx, line in enumerate(lines):
        line_num = idx + 1
        if "settings" in line:
            print(f"Line {line_num}: {line.strip()}")

if __name__ == "__main__":
    scan_file()
