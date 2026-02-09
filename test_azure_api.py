

import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import openai

def print_section(title):
    """Print formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def test_api_connection():
    """
    Simple test to verify Azure OpenAI API connection works.
    """
    print("\n" + "█"*80)
    print("█" + " "*78 + "█")
    print("█" + "  AZURE OPENAI API CONNECTION TEST".center(78) + "█")
    print("█" + " "*78 + "█")
    print("█"*80)
    
    # Load environment variables
    print_section("1. LOADING ENVIRONMENT VARIABLES")
    load_dotenv()
    
    endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
    api_key = os.getenv('AZURE_OPENAI_API_KEY', '')
    api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2025-08-07')
    
    print(f"Endpoint: {endpoint}")
    print(f"API Key: {'*' * 40} (masked)")
    print(f"API Version: {api_version}")
    
    # Validate credentials
    if not endpoint:
        print("\n[ERROR] AZURE_OPENAI_ENDPOINT not found in .env file")
        return False
    
    if not api_key:
        print("\n[ERROR] AZURE_OPENAI_API_KEY not found in .env file")
        return False
    
    print("\n[OK] Environment variables loaded successfully")
    
    # Create Azure OpenAI client
    print_section("2. CREATING AZURE OPENAI CLIENT")
    
    try:
        client = openai.AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version
        )
        print(f"[OK] Client created: {type(client).__name__}")
    except Exception as e:
        print(f"[ERROR] Failed to create client: {str(e)}")
        return False
    
    # Make a test API call
    print_section("3. TESTING API CALL")
    
    print("Sending test request to Azure OpenAI...")
    print("Model deployment: (will use whatever deployment name you have)")
    print("Test prompt: 'Say hello in one word'")
    
    # You need to replace 'gpt-4' with your actual deployment name in Azure
    # Common deployment names: gpt-4, gpt-35-turbo, gpt-4-turbo, etc.
    # Check your Azure OpenAI resource to find the correct deployment name
    
    # deployment_name = "gpt-5-mini"  # Updated from .env: DEFAULT_AZURE_OPENAI_DEPLOYMENT
    deployment_name = os.getenv("DEFAULT_AZURE_OPENAI_DEPLOYMENT", "gpt-5-mini")

    
    try:
        start_time = time.time()
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "user", "content": "Say hello in one word"}
            ],
            max_completion_tokens=10  # Changed from max_tokens for API version 2025-08-07
        )
        
        elapsed = time.time() - start_time
        
        print(f"\n[SUCCESS] API CALL SUCCESSFUL!")
        print(f"Response time: {elapsed:.2f} seconds")
        
        # Display response details
        print_section("4. RESPONSE DETAILS")
        
        print(f"Response ID: {response.id}")
        print(f"Model: {response.model}")
        print(f"Created: {response.created}")
        
        if response.choices and len(response.choices) > 0:
            message = response.choices[0].message
            print(f"\nResponse Content:")
            print(f"   Role: {message.role}")
            print(f"   Content: {message.content}")
            print(f"   Finish Reason: {response.choices[0].finish_reason}")
        
        if response.usage:
            print(f"\nToken Usage:")
            print(f"   Prompt tokens: {response.usage.prompt_tokens}")
            print(f"   Completion tokens: {response.usage.completion_tokens}")
            print(f"   Total tokens: {response.usage.total_tokens}")
        
        # Print raw response object
        print(f"\nFull Response Object:")
        print(response)
        
        print_section("TEST RESULT: SUCCESS")
        print("Azure OpenAI API is working correctly!")
        print("You can now use this API configuration with the ACE framework.")
        
        return True
        
    except openai.NotFoundError as e:
        print(f"\n[ERROR] MODEL NOT FOUND")
        print(f"Error: {str(e)}")
        print(f"\nSolution:")
        print(f"   1. Check your Azure OpenAI resource in Azure Portal")
        print(f"   2. Go to 'Deployments' section")
        print(f"   3. Find your deployment name (e.g., 'gpt-4', 'gpt-35-turbo')")
        print(f"   4. Update the 'deployment_name' variable in this script")
        print(f"\n   Current deployment name used: '{deployment_name}'")
        return False
        
    except openai.AuthenticationError as e:
        print(f"\n[ERROR] AUTHENTICATION FAILED")
        print(f"Error: {str(e)}")
        print(f"\nCheck:")
        print(f"   - API key is correct in .env file")
        print(f"   - API key hasn't expired")
        print(f"   - Endpoint URL is correct")
        return False
        
    except openai.RateLimitError as e:
        print(f"\n[ERROR] RATE LIMIT EXCEEDED")
        print(f"Error: {str(e)}")
        print(f"\nYour API quota may be exceeded. Wait and try again.")
        return False
        
    except Exception as e:
        print(f"\n[ERROR] API CALL FAILED")
        print(f"Error Type: {type(e).__name__}")
        print(f"Error Message: {str(e)}")
        print(f"\nFull Error Details:")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n" + "="*80)
    print("IMPORTANT: Update 'deployment_name' variable with your Azure deployment name!")
    print("Check Azure Portal > Your OpenAI Resource > Deployments")
    print("="*80)
    
    success = test_api_connection()
    
    print("\n" + "="*80)
    if success:
        print("[SUCCESS] All checks passed! API connection is working.")
        sys.exit(0)
    else:
        print("[FAILED] Test failed. Please check the error messages above.")
        sys.exit(1)
