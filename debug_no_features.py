import os
from openai import AzureOpenAI
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(), override=True)

client = AzureOpenAI(
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    api_version="2025-08-07" # Using the user's version
)

print("Attempting request to gpt-5-mini with NO max_tokens params...")
try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": "Hello, are you working?"}]
        # No max_tokens or max_completion_tokens
    )
    print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
except Exception as e:
    print(f"\nFULL ERROR:\n{e}")
