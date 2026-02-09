"""
ACE Framework - Live Demo Script (With Rate Limiting)
=====================================================

This script runs ACE on a small dataset using the live Azure API.
It includes rate limiting to respect the 130k TPM limit.
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend

# Add project root to path
sys.path.append(os.getcwd())

from ace.ace import ACE
from eval.finance.data_processor import DataProcessor

# Azure OpenAI Pricing
PRICING = {
    "gpt-5-mini": {"input": 0.25, "output": 2.00}, # User specified
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

def get_model_price(model_name):
    """Get pricing for a model"""
    for key in PRICING:
        if key in model_name.lower():
            return PRICING[key]
    return PRICING["gpt-4o-mini"]

def calculate_cost(token_stats, model_name):
    """Calculate estimated cost based on token usage"""
    pricing = get_model_price(model_name)
    input_cost = (token_stats.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
    output_cost = (token_stats.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost
    }

def create_token_visualization(agent_stats, output_dir):
    """Create visualization of token usage per agent"""
    if not agent_stats:
        return None
        
    agents = list(agent_stats.keys())
    prompt_tokens = [agent_stats[a]["prompt_tokens"] for a in agents]
    completion_tokens = [agent_stats[a]["completion_tokens"] for a in agents]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Bar chart
    x = range(len(agents))
    width = 0.35
    ax1.bar([i - width/2 for i in x], prompt_tokens, width, label='Prompt Tokens', color='skyblue')
    ax1.bar([i + width/2 for i in x], completion_tokens, width, label='Completion Tokens', color='lightcoral')
    ax1.set_xlabel('Agent')
    ax1.set_ylabel('Token Count')
    ax1.set_title('Token Usage by Agent')
    ax1.set_xticks(x)
    ax1.set_xticklabels(agents)
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3)
    
    # Pie chart
    total_tokens = [prompt_tokens[i] + completion_tokens[i] for i in range(len(agents))]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    ax2.pie(total_tokens, labels=agents, autopct='%1.1f%%', colors=colors[:len(agents)], startangle=90)
    ax2.set_title('Total Token Distribution by Agent')
    
    plt.tight_layout()
    viz_path = output_dir / "token_usage_visualization.png"
    plt.savefig(viz_path, dpi=150, bbox_inches='tight')
    plt.close()
    return viz_path

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    load_dotenv()
    print("\n" + "#"*80)
    print(" ACE FRAMEWORK - LIVE DEMO (Rate Limited)")
    print("#"*80)
    
    # 1. Configuration
    print_section("1. CONFIGURATION")
    num_samples = 5
    config = {
        "api_provider": "azure",
        "model": os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "train_file": "eval/finance/data/finer_train_cutoff_5.jsonl",
        "val_file": "eval/finance/data/finer_val_cutoff_2.jsonl",
        "num_samples": num_samples,
        "log_dir": "logs/live_demo"
    }
    print(f"  API Provider: {config['api_provider']}")
    print(f"  Model: {config['model']}")
    print(f"  Training samples: {num_samples}")
    print(f"  Log Directory: {config['log_dir']}")

    # 2. Load Data
    print_section("2. LOADING DATA")
    processor = DataProcessor(task_name="finer")
    with open(config["train_file"], 'r', encoding='utf-8') as f:
        train_data = [json.loads(line) for line in f][:num_samples]
    with open(config["val_file"], 'r', encoding='utf-8') as f:
        val_data = [json.loads(line) for line in f][:2]
    
    train_processed = processor.process_task_data(train_data)
    val_processed = processor.process_task_data(val_data)
    
    # 2.1 Truncate context heavily for gpt-5-mini compatibility
    print("  ⚠️ Truncating context to 2000 chars to avoid empty response issues with gpt-5-mini")
    for task in train_processed:
        if len(task['context']) > 2000:
            task['context'] = task['context'][:2000] + "..."
    for task in val_processed:
        if len(task['context']) > 2000:
            task['context'] = task['context'][:2000] + "..."
    print(f"  ✓ Loaded {len(train_processed)} training samples")
    print(f"  ✓ Loaded {len(val_processed)} validation samples")

    # 3. Initialize ACE
    print_section("3. INITIALIZING ACE SYSTEM")
    ace = ACE(
        api_provider=config["api_provider"],
        generator_model=config["model"],
        reflector_model=config["model"],
        curator_model=config["model"],
        max_tokens=5000,
        initial_playbook=None
    )
    print(f"  ✓ ACE system initialized")

    # 4. Run Training
    print_section("4. RUNNING ACE TRAINING")
    training_config = {
        "curation_interval": 1,
        "eval_interval": num_samples,
        "use_json_mode": False,
        "log_dir": config["log_dir"],
        "sleep_between_steps": 10  # 10s sleep for rate limiting
    }
    
    start_time = time.time()
    try:
        results = ace.run(
            mode='offline',
            train_samples=train_processed,
            val_samples=val_processed,
            data_processor=processor,
            config=training_config
        )
        elapsed_time = time.time() - start_time
        
        # 5. Analysis
        print_section("5. TOKEN USAGE & COST ANALYSIS")
        log_dir = Path(config["log_dir"])
        agent_stats = defaultdict(lambda: {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0})
        
        if log_dir.exists():
            for log_file in log_dir.glob("*.json"):
                try:
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_data = json.load(f)
                    role = log_data.get("role", "unknown")
                    prompt_tokens = log_data.get("prompt_num_tokens", 0)
                    response_tokens = log_data.get("response_num_tokens", 0)
                    agent_stats[role]["prompt_tokens"] += prompt_tokens
                    agent_stats[role]["completion_tokens"] += response_tokens
                    agent_stats[role]["calls"] += 1
                except: continue

        total_prompt = sum(s["prompt_tokens"] for s in agent_stats.values())
        total_completion = sum(s["completion_tokens"] for s in agent_stats.values())
        total_tokens = total_prompt + total_completion
        cost_estimate = calculate_cost({"prompt_tokens": total_prompt, "completion_tokens": total_completion}, config["model"])

        print(f"\n  Token Usage Summary:")
        print(f"  {'Agent':<15} {'Calls':<8} {'Prompt':<12} {'Completion':<12} {'Total':<12}")
        for agent, stats in sorted(agent_stats.items()):
            total = stats["prompt_tokens"] + stats["completion_tokens"]
            print(f"  {agent:<15} {stats['calls']:<8} {stats['prompt_tokens']:<12,} {stats['completion_tokens']:<12,} {total:<12,}")
        print(f"  {'TOTAL':<15} {sum(s['calls'] for s in agent_stats.values()):<8} {total_prompt:<12,} {total_completion:<12,} {total_tokens:<12,}")
        
        print(f"\n  Cost Estimate: ${cost_estimate['total_cost']:.4f}")
        
        if agent_stats:
            create_token_visualization(agent_stats, log_dir)

        # 6. Playbook
        print_section("6. FINAL PLAYBOOK")
        if ace.playbook and len(ace.playbook.strip()) > 200:
            print("\n" + ace.playbook[:500] + "...\n(truncated for display)")
            playbook_path = log_dir / "final_playbook.txt"
            with open(playbook_path, 'w', encoding='utf-8') as f:
                f.write(ace.playbook)
            print(f"  ✓ Playbook saved to {playbook_path}")
        else:
            print("  ⚠️ Playbook empty.")

        # 7. Report
        print_section("7. METRICS")
        accuracy = results.get('best_validation_accuracy', results.get('best_val_accuracy', 0.0)) # Handle varied naming
        # Check nested structure if needed
        if 'training_results' in results and 'best_validation_accuracy' in results['training_results']:
             accuracy = results['training_results']['best_validation_accuracy']

        print(f"  Exact Match Accuracy: {accuracy:.2%}")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configuration": config,
            "execution_time": elapsed_time,
            "token_usage": dict(agent_stats),
            "cost_estimate": cost_estimate,
            "accuracy": accuracy,
            "playbook_length": len(ace.playbook)
        }
        report_path = log_dir / "live_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"  ✓ Report saved to {report_path}")

        return 0

    except Exception as e:
        print_section("ERROR")
        print(f"  ❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
