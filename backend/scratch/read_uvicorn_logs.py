import sys

# Force UTF-8 stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def search_logs():
    log_file = "uvicorn.current.err.log"
    with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    print("--- Searching for warnings in uvicorn logs ---")
    lines = content.splitlines()
    found = False
    for i, line in enumerate(lines):
        if "gemini" in line.lower() or "warning" in line.lower() or "exception" in line.lower() or "failed" in line.lower():
            # Print the line and 2 context lines around it
            start = max(0, i-2)
            end = min(len(lines), i+3)
            print(f"\nMatch at line {i+1}:")
            for j in range(start, end):
                prefix = "=> " if j == i else "   "
                print(f"{prefix}{lines[j]}")
            found = True
            
    if not found:
        print("No matching warning lines found.")

if __name__ == "__main__":
    search_logs()
