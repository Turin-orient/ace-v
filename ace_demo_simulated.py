"""
ACE Framework - Simulated Demo (Realistic Metrics)
==================================================

This script simulates a complete ACE run with realistic token usage,
costs, and metrics based on typical patterns observed in actual runs.
Use this to visualize the expected output while Azure API issues are resolved.
"""

import os
import sys
import json
import time
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

# Azure OpenAI Pricing (per 1M tokens)
PRICING = {
    "gpt-5-mini": {"input": 0.15, "output": 0.60},
}

def create_simulated_metrics():
    """Create realistic metrics based on typical ACE runs"""
    # Simulated token usage per agent (5 training samples)
    agent_stats = {
        "generator": {
            "calls": 10,  # Initial + post-curate for 5 samples
            "prompt_tokens": 8500,  # ~850 per call (playbook + context)
            "completion_tokens": 4200  # ~420 per call (answer generation)
        },
        "reflector": {
            "calls": 5,  # One per training sample
            "prompt_tokens": 6800,  # ~1360 per call (context + answer + target)
            "completion_tokens": 2100  # ~420 per call (reflection)
        },
        "curator": {
            "calls": 5,  # One per curation interval
            "prompt_tokens": 12500,  # ~2500 per call (playbook + reflection + stats)
            "completion_tokens": 1500  # ~300 per call (operations JSON)
        }
    }
    
    return agent_stats

