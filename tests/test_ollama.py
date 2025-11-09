import requests
import json

url = "http://localhost:11434/api/chat"

# Test 1: Simple message without tools
payload1 = {
    "model": "gpt-oss:20b",
    "messages": [
        {"role": "user", "content": "Say hello"}
    ],
    "stream": False
}

print("Test 1: Simple chat without tools")
try:
    response = requests.post(url, json=payload1, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "="*80 + "\n")

# Test 2: With tools
payload2 = {
    "model": "gpt-oss:20b",
    "messages": [
        {"role": "user", "content": "What files are in the current directory?"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List files in a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path"
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    ],
    "stream": False
}

print("Test 2: Chat with tools")
try:
    response = requests.post(url, json=payload2, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")

print("\n" + "="*80 + "\n")

# Test 3: With system prompt (should NOT call tools for greetings)
payload3 = {
    "model": "gpt-oss:20b",
    "messages": [
        {
            "role": "system", 
            "content": "You are Wolf. Only use tools when explicitly asked to perform file operations. For greetings, respond conversationally without tools."
        },
        {"role": "user", "content": "hey there"}
    ],
    "tools": [
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List files in a directory",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Directory path"
                        }
                    },
                    "required": ["path"]
                }
            }
        }
    ],
    "stream": False
}

print("Test 3: System prompt (greeting should NOT trigger tools)")
try:
    response = requests.post(url, json=payload3, timeout=30)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        message = result.get("message", {})
        has_tool_calls = "tool_calls" in message
        print(f"Response has tool_calls: {has_tool_calls}")
        if has_tool_calls:
            print("❌ FAILED: Greeting triggered tool call (should be conversational only)")
        else:
            print("✅ PASSED: Conversational response without tools")
        print(f"Response: {json.dumps(result, indent=2)}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
