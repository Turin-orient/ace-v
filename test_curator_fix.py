
import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.getcwd())

from ace.ace import ACE
from eval.finance.data_processor import DataProcessor

def main():
    load_dotenv()
    
    # Configuration for a quick test
    config = {
        "api_provider": "azure",
        "model": os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "train_file": "eval/finance/data/finer_train_cutoff_5.jsonl",
        "val_file": "eval/finance/data/finer_val_cutoff_2.jsonl"
    }
    
    print(f"--- STARTING CURATOR FIX TEST ---")
    print(f"Model: {config['model']}")
    
    # Initialize Data Processor
    processor = DataProcessor(task_name="finer")
    
    # Load limited data
    with open(config["train_file"], 'r', encoding='utf-8') as f:
        train_data = [json.loads(line) for line in f][:2] # Only first 2
    
    with open(config["val_file"], 'r', encoding='utf-8') as f:
        val_data = [json.loads(line) for line in f][:1] # Only first 1
        
    train_processed = processor.process_task_data(train_data)
    val_processed = processor.process_task_data(val_data)
    
    # Initialize ACE
    ace = ACE(
        api_provider=config["api_provider"],
        generator_model=config["model"],
        reflector_model=config["model"],
        curator_model=config["model"],
        max_tokens=1000,
        initial_playbook=None
    )
    
    # Training configuration
    training_config = {
        "curation_interval": 1, 
        "eval_interval": 2,
        "use_json_mode": False,
        "log_dir": "logs/curator_fix_verification"
    }
    
    print("\nRunning offline training for 2 samples...")
    print("This will trigger a curator call after each sample.")
    
    try:
        results = ace.run(
            mode='offline',
            train_samples=train_processed,
            val_samples=val_processed,
            data_processor=processor,
            config=training_config
        )
        
        print("\n--- RESULTS ---")
        print(f"Final Playbook Length: {len(ace.playbook)} chars")
        
        # Check if playbook is not empty (contains more than just headers)
        headers_only_length = 196 # Approximated from previous logs
        if len(ace.playbook.strip()) > headers_only_length:
            print("✅ SUCCESS: Playbook is NO LONGER EMPTY!")
            print("\nPlaybook Sample:")
            print(ace.playbook[:500])
        else:
            print("❌ FAILURE: Playbook is still empty or contains only headers.")
            
    except Exception as e:
        print(f"❌ ERROR: Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
