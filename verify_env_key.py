import os
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load env file directly
load_dotenv(override=True)

endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
api_key = os.getenv("AZURE_OPENAI_API_KEY")
api_version = os.getenv("AZURE_OPENAI_API_VERSION")
deployment = os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT")

print(f"Endpoint: {endpoint}")
print(f"Deployment: {deployment}")
print(f"Version: {api_version}")
print("Testing connection...")

client = AzureOpenAI(
    azure_endpoint=endpoint,
    api_key=api_key,
    api_version=api_version
)

try:
    response = client.chat.completions.create(
        model=deployment,
        messages=[
            {"role": "user", "content": "Hello"}
        ],
        max_completion_tokens=50
    )
    print(f"✅ SUCCESS! Full Response Object:")
    print(response.model_dump_json(indent=2))
except Exception as e:
    print(f"❌ ERROR: {e}")
    if hasattr(e, 'response'):
        print(f"Status Code: {e.response.status_code}")
        print(f"Headers: {e.response.headers}")
