import os
from openai import AzureOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

client = AzureOpenAI(
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version="2024-12-01-preview"
)

# MODELS TO TEST
models = ["gpt-4o", "gpt-4o-mini", "gpt-4", "gpt-35-turbo"]

for model in models:
    print(f"Testing {model}...")
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hi"}],
            max_completion_tokens=10 
        )
        print(f"✅ SUCCESS with {model}! Response: {response.choices[0].message.content}")
    except Exception as e:
        print(f"❌ Failed {model}: {str(e)[:100]}...")
