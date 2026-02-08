#!/usr/bin/env python
"""
OpenRouter API Test Script
Tests API key and model availability with z-ai/glm-4.5-air:free
"""
import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get('OPENROUTER_API_KEY', '')
MODEL = "z-ai/glm-4.5-air:free"
BASE_URL = "https://openrouter.ai/api/v1"


async def test_openrouter():
    """Test OpenRouter API with the specified model."""
    print("=" * 60)
    print("OpenRouter API Test")
    print("=" * 60)
    
    # Check API key
    print("\n1. API Key Check:")
    if not API_KEY:
        print("ERROR: OPENROUTER_API_KEY not found in .env")
        return False
    
    print(f"API Key loaded: {API_KEY[:15]}...")
    print(f"Key length: {len(API_KEY)} characters")
    
    # Test API connection
    print("\n2. Testing API Connection:")
    async with httpx.AsyncClient(timeout=60.0) as client:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://refactorbot.dev",
            "X-Title": "RefactorBot V2"
        }
        
        body = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant."},
                {"role": "user", "content": "What is 2 + 2? Answer briefly."}
            ],
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        try:
            print(f"Sending request to {BASE_URL}/chat/completions")
            print(f"Model: {MODEL}")
            
            response = await client.post(
                f"{BASE_URL}/chat/completions",
                headers=headers,
                json=body
            )
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                choice = data.get("choices", [{}])[0]
                message = choice.get("message", {})
                content = message.get("content", "")
                usage = data.get("usage", {})
                
                print("\n3. Response:")
                print("SUCCESS!")
                print(f"Model: {data.get('model', MODEL)}")
                print(f"Response: {content}")
                print(f"Prompt Tokens: {usage.get('prompt_tokens', 0)}")
                print(f"Completion Tokens: {usage.get('completion_tokens', 0)}")
                print(f"Total Tokens: {usage.get('total_tokens', 0)}")
                
                return True
                
            else:
                print("\n3. Error Response:")
                print(f"FAILED: {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Error: {error_data}")
                except:
                    print(f"Response: {response.text[:500]}")
                return False
                
        except httpx.TimeoutException:
            print("TIMEOUT: Request timed out")
            return False
        except Exception as e:
            print(f"ERROR: {e}")
            return False
    
    print("\n" + "=" * 60)


async def list_models():
    """List available models."""
    print("\n" + "=" * 60)
    print("Available Models Check")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await client.get(
                f"{BASE_URL}/models",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])[:10]
                
                print(f"\nFound {len(data.get('data', []))} models")
                print(f"\nFirst 10 models:")
                for m in models:
                    print(f"   - {m.get('id')}")
            else:
                print(f"Failed to list models: {response.status_code}")
                print(f"   {response.text[:200]}")
                
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 60)


async def main():
    """Run all tests."""
    print(f"\nStarting OpenRouter API Test")
    print(f"Model: {MODEL}")
    print("\n" + "=" * 60)
    
    # Test the API
    success = await test_openrouter()
    
    # List models (optional)
    if success:
        await list_models()
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if success:
        print("OpenRouter API is working correctly!")
        print(f"Model {MODEL} is available!")
    else:
        print("OpenRouter API test failed")
        print("\nTroubleshooting:")
        print("1. Check your API key at https://openrouter.ai/keys")
        print(f"2. Verify the model name: {MODEL}")
        print("3. Check your account credits")
    print("=" * 60)
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
