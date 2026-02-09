import pandas as pd
import json
import glob
import re
import os

files = glob.glob('logs/phase3_batch_run/detailed_llm_logs/*.json')
sample_groups = {}

for f in files:
    filename = os.path.basename(f)
    match = re.search(r's_(\d+)_', filename)
    if not match: 
        continue
    sample_id = int(match.group(1))
    if sample_id not in sample_groups:
        sample_groups[sample_id] = {'total_input': 0, 'total_output': 0, 'initial_correct': False}
    try:
        with open(f, 'r', encoding='utf-8') as jf:
            jdata = json.load(jf)
            sample_groups[sample_id]['total_input'] += jdata.get('prompt_num_tokens', 0)
            sample_groups[sample_id]['total_output'] += jdata.get('response_num_tokens', 0)
        if 'reflect_on_correct' in filename:
            sample_groups[sample_id]['initial_correct'] = True
    except:
        pass

total_in = sum(g['total_input'] for g in sample_groups.values())
total_out = sum(g['total_output'] for g in sample_groups.values())
cost = (total_in * 0.25 / 1_000_000) + (total_out * 2.00 / 1_000_000)
correct_count = sum(1 for g in sample_groups.values() if g['initial_correct'])
accuracy = correct_count / len(sample_groups) * 100 if sample_groups else 0

print(f'Total Samples Processed: {len(sample_groups)}')
print(f'Sample Range: {min(sample_groups.keys())}-{max(sample_groups.keys())}')
print(f'Total Input Tokens: {total_in:,}')
print(f'Total Output Tokens: {total_out:,}')
print(f'Total Cost: ${cost:.4f}')
print(f'Initial Accuracy: {correct_count}/{len(sample_groups)} ({accuracy:.1f}%)')
