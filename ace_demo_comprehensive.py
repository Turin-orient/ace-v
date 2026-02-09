"""
ACE Framework - Comprehensive Demo Script
==========================================

This script runs ACE on a small dataset and provides:
- Token usage tracking per agent
- Cost estimation
- Visualizations of token usage
- Model logging
- Full playbook output
- Exact Match Accuracy metrics
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

# Azure OpenAI Pricing (as of 2024, update as needed)
# Prices per 1M tokens
PRICING = {
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-35-turbo": {"input": 0.50, "output": 1.50},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-5-mini": {"input": 0.15, "output": 0.60},  # Assuming similar to gpt-4o-mini
}

def get_model_price(model_name):
    """Get pricing for a model, default to gpt-4o-mini if not found"""
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
    agents = list(agent_stats.keys())
    prompt_tokens = [agent_stats[a]["prompt_tokens"] for a in agents]
    completion_tokens = [agent_stats[a]["completion_tokens"] for a in agents]
    
    # Create stacked bar chart
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
    
    # Pie chart for total distribution
    total_tokens = [prompt_tokens[i] + completion_tokens[i] for i in range(len(agents))]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    
    ax2.pie(total_tokens, labels=agents, autopct='%1.1f%%', colors=colors[:len(agents)], startangle=90)
    ax2.set_title('Total Token Distribution by Agent')
    
    plt.tight_layout()
    viz_path = output_dir / "token_usage_visualization.png"
    plt.savefig(viz_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"📊 Visualization saved to {viz_path}")
    return viz_path

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    load_dotenv()
    
    print("\n" + "#"*80)
    print(" ACE FRAMEWORK - COMPREHENSIVE DEMO")
    print("#"*80)
    
    # Configuration
    print_section("1. CONFIGURATION")
    
    num_samples = 5  # Using 5 samples for demo
    
    config = {
        "api_provider": "azure",
        "model": os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini"),
        "train_file": "eval/finance/data/finer_train_cutoff_5.jsonl",
        "val_file": "eval/finance/data/finer_val_cutoff_2.jsonl",
        "num_samples": num_samples
    }
    
    print(f"  API Provider: {config['api_provider']}")
    print(f"  Model: {config['model']}")
    print(f"  Training samples: {num_samples}")
    print(f"  Validation samples: 2")
    
    # Load data
    print_section("2. LOADING DATA")
    
    processor = DataProcessor(task_name="finer")
    
    with open(config["train_file"], 'r', encoding='utf-8') as f:
        train_data = [json.loads(line) for line in f][:num_samples]
    
    with open(config["val_file"], 'r', encoding='utf-8') as f:
        val_data = [json.loads(line) for line in f][:2]
    
    train_processed = processor.process_task_data(train_data)
    val_processed = processor.process_task_data(val_data)
    
    print(f"  ✓ Loaded {len(train_processed)} training samples")
    print(f"  ✓ Loaded {len(val_processed)} validation samples")
    
    # Initialize ACE
    print_section("3. INITIALIZING ACE SYSTEM")
    
    ace = ACE(
        api_provider=config["api_provider"],
        generator_model=config["model"],
        reflector_model=config["model"],
        curator_model=config["model"],
        max_tokens=1000,
        initial_playbook=None
    )
    
    print(f"  ✓ ACE system initialized")
    print(f"  ✓ Using model: {config['model']}")
    print(f"  ✓ Initial playbook: Empty (will be built during training)")
    
    # Training configuration
    training_config = {
        "curation_interval": 1,
        "eval_interval": num_samples,
        "use_json_mode": False,
        "log_dir": "logs/comprehensive_demo"
    }
    
    # Run training
    print_section("4. RUNNING ACE TRAINING")
    
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
        
        # Calculate token statistics from logs
        print_section("5. TOKEN USAGE & COST ANALYSIS")
        
        log_dir = Path("logs/comprehensive_demo")
        agent_stats = defaultdict(lambda: {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0})
        
        # Parse all log files
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
                except:
                    continue
        
        # Calculate totals
        total_prompt_tokens = sum(s["prompt_tokens"] for s in agent_stats.values())
        total_completion_tokens = sum(s["completion_tokens"] for s in agent_stats.values())
        total_tokens = total_prompt_tokens + total_completion_tokens
        
        # Calculate cost
        cost_estimate = calculate_cost({
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens
        }, config["model"])
        
        print(f"\n  Token Usage Summary:")
        print(f"  {'Agent':<15} {'Calls':<8} {'Prompt':<12} {'Completion':<12} {'Total':<12}")
        print(f"  {'-'*60}")
        
        for agent, stats in sorted(agent_stats.items()):
            total = stats["prompt_tokens"] + stats["completion_tokens"]
            print(f"  {agent:<15} {stats['calls']:<8} {stats['prompt_tokens']:<12,} {stats['completion_tokens']:<12,} {total:<12,}")
        
        print(f"  {'-'*60}")
        print(f"  {'TOTAL':<15} {sum(s['calls'] for s in agent_stats.values()):<8} {total_prompt_tokens:<12,} {total_completion_tokens:<12,} {total_tokens:<12,}")
        
        print(f"\n  Cost Estimate (Model: {config['model']}):")
        print(f"    Input tokens:  ${cost_estimate['input_cost']:.4f}")
        print(f"    Output tokens: ${cost_estimate['output_cost']:.4f}")
        print(f"    Total cost:    ${cost_estimate['total_cost']:.4f}")
        
        # Create visualization
        if agent_stats:
            viz_path = create_token_visualization(agent_stats, log_dir)
        
        # Display playbook
        print_section("6. FINAL PLAYBOOK")
        
        if ace.playbook and len(ace.playbook.strip()) > 200:
            print("\n" + ace.playbook)
            
            # Save playbook
            playbook_path = log_dir / "final_playbook.txt"
            with open(playbook_path, 'w', encoding='utf-8') as f:
                f.write(ace.playbook)
            print(f"\n  ✓ Playbook saved to {playbook_path}")
        else:
            print("\n  ⚠️  Playbook is empty or minimal (likely due to LLM failures)")
        
        # Display accuracy
        print_section("7. RESULTS & METRICS")
        
        print(f"\n  Execution Time: {elapsed_time:.2f} seconds")
        
        if 'best_val_accuracy' in results:
            print(f"  Exact Match Accuracy: {results['best_val_accuracy']:.2%}")
        else:
            print(f"  Exact Match Accuracy: Not available (check results)")
        
        # Save comprehensive report
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "configuration": config,
            "execution_time_seconds": elapsed_time,
            "token_usage": {
                "by_agent": dict(agent_stats),
                "total_prompt_tokens": total_prompt_tokens,
                "total_completion_tokens": total_completion_tokens,
                "total_tokens": total_tokens
            },
            "cost_estimate": cost_estimate,
            "accuracy": results.get('best_val_accuracy', 0.0),
            "playbook_length": len(ace.playbook),
            "results": results
        }
        
        report_path = log_dir / "comprehensive_report.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"\n  ✓ Comprehensive report saved to {report_path}")
        
        print_section("8. SUMMARY")
        
        print(f"\n  ✅ Demo completed successfully!")
        print(f"  📊 Total API calls: {sum(s['calls'] for s in agent_stats.values())}")
        print(f"  🎯 Total tokens used: {total_tokens:,}")
        print(f"  💰 Estimated cost: ${cost_estimate['total_cost']:.4f}")
        print(f"  📝 Playbook bullets: {ace.playbook.count('[') if ace.playbook else 0}")
        
        return 0
        
    except Exception as e:
        print_section("ERROR")
        print(f"\n  ❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
