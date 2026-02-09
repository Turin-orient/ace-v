
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict

# Add project root to path
sys.path.append(os.getcwd())

from ace.ace import ACE
from eval.finance.data_processor import DataProcessor
from playbook_utils import get_playbook_stats

# Azure OpenAI Pricing
PRICING = {
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
}

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    load_dotenv()
    print_section("ACE LEARNING VERIFICATION TEST")
    
    # 1. Load Existing Playbook
    playbook_path = Path("logs/live_demo_manual/final_playbook.txt")
    if not playbook_path.exists():
        print(f"❌ Playbook not found at {playbook_path}")
        return

    with open(playbook_path, "r", encoding="utf-8") as f:
        initial_playbook = f.read()

    print(f"✅ Loaded Initial Playbook ({len(initial_playbook)} chars)")
    
    # Get initial stats
    initial_stats = get_playbook_stats(initial_playbook)
    print("\nInitial Stats:")
    print(f"  Total Bullets: {initial_stats['total_bullets']}")
    print(f"  High Performing: {initial_stats['high_performing']}")
    print(f"  Unused: {initial_stats['unused']}")
    
    # 2. Load New Data (Samples 6-8)
    data_file = "eval/finance/data/finer_train_batched_1000_samples.jsonl"
    processor = DataProcessor(task_name="finer")
    
    # Skip first 5 samples used in demo, take next 3
    start_idx = 5
    num_samples = 3
    
    with open(data_file, 'r', encoding='utf-8') as f:
        all_lines = f.readlines()
        
    raw_data = [json.loads(line) for line in all_lines[start_idx:start_idx+num_samples]]
    processed_data = processor.process_task_data(raw_data)
    
    # Truncate context
    for task in processed_data:
        if len(task['context']) > 2000:
            task['context'] = task['context'][:2000] + "..."
            
    print(f"\n✅ Loaded {len(processed_data)} NEW samples (Indices {start_idx}-{start_idx+num_samples-1})")

    # 3. Running ACE
    ace = ACE(
        api_provider="azure",
        generator_model=os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        reflector_model=os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        curator_model=os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        max_tokens=5000,
        initial_playbook=initial_playbook 
    )

    training_config = {
        "curation_interval": 1,
        "eval_interval": num_samples,
        "use_json_mode": False,
        "log_dir": "logs/verify_learning",
        "sleep_between_steps": 10
    }
    
    print("\n🚀 Starting Run...")
    results = ace.run(
        mode='offline',
        train_samples=processed_data,
        val_samples=[],
        data_processor=processor,
        config=training_config
    )
    
    # 4. Compare Stats
    final_playbook = ace.playbook
    final_stats = get_playbook_stats(final_playbook)
    
    print_section("VERIFICATION RESULTS")
    print(f"Initial Total Bullets: {initial_stats['total_bullets']}")
    print(f"Final Total Bullets:   {final_stats['total_bullets']}")
    print(f"Delta: {final_stats['total_bullets'] - initial_stats['total_bullets']} new bullets added")
    
    print("\nUsage Stats Changes:")
    # We can't map 1-to-1 easily without parsing ids, but we can check totals
    # A better check is to see if any bullet has helpful > 0 that was 0 before
    
    # Simple check: Count bullets with helpful > 0
    init_helpful_count = sum(1 for section in initial_stats['by_section'].values() for _ in range(section['helpful'])) 
    # Wait, 'helpful' in stats is sum of counts. 
    # Let's count non-zero bullets manually
    def count_helpful_bullets(text):
        count = 0
        for line in text.split('\n'):
            if "helpful=" in line:
                try:
                    val = int(line.split("helpful=")[1].split()[0])
                    if val > 0: count += 1
                except: pass
        return count

    init_helpful_bullets = count_helpful_bullets(initial_playbook)
    final_helpful_bullets = count_helpful_bullets(final_playbook)
    
    print(f"Bullets with helpful > 0 (Before): {init_helpful_bullets}")
    print(f"Bullets with helpful > 0 (After):  {final_helpful_bullets}")
    
    if final_helpful_bullets > init_helpful_bullets:
        print("\n✅ SUCCESS: 'helpful' counters increased, proving the reinforcement loop works!")
    elif final_stats['total_bullets'] > initial_stats['total_bullets']:
        print("\n✅ SUCCESS: New bullets added, proving the curator loop works!")
    else:
        print("\n⚠️ WARNING: No obvious changes detected. Check logs.")

if __name__ == "__main__":
    main()
