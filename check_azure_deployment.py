"""
Azure OpenAI Deployment Checker
================================

This script performs detailed checks on Azure OpenAI deployment to diagnose
why responses are empty.
"""

import os
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables
load_dotenv()

print("=" * 80)
print(" AZURE OPENAI DEPLOYMENT DIAGNOSTIC")
print("=" * 80)

# Get configuration
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
model = os.getenv("AZURE_OPENAI_MODEL_NAME", "gpt-5-mini")

print("\n1. CONFIGURATION")
print("-" * 80)
print(f"Endpoint: {endpoint}")
print(f"API Key: {api_key[:8]}...{api_key[-4:] if api_key else 'NOT SET'}")
print(f"API Version: {api_version}")
print(f"Model Name: {model}")

# Initialize client
print("\n2. INITIALIZING CLIENT")
print("-" * 80)
try:
    client = AzureOpenAI(
        api_key=api_key,
        api_version=api_version,
        azure_endpoint=endpoint
    )
    print("✅ Client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize client: {e}")
    exit(1)

# Test 1: Minimal call with max_completion_tokens
print("\n3. TEST 1: Minimal call with max_completion_tokens")
print("-" * 80)
try:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say exactly: Hello World"}],
        max_completion_tokens=20
    )
    
    print(f"✅ API call completed")
    print(f"   Response object type: {type(response)}")
    print(f"   Has choices: {hasattr(response, 'choices')}")
    print(f"   Number of choices: {len(response.choices) if hasattr(response, 'choices') else 0}")
    
    if response.choices:
        print(f"   Choice 0 exists: Yes")
        print(f"   Message object: {response.choices[0].message}")
        print(f"   Content type: {type(response.choices[0].message.content)}")
        print(f"   Content value: '{response.choices[0].message.content}'")
        print(f"   Content length: {len(response.choices[0].message.content) if response.choices[0].message.content else 0}")
        
        if response.choices[0].message.content:
            print(f"   ✅ GOT RESPONSE: {response.choices[0].message.content}")
        else:
            print(f"   ❌ EMPTY RESPONSE (this is the problem!)")
    
    # Token usage
    if hasattr(response, 'usage'):
        print(f"\n   Token Usage:")
        print(f"   - Prompt tokens: {response.usage.prompt_tokens}")
        print(f"   - Completion tokens: {response.usage.completion_tokens}")
        print(f"   - Total tokens: {response.usage.total_tokens}")
        
except Exception as e:
    print(f"❌ Test 1 failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Try with max_tokens instead
print("\n4. TEST 2: Try with max_tokens (old parameter)")
print("-" * 80)
try:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say exactly: Test Response"}],
        max_tokens=20  # Old parameter name
    )
    
    content = response.choices[0].message.content if response.choices else None
    print(f"   Content: '{content}'")
    
    if content:
        print(f"   ✅ GOT RESPONSE with max_tokens")
    else:
        print(f"   ❌ Still empty with max_tokens")
        
except Exception as e:
    print(f"❌ Test 2 failed: {e}")

# Test 3: Try older API version
print("\n5. TEST 3: Try with older API version (2024-02-01)")
print("-" * 80)
try:
    client_old = AzureOpenAI(
        api_key=api_key,
        api_version="2024-02-01",
        azure_endpoint=endpoint
    )
    
    response = client_old.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say: Version Test"}],
        max_tokens=20
    )
    
    content = response.choices[0].message.content if response.choices else None
    print(f"   Content: '{content}'")
    
    if content:
        print(f"   ✅ GOT RESPONSE with old API version!")
    else:
        print(f"   ❌ Still empty with old API version")
        
except Exception as e:
    print(f"❌ Test 3 failed: {e}")

print("\n" + "=" * 80)
print(" DIAGNOSTIC COMPLETE")
print("=" * 80)
print("\nIf ALL tests show empty responses:")
print("  → Azure model deployment has an issue")
print("  → Check Azure Portal for deployment status")
print("  → Verify model capacity is allocated")
print("\nIf SOME tests work:")
print("  → API version or parameter mismatch")
print("  → Update .env with working configuration")
