import requests
import json

# Test streaming endpoint
url = "http://localhost:3000/v1/chat/completions"
data = {
    "messages": [{"role": "user", "content": "Hello"}],
    "model": "llama3.2:3b", 
    "stream": True
}

print("Testing streaming endpoint...")
response = requests.post(url, json=data, stream=True)
print(f"Status: {response.status_code}")
print("Response chunks:")

chunk_count = 0
for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
    if chunk:
        chunk_count += 1
        print(f"Chunk {chunk_count}: {repr(chunk)}")
        if chunk_count > 10:  # Limit output
            print("... (truncated)")
            break

print(f"Total chunks received: {chunk_count}")
