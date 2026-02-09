import json
import re
from pathlib import Path

import glob

# Paths
# Paths
search_pattern = "results/ace_run_20260203_143224_default_offline/detailed_llm_logs/generator_train_e_1_s_5_post_curate_*.json"
output_file = "logs/live_demo_manual/final_playbook.txt"
report_file = "logs/live_demo_manual/report.json"

files = glob.glob(search_pattern)
if not files:
    print(f"❌ No file found matching: {search_pattern}")
    exit(1)

log_file = files[0]
print(f"Reading {log_file}...")
with open(log_file, "r", encoding="utf-8") as f:
    data = json.load(f)

prompt = data["prompt"]

# Extract Playbook
# Structure is **Playbook:** ... **Reflection:**
match = re.search(r"\*\*Playbook:\*\*(.*?)\*\*Reflection:\*\*", prompt, re.DOTALL)
if not match:
    # Fallback to Question if Reflection is missing/different
    match = re.search(r"\*\*Playbook:\*\*(.*?)\*\*Question:\*\*", prompt, re.DOTALL)

if match:
    playbook_content = match.group(1).strip()
    print(f"✅ Found playbook content ({len(playbook_content)} chars)")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(playbook_content)
        
    # Update report
    with open(report_file, "r") as f:
        report = json.load(f)
    report["playbook_length"] = len(playbook_content)
    with open(report_file, "w") as f:
        json.dump(report, f, indent=2)
else:
    print("❌ Could not extract playbook from prompt!")
