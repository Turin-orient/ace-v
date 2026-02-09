"""Simple debug script to test Azure OpenAI connection"""
import os
from dotenv import load_dotenv
import openai

load_dotenv()

print("="*60)
print("AZURE OPENAI CONNECTION DEBUG")
print("="*60)

endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
api_key = os.getenv('AZURE_OPENAI_API_KEY')
api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
deployment = os.getenv('DEFAULT_AZURE_OPENAI_DEPLOYMENT', 'gpt-5-mini')

print(f"\nEndpoint: {endpoint}")
print(f"API Version: {api_version}")
print(f"Deployment: {deployment}")
print(f"API Key: {api_key[:20]}... (masked)")

print("\n" + "="*60)
print("Creating client...")
try:
    client = openai.AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version
    )
    print("[OK] Client created successfully")
except Exception as e:
    print(f"[ERROR] Failed to create client: {e}")
    exit(1)

print("\n" + "="*60)
print("Making API call...")
print(f"Deployment: {deployment}")

try:
    response = client.chat.completions.create(
        model=deployment,
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=10
    )
    
    print("\n[SUCCESS] API call successful!")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Tokens used: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"\n[ERROR] API call failed:")
    print(f"Type: {type(e).__name__}")
    print(f"Message: {str(e)}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "="*60)
print("[SUCCESS] All tests passed!")
print("="*60)
