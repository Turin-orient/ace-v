"""
Extract playbook from verification run (newest run)
"""
import json
import re
from pathlib import Path
import glob

# Find the latest generator log file from verification run
search_pattern = "results/ace_run_20260203_155412_default_offline/detailed_llm_logs/generator_train_e_1_s_3_post_curate_*.json"
log_files = glob.glob(search_pattern)

if not log_files:
    print(f"❌ No log files found matching pattern: {search_pattern}")
    exit(1)

latest_log = sorted(log_files)[-1]
print(f"Reading {latest_log}...")

with open(latest_log, 'r', encoding='utf-8') as f:
    data = json.load(f)

prompt = data.get('prompt', '')

# Extract playbook content using regex
match = re.search(r"\*\*Playbook:\*\*(.*?)\*\*Reflection:\*\*", prompt, re.DOTALL)

if not match:
    # Fallback to Question if Reflection is missing/different
    match = re.search(r"\*\*Playbook:\*\*(.*?)\*\*Question:\*\*", prompt, re.DOTALL)

if match:
    playbook_content = match.group(1).strip()
    print(f"✅ Found playbook content ({len(playbook_content)} chars)")
    
    # Save to file
    output_file = "logs/verify_learning_playbook.txt"
    Path("logs").mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(playbook_content)
    
    print(f"✅ Saved to: {output_file}")
else:
    print("❌ Could not extract playbook content")
