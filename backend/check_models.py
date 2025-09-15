"""
Quick script to check which OpenAI models you have access to.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def check_available_models():
    """Check which models are available with your API key."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("No API key found!")
        return
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get list of available models
        response = requests.get(
            'https://api.openai.com/v1/models',
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            models = response.json()
            chat_models = []
            
            for model in models['data']:
                model_id = model['id']
                # Filter for chat models
                if any(name in model_id for name in ['gpt-3.5', 'gpt-4', 'chatgpt']):
                    chat_models.append(model_id)
            
            print("Available chat models:")
            for model in sorted(chat_models):
                print(f"  - {model}")
            
            # Test with gpt-3.5-turbo (most common)
            print("\nTesting gpt-3.5-turbo...")
            test_model('gpt-3.5-turbo', headers)
            
        else:
            print(f"Error getting models: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

def test_model(model_name, headers):
    """Test if a specific model works."""
    test_data = {
        'model': model_name,
        'messages': [
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Say hello!'}
        ],
        'max_tokens': 50
    }
    
    try:
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=test_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            message = result['choices'][0]['message']['content']
            print(f"✅ {model_name} works! Response: {message.strip()}")
            return True
        else:
            print(f"❌ {model_name} failed: {response.status_code}")
            print(f"   Error: {response.json().get('error', {}).get('message', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ {model_name} error: {e}")
        return False

if __name__ == "__main__":
    check_available_models()