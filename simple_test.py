"""Simple Azure OpenAI deployment test"""
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

print("Testing Azure OpenAI with max_completion_tokens...")
try:
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[{"role": "user", "content": "Say: Hello"}],
        max_completion_tokens=10
    )
    print(f"Response content: '{response.choices[0].message.content}'")
    print(f"Content length: {len(response.choices[0].message.content)}")
    print(f"Tokens used: {response.usage.completion_tokens}")
except Exception as e:
    print(f"Error: {e}")