def calculate_cost(agent_stats, model_name):
    """Calculate cost from agent statistics"""
    total_prompt = sum(s["prompt_tokens"] for s in agent_stats.values())
    total_completion = sum(s["completion_tokens"] for s in agent_stats.values())
    
    pricing = PRICING.get(model_name, PRICING["gpt-5-mini"])
    
    input_cost = (total_prompt / 1_000_000) * pricing["input"]
    output_cost = (total_completion / 1_000_000) * pricing["output"]
    
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
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Bar chart
    x = range(len(agents))
    width = 0.35
    
    ax1.bar([i - width/2 for i in x], prompt_tokens, width, label='Prompt Tokens', color='skyblue')
    ax1.bar([i + width/2 for i in x], completion_tokens, width, label='Completion Tokens', color='lightcoral')
    
    ax1.set_xlabel('Agent', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Token Count', fontsize=12, fontweight='bold')
    ax1.set_title('Token Usage by Agent', fontsize=14, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(agents, fontsize=10)
    ax1.legend(fontsize=10)
    ax1.grid(axis='y', alpha=0.3)
    
    # Pie chart
    total_tokens = [prompt_tokens[i] + completion_tokens[i] for i in range(len(agents))]
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    explode = (0.05, 0, 0)
    
    ax2.pie(total_tokens, labels=agents, autopct='%1.1f%%', colors=colors, startangle=90, explode=explode)
    ax2.set_title('Total Token Distribution by Agent', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    viz_path = output_dir / "token_usage_visualization.png"
    plt.savefig(viz_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return viz_path

def create_simulated_playbook():
    """Create a realistic playbook following ace_context_guide.md principles"""
    return """# FINANCIAL NAMED ENTITY RECOGNITION - ACE PLAYBOOK

## STRATEGIES AND INSIGHTS
[ctx-00001] helpful=3 harmful=0 :: When analyzing financial text, prioritize entity boundaries by looking for capitalization patterns and context clues like "Inc.", "LLC", or "Corporation" that indicate organization names.

[ctx-00002] helpful=2 harmful=0 :: For transaction-related entities (SaleOfStock, PurchaseOfStock), the action verb immediately preceding the stock symbol is the key indicator. Example: "sold 100 shares" → SaleOfStock, "bought 50 shares" → PurchaseOfStock.

[ctx-00003] helpful=4 harmful=0 :: Person names in financial contexts are often preceded by titles (CEO, CFO, Director) or possessive pronouns. Use these as strong signals for PERSON entities.

## FORMULAS AND CALCULATIONS
[ctx-00004] helpful=2 harmful=1 :: Entity span calculation: start_index = position of first character, end_index = position after last character. Double-check that the span doesn't include trailing punctuation.

## COMMON MISTAKES TO AVOID
[ctx-00005] helpful=3 harmful=0 :: Do NOT classify stock symbols (e.g., "AAPL", "MSFT") as ORGANIZATION entities. They should be part of transaction entities like SaleOfStock or PurchaseOfStock.

[ctx-00006] helpful=2 harmful=0 :: Avoid including articles ("the", "a") or prepositions in entity spans. Entity boundaries should be tight around the core noun phrase.

[ctx-00007] helpful=1 harmful=2 :: When confused between ORGANIZATION and PRODUCT entities, remember: if it can be bought/sold as a discrete item, it's a PRODUCT. If it's a business entity, it's ORGANIZATION.

## PROBLEM-SOLVING HEURISTICS
[ctx-00008] helpful=3 harmful=0 :: Delta Strategy: If the model incorrectly identifies a transaction type, check the verb tense and direction. "Acquired" and "purchased" → BUY. "Sold" and "disposed" → SELL.

[ctx-00009] helpful=2 harmful=0 :: For ambiguous entity types, use the sentence context window. Look at the surrounding 5-10 words to determine the semantic role of the entity.

## CONTEXT CLUES AND INDICATORS
[ctx-00010] helpful=4 harmful=0 :: Financial reporting language patterns: "disclosed that", "announced", "filed with the SEC" often introduce important named entities in the subsequent clause.

[ctx-00011] helpful=1 harmful=0 :: Numeric entities adjacent to stock symbols usually indicate share quantities or prices. These should NOT be labeled independently but as part of the transaction context.
"""

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    print("\n" + "#"*80)
    print(" ACE FRAMEWORK - COMPREHENSIVE DEMO (SIMULATED)")
    print("#"*80)
    print("\n  NOTE: This is a simulated run with realistic metrics.")
    print("  Azure API authentication issues prevented a live run.\n")
    
    # Configuration
    print_section("1. CONFIGURATION")
    
    config = {
        "api_provider": "azure",
        "model": "gpt-5-mini",
        "num_samples": 5,
        "val_samples": 2
    }
    
    print(f"  API Provider: {config['api_provider']}")
    print(f"  Model: {config['model']}")
    print(f"  Training samples: {config['num_samples']}")
    print(f"  Validation samples: {config['val_samples']}")
    
    # Simulate training
    print_section("2. SIMULATED TRAINING EXECUTION")
    
    print("\n  ⏳ Running ACE training loop...")
    time.sleep(1)
    print("  ✓ Epoch 1/1 completed")
    print("  ✓ Generator: 10 calls (initial + post-curate)")
    print("  ✓ Reflector: 5 calls")
    print("  ✓ Curator: 5 calls")
    print("  ✓ Validation: 2 samples evaluated")
    
    # Get metrics
    agent_stats = create_simulated_metrics()
    
    # Calculate totals
    total_prompt_tokens = sum(s["prompt_tokens"] for s in agent_stats.values())
    total_completion_tokens = sum(s["completion_tokens"] for s in agent_stats.values())
    total_tokens = total_prompt_tokens + total_completion_tokens
    
    # Calculate cost
    cost_estimate = calculate_cost(agent_stats, config["model"])
    
    # Display token usage
    print_section("3. TOKEN USAGE & COST ANALYSIS")
    
    print(f"\n  Token Usage Summary:")
    print(f"  {'Agent':<15} {'Calls':<8} {'Prompt':<12} {'Completion':<12} {'Total':<12}")
    print(f"  {'-'*60}")
    
    for agent, stats in sorted(agent_stats.items()):
        total = stats["prompt_tokens"] + stats["completion_tokens"]
        print(f"  {agent:<15} {stats['calls']:<8} {stats['prompt_tokens']:<12,} {stats['completion_tokens']:<12,} {total:<12,}")
    
    print(f"  {'-'*60}")
    print(f"  {'TOTAL':<15} {sum(s['calls'] for s in agent_stats.values()):<8} {total_prompt_tokens:<12,} {total_completion_tokens:<12,} {total_tokens:<12,}")
    
    print(f"\n  💰 Cost Estimate (Model: {config['model']}):")
    print(f"     Input tokens:  ${cost_estimate['input_cost']:.4f}")
    print(f"     Output tokens: ${cost_estimate['output_cost']:.4f}")
    print(f"     Total cost:    ${cost_estimate['total_cost']:.4f}")
    
    # Create visualization
    output_dir = Path("logs/simulated_demo")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    viz_path = create_token_visualization(agent_stats, output_dir)
    print(f"\n  📊 Visualization saved to {viz_path}")
    
    # Display playbook
    print_section("4. FINAL PLAYBOOK")
    
    playbook = create_simulated_playbook()
    print("\n" + playbook)
    
    playbook_path = output_dir / "final_playbook.txt"
    with open(playbook_path, 'w', encoding='utf-8') as f:
        f.write(playbook)
    print(f"\n  ✓ Playbook saved to {playbook_path}")
    
    # Display metrics
    print_section("5. RESULTS & METRICS")
    
    simulated_accuracy = 0.65  # Realistic accuracy for 5 training samples
    
    print(f"\n  🎯 Exact Match Accuracy: {simulated_accuracy:.2%}")
    print(f"  ⏱️  Execution Time: ~45 seconds (estimated)")
    print(f"  📝 Playbook Bullets: 11")
    print(f"  🔄 Curation Operations: 11 ADD operations")
    
    # Save comprehensive report
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "mode": "simulated",
        "configuration": config,
        "token_usage": {
            "by_agent": agent_stats,
            "total_prompt_tokens": total_prompt_tokens,
            "total_completion_tokens": total_completion_tokens,
            "total_tokens": total_tokens
        },
        "cost_estimate": cost_estimate,
        "accuracy": simulated_accuracy,
        "playbook_length": len(playbook),
        "playbook_bullets": 11
    }
    
    report_path = output_dir / "comprehensive_report.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n  ✓ Comprehensive report saved to {report_path}")
    
    print_section("6. SUMMARY")
    
    print(f"\n  ✅ Simulated demo completed successfully!")
    print(f"  📊 Total API calls: {sum(s['calls'] for s in agent_stats.values())}")
    print(f"  🎯 Total tokens used: {total_tokens:,}")
    print(f"  💰 Estimated cost: ${cost_estimate['total_cost']:.4f}")
    print(f"  📝 Playbook bullets: 11")
    print(f"  ✨ Playbook follows ACE Context Engineering principles:")
    print(f"      - Unique IDs ([ctx-XXXXX])")
    print(f"      - Helpful/Harmful counters")
    print(f"      - Delta-focused insights")
    print(f"      - Structured by section")
    
    print("\n" + "="*80)
    print(" 💡 To run with live Azure API, resolve authentication issues and")
    print("    run: ace_demo_comprehensive.py")
    print("="*80 + "\n")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
