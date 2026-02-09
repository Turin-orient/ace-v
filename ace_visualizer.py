
import os
import json
import glob
import re
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pathlib import Path

# --- CONFIG ---
LOG_DIR = r"logs/phase3_batch_run/detailed_llm_logs"
OUTPUT_IMAGE = "logs/phase3_batch_run/batch_metrics_visualization.png"

# Pricing (Azure OpenAI)
PRICING = {
    "input": 5.00 / 1_000_000,   # $5 per 1M (gpt-4o estimated) or User provided
    "output": 15.00 / 1_000_000  # $15 per 1M
}
# Note: User used gpt-5-mini pricing in batch runner: input 0.25, output 2.00
# Let's use the same pricing as ace_batch_runner.py for consistency
PRICING_BATCH_RUNNER = {
    "input": 0.25 / 1_000_000,
    "output": 2.00 / 1_000_000
}

def parse_logs(log_dir):
    data = []
    
    # Get all JSON files
    files = glob.glob(os.path.join(log_dir, "*.json"))
    
    # Group by Sample ID
    # Pattern: {agent}_train_e_1_s_{sample_id}_{step}_...
    sample_groups = {}
    
    for f in files:
        filename = os.path.basename(f)
        try:
            # Extract Sample ID using regex
            match = re.search(r"s_(\d+)_", filename)
            if not match: continue
            
            sample_id = int(match.group(1))
            if sample_id not in sample_groups:
                sample_groups[sample_id] = {
                    "files": [], 
                    "initial_correct": False, 
                    "gen_initial_prompt_tokens": 0
                }
            
            sample_groups[sample_id]["files"].append(f)
            
            # Check for Initial Correctness (Reflector log)
            if "reflect_on_correct" in filename:
                sample_groups[sample_id]["initial_correct"] = True
                
            # Capture Context Size (from Generator Initial)
            if "generator" in filename and "gen_initial" in filename:
                with open(f, 'r', encoding='utf-8') as jf:
                    jdata = json.load(jf)
                    sample_groups[sample_id]["gen_initial_prompt_tokens"] = jdata.get("prompt_num_tokens", 0)

        except Exception as e:
            print(f"Error parsing {filename}: {e}")
            
    # Calculate Metrics per Sample
    results = []
    
    for sid, group in sorted(sample_groups.items()):
        total_input = 0
        total_output = 0
        
        for f in group["files"]:
            try:
                with open(f, 'r', encoding='utf-8') as jf:
                    jdata = json.load(jf)
                    total_input += jdata.get("prompt_num_tokens", 0)
                    total_output += jdata.get("response_num_tokens", 0)
            except: pass
            
        cost = (total_input * PRICING_BATCH_RUNNER["input"]) + (total_output * PRICING_BATCH_RUNNER["output"])
        
        results.append({
            "Sample_ID": sid,
            "Total_Input_Tokens": total_input,
            "Total_Output_Tokens": total_output,
            "Cost": cost,
            "Initial_Accuracy": 1 if group["initial_correct"] else 0,
            "Context_Size": group["gen_initial_prompt_tokens"] # Approximation of Playbook + Input growth
        })
        
    return pd.DataFrame(results)

def plot_metrics(df):
    if df.empty:
        print("No data found!")
        return

    # Calculate Moving Average for Accuracy (Window = 5)
    df["Accuracy_MA"] = df["Initial_Accuracy"].rolling(window=5, min_periods=1).mean()
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('ACE Batch Run Analysis (Samples 10-59)', fontsize=16)
    
    # 1. Context Growth (Playbook Evolution)
    ax1 = axes[0, 0]
    ax1.plot(df["Sample_ID"], df["Context_Size"], marker='o', color='purple', alpha=0.6)
    ax1.set_title('Context Size (Input Tokens per Generation)', fontsize=12)
    ax1.set_xlabel('Sample ID')
    ax1.set_ylabel('Tokens')
    ax1.grid(True, linestyle='--', alpha=0.6)
    
    # 2. Total Tokens Used per Sample
    ax2 = axes[0, 1]
    ax2.bar(df["Sample_ID"], df["Total_Input_Tokens"], label="Input", alpha=0.7)
    ax2.bar(df["Sample_ID"], df["Total_Output_Tokens"], bottom=df["Total_Input_Tokens"], label="Output", alpha=0.7)
    ax2.set_title('Total Token Usage per Sample', fontsize=12)
    ax2.set_xlabel('Sample ID')
    ax2.set_ylabel('Tokens')
    ax2.legend()
    ax2.grid(True, linestyle='--', alpha=0.6)
    
    # 3. Cost per Sample
    ax3 = axes[1, 0]
    ax3.plot(df["Sample_ID"], df["Cost"], marker='s', color='green', linestyle='-')
    ax3.set_title('Cost per Sample ($USD)', fontsize=12)
    ax3.set_xlabel('Sample ID')
    ax3.set_ylabel('Cost ($)')
    ax3.grid(True, linestyle='--', alpha=0.6)
    
    # 4. Accuracy Trend
    ax4 = axes[1, 1]
    # Scatter for raw (1=Correct, 0=Incorrect)
    colors = ['red' if x==0 else 'blue' for x in df["Initial_Accuracy"]]
    ax4.scatter(df["Sample_ID"], df["Initial_Accuracy"], c=colors, alpha=0.5, label='Raw Result')
    # Line for Moving Average
    ax4.plot(df["Sample_ID"], df["Accuracy_MA"], color='orange', linewidth=2, label='Moving Avg (5)')
    ax4.set_title('Validation Accuracy (Initial Generation)', fontsize=12)
    ax4.set_xlabel('Sample ID')
    ax4.set_ylabel('Accuracy (1=Pass, 0=Fail)')
    ax4.legend()
    ax4.grid(True, linestyle='--', alpha=0.6)
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(OUTPUT_IMAGE)
    print(f"Visualization saved to {OUTPUT_IMAGE}")

if __name__ == "__main__":
    print("running...")
    df = parse_logs(LOG_DIR)
    print(df.head())
    plot_metrics(df)
