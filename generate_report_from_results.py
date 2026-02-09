import os
import sys
import json
import matplotlib.pyplot as plt
from pathlib import Path
from collections import defaultdict
import re

# Pricing (same as demo)
PRICING = {
    "gpt-5-mini": {"input": 0.25, "output": 2.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
}

def get_model_price(model_name):
    for key in PRICING:
        if key in model_name.lower():
            return PRICING[key]
    return PRICING["gpt-4o-mini"]

def calculate_cost(token_stats, model_name):
    pricing = get_model_price(model_name)
    input_cost = (token_stats.get("prompt_tokens", 0) / 1_000_000) * pricing["input"]
    output_cost = (token_stats.get("completion_tokens", 0) / 1_000_000) * pricing["output"]
    return {
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost
    }

def create_viz(agent_stats, output_dir):
    agents = list(agent_stats.keys())
    prompt_tokens = [agent_stats[a]["prompt_tokens"] for a in agents]
    completion_tokens = [agent_stats[a]["completion_tokens"] for a in agents]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    x = range(len(agents))
    width = 0.35
    ax1.bar([i - width/2 for i in x], prompt_tokens, width, label='Prompt Tokens', color='skyblue')
    ax1.bar([i + width/2 for i in x], completion_tokens, width, label='Completion Tokens', color='lightcoral')
    ax1.set_xticks(x)
    ax1.set_xticklabels(agents)
    ax1.set_title("Token Usage by Agent")
    ax1.legend()
    
    total_tokens = [prompt_tokens[i] + completion_tokens[i] for i in range(len(agents))]
    ax2.pie(total_tokens, labels=agents, autopct='%1.1f%%', startangle=90)
    ax2.set_title("Total Token Distribution")
    
    plt.tight_layout()
    viz_path = output_dir / "token_usage_visualization.png"
    plt.savefig(viz_path)
    print(f"📊 Visualization saved to {viz_path}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_report_from_results.py <results_dir>")
        return

    results_dir = Path(sys.argv[1])
    logs_dir = results_dir / "detailed_llm_logs"
    
    output_dir = Path("logs/live_demo_manual")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating report from {logs_dir}...")
    
    agent_stats = defaultdict(lambda: {"prompt_tokens": 0, "completion_tokens": 0, "calls": 0})
    model_name = "gpt-5-mini" # Default
    
    for log_file in logs_dir.glob("*.json"):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            role = data.get("role", "unknown")
            pt = data.get("prompt_num_tokens", 0)
            ct = data.get("response_num_tokens", 0)
            model_name = data.get("model", model_name)
            
            agent_stats[role]["prompt_tokens"] += pt
            agent_stats[role]["completion_tokens"] += ct
            agent_stats[role]["calls"] += 1
        except Exception as e:
            pass # Skip problematic files/folders
            
    # Calculate totals
    total_prompt = sum(s["prompt_tokens"] for s in agent_stats.values())
    total_completion = sum(s["completion_tokens"] for s in agent_stats.values())
    total_tokens = total_prompt + total_completion
    cost = calculate_cost({"prompt_tokens": total_prompt, "completion_tokens": total_completion}, model_name)
    
    # Copy Playbook
    playbook_content = ""
    playbook_dir = results_dir / "intermediate_playbooks"
    # Find latest playbook
    playbooks = list(playbook_dir.glob("*.txt"))
    if playbooks:
        latest = max(playbooks, key=os.path.getmtime)
        with open(latest, 'r', encoding='utf-8') as f:
            playbook_content = f.read()
            
    with open(output_dir / "final_playbook.txt", "w", encoding='utf-8') as f:
        f.write(playbook_content)
        
    print(f"✅ Report Generated:")
    print(f"Total Tokens: {total_tokens}")
    print(f"Cost: ${cost['total_cost']:.4f}")
    
    # JSON Report
    report = {
        "cost": cost,
        "token_usage": dict(agent_stats),
        "total_tokens": total_tokens
    }
    with open(output_dir / "report.json", "w") as f:
        json.dump(report, f, indent=2)
        
    create_viz(agent_stats, output_dir)

if __name__ == "__main__":
    main()
