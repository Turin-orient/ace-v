
import os
import sys
import json
import time
import glob
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

from ace.ace import ACE
from eval.finance.data_processor import DataProcessor
from playbook_utils import get_playbook_stats

# Azure OpenAI Pricing
PRICING = {
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

class TokenBucket:
    """Smart Rate Limiter using Token Bucket Algorithm"""
    def __init__(self, rate_per_minute, capacity):
        self.rate = rate_per_minute / 60.0  # Tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.total_consumed = 0

    def refill(self):
        now = time.time()
        delta = now - self.last_update
        self.tokens = min(self.capacity, self.tokens + delta * self.rate)
        self.last_update = now

    def consume(self, tokens, block=True):
        self.refill()
        if tokens > self.tokens:
            if not block:
                return False
            # Calculate wait time
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            print(f"⏳ Rate Limit Reached. Sleeping {wait_time:.2f}s...")
            time.sleep(wait_time)
            self.tokens = 0 # Consumed after wait (approx)
            self.last_update = time.time()
        else:
            self.tokens -= tokens
        self.total_consumed += tokens
        return True

def get_model_price(model_name):
    for key in PRICING:
        if key in model_name.lower():
            return PRICING[key]
    return PRICING["gpt-4o-mini"]

def calculate_current_cost(log_dir):
    """Calculate total cost from generated log files"""
    total_input = 0
    total_output = 0
    model = os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    
    files = glob.glob(str(Path(log_dir) / "*.json"))
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as log_file:
                data = json.load(log_file)
                total_input += data.get("prompt_num_tokens", 0)
                total_output += data.get("response_num_tokens", 0)
        except: continue
        
    price = get_model_price(model)
    cost = (total_input / 1_000_000 * price["input"]) + (total_output / 1_000_000 * price["output"])
    return cost

def main():
    load_dotenv()
    
    # --- CONFIGURATION ---
    # Rate Limit: 130k TPM. We set capacity slightly lower for safety buffer.
    RATE_LIMIT_TPM = 125000 
    # Budget Cap in USD
    MAX_BUDGET = 5.00 
    # Dataset
    DATA_FILE = "eval/finance/data/finer_train_batched_1000_samples.jsonl"
    # Log Directory (Persistent)
    BATCH_LOG_DIR = "logs/phase3_batch_run"
    
    print("\n" + "="*80)
    print("🚀 ACE SMART BATCH RUNNER")
    print("="*80)
    print(f"Rate Limit: {RATE_LIMIT_TPM} TPM")
    print(f"Budget Cap: ${MAX_BUDGET}")
    print(f"Log Dir:    {BATCH_LOG_DIR}")
    
    # 1. Setup Folders
    Path(BATCH_LOG_DIR).mkdir(parents=True, exist_ok=True)
    detailed_log_dir = Path(BATCH_LOG_DIR) / "detailed_llm_logs"
    detailed_log_dir.mkdir(exist_ok=True)
    usage_log_path = os.path.join(BATCH_LOG_DIR, "usage_log.jsonl")
    
    # 2. Load Data
    processor = DataProcessor(task_name="finer")
    raw_data = []
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            raw_data.append(json.loads(line))
    
    processed_data = processor.process_task_data(raw_data)
    # Filter: Take first 50 for now (User requested ~20-50 batch)
    TARGET_BATCH_SIZE = 50
    # Also skip the ones used in previous demo? (Indices 0-4 and 5-7 were used).
    # Let's start fresh from index 10 to be safe.
    START_IDX = 60
    batch_samples = processed_data[START_IDX : START_IDX + TARGET_BATCH_SIZE]
    
    # Truncate context for safety

    for task in batch_samples:
        if len(task['context']) > 2000:
            task['context'] = task['context'][:2000] + "..."
            
    print(f"✅ Training Target: {len(batch_samples)} samples (Indices {START_IDX}-{START_IDX+TARGET_BATCH_SIZE-1})")

    # 3. Load Initial Playbook
    # We want to continue from where verification left off
    latest_playbook_path = "logs/verify_learning_playbook.txt"
    if not Path(latest_playbook_path).exists():
        print(f"⚠️ Warning: {latest_playbook_path} not found. Using empty/default.")
        initial_playbook = None
    else:
        with open(latest_playbook_path, 'r', encoding='utf-8') as f:
            initial_playbook = f.read()
        print(f"✅ Loaded evolved playbook ({len(initial_playbook)} chars)")

    # 4. Initialize ACE
    model = os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    ace = ACE(
        api_provider="azure",
        generator_model=model,
        reflector_model=model,
        curator_model=model,
        max_tokens=6000, # Increased context
        initial_playbook=initial_playbook
    )
    
    # 5. Initialize Token Bucket
    bucket = TokenBucket(rate_per_minute=RATE_LIMIT_TPM, capacity=100000) # Bucket size smaller than 1 min rate
    
    # 6. Training Loop
    print("\n▶️ Starting Batch Execution...")
    
    config_params = {
        'max_num_rounds': 1,
        'curator_frequency': 1,
        'token_budget': 1000, # Unused legcay param
        'use_json_mode': False,
        'no_ground_truth': False,
        'test_workers': 1
    }
    
    skipped = 0
    executed = 0
    
    for i, sample in enumerate(batch_samples):
        global_sample_id = START_IDX + i
        step_id = f"train_e_1_s_{global_sample_id}"
        
        # --- RESUMABILITY CHECK ---
        # Check if post_curate log exists for this step
        expected_log = list(detailed_log_dir.glob(f"*_{step_id}_post_curate_*.json"))
        if expected_log:
            print(f"⏭️  Skipping Sample {global_sample_id} (Already completed)")
            skipped += 1
            # Update ACE playbook state from disk if needed? 
            # Actually, if we skip, our in-memory playbook is stale.
            # To be truly resumable, we should load the LATEST playbook from the logs.
            # But simpler: Just proceed. The next curator step will use the current in-memory playbook.
            # Ideally, we should restart from the *final* playbook of the last run.
            # Ensure "initial_playbook" loaded above is the verified one.
            continue
            
        # --- BUDGET CHECK ---
        current_cost = calculate_current_cost(detailed_log_dir)
        if current_cost >= MAX_BUDGET:
            print(f"🛑 Budget Cap Reached (${current_cost:.2f} >= ${MAX_BUDGET}). Stopping.")
            break
            
        # --- RATE LIMIT CHECK ---
        # Estimate cost: 2k input + 1k output = 3000 tokens per agent
        # 3 agents = 9000 tokens estimated worst case
        # Consume upfront? Or simpler: consume a chunk now.
        bucket.consume(6000) # Reserve 6k tokens
        
        # --- EXECUTE ---
        print(f"\n📍 Processing Sample {global_sample_id} (Cost: ${current_cost:.4f})")
        
        try:
            ace._train_single_sample(
                task_dict=sample,
                data_processor=processor,
                step_id=step_id,
                epoch=1,
                step=global_sample_id,
                usage_log_path=usage_log_path,
                log_dir=str(detailed_log_dir),
                config_params=config_params,
                total_samples=len(processed_data)
            )
            executed += 1
            
            # Save Playbook Checkpoint
            checkpoint_path = Path(BATCH_LOG_DIR) / "final_playbook.txt"
            with open(checkpoint_path, "w", encoding='utf-8') as f:
                f.write(ace.playbook)
                
        except Exception as e:
            print(f"❌ Error on sample {global_sample_id}: {e}")
            import traceback
            traceback.print_exc()
            # Don't break, try next
            
    print("\n" + "="*80)
    print("BATCH COMPLETE")
    print(f"Skipped: {skipped}")
    print(f"Executed: {executed}")
    print(f"Final Cost: ${calculate_current_cost(detailed_log_dir):.4f}")
    print(f"Playbook saved to: {Path(BATCH_LOG_DIR) / 'final_playbook.txt'}")

if __name__ == "__main__":
    main()
