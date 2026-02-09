
import os
import json
import openai
from dotenv import load_dotenv

def test_json_mode_with_real_prompt():
    load_dotenv()
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2025-08-07')
    deployment_name = os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    
    print(f"Testing with model: {deployment_name}")
    
    client = openai.AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version
    )
    
    # Path to the log file
    log_file = r"c:\Intern_Docs\Research_ACE\ace-azure-openai\results\ace_run_20260129_173922_default_offline\detailed_llm_logs\curator_train_e_1_s_1_20260129_174018_159.json"
    
    with open(log_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
        prompt = data['prompt']
    
    print(f"Loaded prompt length: {len(prompt)}")
    
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_completion_tokens=4096
        )
        
        content = response.choices[0].message.content
        print(f"\nResponse Content Length: {len(content) if content else 0}")
        print(f"Finish Reason: {response.choices[0].finish_reason}")
        print(f"Content Preview: {content[:100] if content else 'None'}")
        
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    test_json_mode_with_real_prompt()
