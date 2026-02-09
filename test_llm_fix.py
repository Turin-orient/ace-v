
import os
import sys
from dotenv import load_dotenv
import openai

# Add current directory to path to import local modules
sys.path.append(os.getcwd())
from llm import timed_llm_call

def test_fix():
    load_dotenv()
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
    api_key = os.getenv('AZURE_OPENAI_API_KEY')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION')
    deployment_name = os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")
    
    client = openai.AzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version=api_version
    )
    
    print(f"Testing timed_llm_call with model: {deployment_name}")
    
    # We use a simple prompt. If the model returns "" (as seen in simple_test.py), 
    # timed_llm_call should now raise an exception and retry.
    # Note: Retries might take a long time if it keeps failing.
    # For this test, we can check the logs/output to see if it retries.
    
    try:
        # Reducing retries for this test so it doesn't hang forever
        response, call_info = timed_llm_call(
            client, 
            "azure", 
            deployment_name, 
            "Say: Hello", 
            role="test", 
            call_id="test_fix",
            retries_on_timeout=3 # limit retries for testing
        )
        print(f"\nFinal Response: '{response}'")
        print(f"Call Info: {call_info}")
    except Exception as e:
        print(f"\nCaught expected exception (if all retries failed): {e}")

if __name__ == "__main__":
    test_fix()
