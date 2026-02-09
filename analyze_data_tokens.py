
import json
import tiktoken
import numpy as np
from pathlib import Path

def analyze_file(filepath):
    print(f"Analyzing {filepath}...")
    enc = tiktoken.encoding_for_model("gpt-4") # Use gpt-4 encoding as proxy for gpt-5-mini
    
    lengths = []
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            try:
                data = json.loads(line)
                # Combine relevant fields to estimate context size sent to LLM
                # Typically: instruction + context + playbook (approx 2k)
                text = data.get('context', '') + " " + data.get('instruction', '')
                tokens = len(enc.encode(text))
                lengths.append(tokens)
            except Exception as e:
                print(f"Error parsing line {i}: {e}")

    if not lengths:
        print("No valid data found.")
        return

    print("\n" + "="*40)
    print("TOKEN STATISTICS (Input Context Only)")
    print("="*40)
    print(f"Total Samples: {len(lengths)}")
    print(f"Min Tokens:    {min(lengths)}")
    print(f"Max Tokens:    {max(lengths)}")
    print(f"Avg Tokens:    {sum(lengths) / len(lengths):.2f}")
    print(f"Median Tokens: {np.median(lengths):.2f}")
    print(f"95th Percentile: {np.percentile(lengths, 95):.2f}")
    print("\nDistribution:")
    print(f"< 2k tokens:   {sum(1 for x in lengths if x < 2000)} samples")
    print(f"2k - 8k tokens:{sum(1 for x in lengths if 2000 <= x < 8000)} samples")
    print(f"8k - 32k tokens:{sum(1 for x in lengths if 8000 <= x < 32000)} samples")
    print(f"> 32k tokens:  {sum(1 for x in lengths if x >= 32000)} samples")
    print("="*40)

if __name__ == "__main__":
    target_file = "eval/finance/data/finer_train_batched_1000_samples.jsonl"
    if Path(target_file).exists():
        analyze_file(target_file)
    else:
        print(f"File not found: {target_file}")
