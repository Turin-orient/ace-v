"""
ACE Framework - Full Pipeline Test (Phase 3)
===========================================

Test the complete ACE training loop:
- Generator: Generate answers using playbook
- Reflector: Analyze answers and tag bullets
- Curator: Update playbook based on reflections

Using cutoff dataset (5 training samples, 2 validation samples)
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ace import ACE
from eval.finance.data_processor import DataProcessor

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    print("\n" + "#"*80)
    print(" ACE FRAMEWORK - FULL PIPELINE TEST (PHASE 3)")
    print("#"*80)
    
    # Load environment
    load_dotenv()
    
    print_section("1. CONFIGURATION")
    
    config = {
        "api_provider": "azure",
        "generator_model": os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "reflector_model": os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "curator_model": os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "max_tokens": 512,
        "task_name": "finer",
        "train_file": "eval/finance/data/finer_train_cutoff_5.jsonl",
        "val_file": "eval/finance/data/finer_val_cutoff_2.jsonl"
    }
    
    for key, value in config.items():
        print(f"  {key}: {value}")
    
    # Load datasets
    print_section("2. LOADING DATASETS")
    
    # Get repository root (where this script is located)
    repo_root = Path(__file__).parent
    
    train_path = repo_root / config["train_file"]
    val_path = repo_root / config["val_file"]
    
    print(f"Training data: {train_path}")
    print(f"Validation data: {val_path}")
    
    # Load JSONL
    with open(train_path, 'r', encoding='utf-8') as f:
        train_data = [json.loads(line) for line in f]
    
    with open(val_path, 'r', encoding='utf-8') as f:
        val_data = [json.loads(line) for line in f]
    
    print(f"  Training samples: {len(train_data)}")
    print(f"  Validation samples: {len(val_data)}")
    
    # Create data processor
    print_section("3. INITIALIZING DATA PROCESSOR")
    
    processor = DataProcessor(task_name=config["task_name"])
    
    # Process data
    train_processed = processor.process_task_data(train_data)
    val_processed = processor.process_task_data(val_data)
    
    print(f"  Processed training samples: {len(train_processed)}")
    print(f"  Processed validation samples: {len(val_processed)}")
    
    # Show first sample
    print("\n  Sample data structure:")
    sample = train_processed[0]
    print(f"    Context (first 100 chars): {sample['context'][:100]}...")
    print(f"    Question (first 100 chars): {sample['question'][:100]}...")
    print(f"    Target: {sample['target'][:100]}...")
    
    # Initialize ACE
    print_section("4. INITIALIZING ACE SYSTEM")
    
    ace = ACE(
        api_provider=config["api_provider"],
        generator_model=config["generator_model"],
        reflector_model=config["reflector_model"],
        curator_model=config["curator_model"],
        max_tokens=config["max_tokens"],
        initial_playbook=None
    )
    
    print(f"  [OK] ACE system initialized")
    print(f"  Initial playbook length: {len(ace.playbook)} characters")
    print(f"  Next bullet ID counter: {ace.next_global_id}")
    
    # Run training
    print_section("5. RUNNING TRAINING LOOP")
    
    print(f"\nProcessing {len(train_processed)} training samples...")
    print("This will test: Generator -> Reflector -> Curator pipeline\n")
    
    start_time = time.time()
    
    results = {
        "samples": [],
        "playbook_evolution": [],
        "token_usage": {"total": 0, "by_agent": {"generator": 0, "reflector": 0, "curator": 0}}
    }
    
    # Custom training config
    training_config = {
        "curation_interval": 1,  # Curate after every sample for testing
        "eval_interval": len(train_processed),  # Evaluate once at the end
        "use_json_mode": False,
        "log_dir": "logs/phase3_test"
    }    
    
    try:
        # Run ACE training
        ace_results = ace.run(
            mode='offline',
            train_samples=train_processed,
            val_samples=val_processed,
            data_processor=processor,
            config=training_config
        )
        
        elapsed = time.time() - start_time
        
        print_section("6. TRAINING RESULTS")
        
        print(f"\nExecution time: {elapsed:.2f} seconds")
        print(f"Final playbook length: {len(ace.playbook)} characters")
        
        # Show playbook sample
        if ace.playbook:
            print(f"\nPlaybook preview (first 500 chars):")
            print(ace.playbook[:500])
            print("...")
        
        # Save results
        output_dir = Path("logs/phase3_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "results.json", 'w', encoding='utf-8') as f:
            json.dump(ace_results, f, indent=2, default=str)
        
        with open(output_dir / "final_playbook.txt", 'w', encoding='utf-8') as f:
            f.write(ace.playbook)
        
        print(f"\n[OK] Results saved to {output_dir}/")
        
        print_section("7. SUMMARY")
        
        print("\n[SUCCESS] Full pipeline test completed!")
        print(f"\nComponents tested:")
        print(f"  [OK] Generator - Generated {len(train_processed)} answers")
        print(f"  [OK] Reflector - Analyzed all outputs")
        print(f"  [OK] Curator - Updated playbook {training_config['curation_interval']} times")
        print(f"  [OK] Data Processor - Processed {len(train_processed) + len(val_processed)} samples")
        
        if 'best_val_accuracy' in ace_results:
            print(f"\nValidation accuracy: {ace_results['best_val_accuracy']:.2%}")
        
        return 0
        
    except Exception as e:
        print_section("ERROR")
        print(f"\n[ERROR] Training failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
