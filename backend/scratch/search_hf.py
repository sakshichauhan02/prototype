import os

workspace_dir = r"c:\Users\saksh\Downloads\prototype\prototype"
search_term = "huggingface"

print(f"Searching for '{search_term}'...")
for root, dirs, files in os.walk(workspace_dir):
    if "venv" in root or ".git" in root or "node_modules" in root or ".next" in root:
        continue
    for file in files:
        if file.endswith((".py", ".ts", ".tsx", ".json", ".md")):
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    if search_term in content.lower():
                        print(f"Found in {file_path}")
            except Exception as e:
                pass
