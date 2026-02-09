
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
    
    config = {
        "api_provider": "azure",
        "model": os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "train_file": "eval/finance/data/finer_train_cutoff_5.jsonl",
        "val_file": "eval/finance/data/finer_val_cutoff_2.jsonl"
    }
    
    print(f"--- STARTING LIGHT CURATOR TEST ---")
    
    # Initialize Data Processor
    processor = DataProcessor(task_name="finer")
    
    # Load 1 sample and TRUNCATE CONTEXT to 1000 chars
    with open(config["train_file"], 'r', encoding='utf-8') as f:
        train_data = [json.loads(line) for line in f][:1]
    
    # Manually truncate to avoid model flakiness with large inputs
    train_data[0]['context'] = train_data[0]['context'][:1000]
    
    # Dummy validation data
    val_data = train_data
        
    train_processed = processor.process_task_data(train_data)
    val_processed = processor.process_task_data(val_data)
    
    # Initialize ACE
    ace = ACE(
        api_provider=config["api_provider"],
        generator_model=config["model"],
        reflector_model=config["model"],
        curator_model=config["model"],
        max_tokens=512,
        initial_playbook=None
    )
    
    # Training configuration
    training_config = {
        "curation_interval": 1, 
        "eval_interval": 1,
        "use_json_mode": False,
        "log_dir": "logs/curator_light_verification"
    }
    
    print("\nRunning offline training for 1 sample with TRUNCATED context...")
    
    try:
        results = ace.run(
            mode='offline',
            train_samples=train_processed,
            val_samples=val_processed,
            data_processor=processor,
            config=training_config
        )
        
        print("\n--- FINAL VERIFICATION ---")
        print(f"Playbook Length: {len(ace.playbook)} chars")
        
        # Headers-only length is roughly 196
        if len(ace.playbook.strip()) > 200:
            print("✅ SUCCESS: The Curator has successfully updated the playbook with new insights!")
            print("\nGenerated Playbook Content:")
            print("-" * 40)
            print(ace.playbook)
            print("-" * 40)
        else:
            print("❌ FAILURE: Playbook is still empty/headers-only.")
            
    except Exception as e:
        print(f"❌ ERROR: Test failed: {e}")

if __name__ == "__main__":
    main()
