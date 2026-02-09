"""Azure OpenAI - Find Deployment Names

This script helps you discover what deployments are available
in your Azure OpenAI resource.
"""

import os
from dotenv import load_dotenv
import openai

load_dotenv()

print("="*60)
print("AZURE OPENAI - DEPLOYMENT FINDER")
print("="*60)

endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_key = os.getenv('AZURE_OPENAI_API_KEY')

print(f"\nEndpoint: {endpoint}")
print(f"API Key: {api_key[:20]}... (masked)")

# Common deployment names to try
COMMON_DEPLOYMENTS = [
    "gpt-4",
    "gpt-4o",
    "gpt-4-turbo",
    "gpt-35-turbo",
    "gpt-4o-mini",
    "gpt-5-mini",
    "text-embedding-ada-002"
]

# Different API versions to try
API_VERSIONS = [
    "2024-02-15-preview",
    "2024-06-01",
    "2024-08-01-preview",
    "2023-12-01-preview"
]

print("\n" + "="*60)
print("TESTING DEPLOYMENTS")
print("="*60)

working_configs = []

for api_version in API_VERSIONS:
    print(f"\n--- Testing API Version: {api_version} ---")
    
    try:
        client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        
        for deployment in COMMON_DEPLOYMENTS:
            try:
                response = client.chat.completions.create(
                    model=deployment,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5
                )
                
                print(f"  [OK] {deployment}")
                working_configs.append({
                    "api_version": api_version,
                    "deployment": deployment
                })
                
            except openai.NotFoundError:
                print(f"  [NOT FOUND] {deployment}")
            except Exception as e:
                print(f"  [ERROR] {deployment}: {type(e).__name__}")
                
    except Exception as e:
        print(f"  [ERROR] Failed to create client: {type(e).__name__}")

print("\n" + "="*60)
print("RESULTS")
print("="*60)

if working_configs:
    print("\n[SUCCESS] Found working configurations:")
    for config in working_configs:
        print(f"\n  Deployment: {config['deployment']}")
        print(f"  API Version: {config['api_version']}")
    
    print("\n" + "="*60)
    print("RECOMMENDED .env CONFIGURATION:")
    print("="*60)
    best = working_configs[0]
    print(f"\nAZURE_OPENAI_API_VERSION={best['api_version']}")
    print(f"DEFAULT_AZURE_OPENAI_DEPLOYMENT={best['deployment']}")
else:
    print("\n[ERROR] No working deployments found!")
    print("\nPossible issues:")
    print("  1. No deployments exist in your Azure resource")
    print("  2. Endpoint URL is incorrect")
    print("  3. API key doesn't have permission")
    print("\nPlease check Azure Portal > Your OpenAI Resource > Deployments")
