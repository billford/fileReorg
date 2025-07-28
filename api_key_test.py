#!/usr/bin/env python3
"""
Quick API Key Format Test
Test your OpenAI API key format without making API calls
"""

def validate_openai_key(api_key):
    """Validate OpenAI API key format"""
    if not api_key:
        return False, "No API key provided"
    
    # Clean the key
    cleaned_key = api_key.strip().replace('\n', '').replace('\r', '').replace('\t', '')
    
    # Check prefix
    if cleaned_key.startswith('sk-proj-'):
        key_type = "project-based"
        min_len, max_len = 150, 200
        expected_len = "~164"
    elif cleaned_key.startswith('sk-'):
        key_type = "legacy"
        min_len, max_len = 45, 60
        expected_len = "48-51"
    else:
        return False, "Key must start with 'sk-' (legacy) or 'sk-proj-' (project-based)"
    
    # Check length
    if len(cleaned_key) < min_len or len(cleaned_key) > max_len:
        return False, f"{key_type.title()} key length ({len(cleaned_key)}) is unusual (expected {expected_len})"
    
    # Check for corruption
    if ' ' in cleaned_key or '\t' in cleaned_key:
        return False, "Key contains spaces/tabs - likely corrupted during copy/paste"
    
    return True, f"✅ Valid {key_type} key format (length: {len(cleaned_key)})"

def main():
    print("🔑 OpenAI API Key Format Validator")
    print("=" * 40)
    
    # Test the user's key from the issue
    user_key = "sk-proj-abc123"
    print("Testing the API key from your issue:")
    print(f"Key: {user_key[:20]}...{user_key[-10:]}")
    
    is_valid, message = validate_openai_key(user_key)
    
    if is_valid:
        print(f"✅ SUCCESS: {message}")
        print("\n🎉 Your API key format is now supported!")
        print("The file organizer will now accept this key.")
    else:
        print(f"❌ FAILED: {message}")
    
    print("\n" + "=" * 40)
    print("You can also test your own key:")
    
    while True:
        test_key = input("\nEnter API key to test (or 'quit' to exit): ").strip()
        
        if test_key.lower() in ['quit', 'exit', 'q']:
            break
            
        if not test_key:
            continue
            
        is_valid, message = validate_openai_key(test_key)
        
        if is_valid:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")

if __name__ == "__main__":
    main()
