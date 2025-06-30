# Focused Code Analysis Report

## Summary
- **Total Issues**: 142
- **Endpoints Found**: 44

## Issues Detected

### focused_analysis.py:66
**Issue**: Potentially broken import: from memory import

```
'from memory import',
```

### focused_analysis.py:67
**Issue**: Potentially broken import: import memory.

```
'import memory.',
```

### focused_analysis.py:68
**Issue**: Potentially broken import: from scripts import

```
'from scripts import',
```

### focused_analysis.py:69
**Issue**: Potentially broken import: import scripts.

```
'import scripts.',
```

### focused_analysis.py:70
**Issue**: Potentially broken import: from tests import

```
'from tests import',
```

### focused_analysis.py:71
**Issue**: Potentially broken import: import tests.

```
'import tests.',
```

### focused_analysis.py:72
**Issue**: Potentially broken import: from readme import

```
'from readme import',
```

### focused_analysis.py:73
**Issue**: Potentially broken import: import readme.

```
'import readme.'
```

### database_manager.py:339
**Issue**: Referenced endpoint not found: {OLLAMA_BASE_URL}/api/tags

```
response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
```

### database_manager.py:389
**Issue**: Referenced endpoint not found: {OLLAMA_BASE_URL}/api/pull

```
f"{OLLAMA_BASE_URL}/api/pull",
```

### database_manager.py:399
**Issue**: Referenced endpoint not found: {OLLAMA_BASE_URL}/api/tags

```
verify_response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
```

### enhanced_memory_api.py:592
**Issue**: Referenced endpoint not found:    POST /api/memory/retrieve

```
print("   POST /api/memory/retrieve")
```

### enhanced_memory_api.py:593
**Issue**: Referenced endpoint not found:    POST /api/learning/process_interaction

```
print("   POST /api/learning/process_interaction")
```

### memory_filter_function.py:174
**Issue**: Referenced endpoint not found: {self.valves.memory_api_url}/api/memory/retrieve

```
f"{self.valves.memory_api_url}/api/memory/retrieve",
```

### memory_filter_function.py:197
**Issue**: Referenced endpoint not found: {self.valves.memory_api_url}/api/memory/retrieve

```
f"{self.valves.memory_api_url}/api/memory/retrieve",
```

### memory_filter_function.py:222
**Issue**: Referenced endpoint not found: {self.valves.memory_api_url}/api/learning/process_interaction

```
f"{self.valves.memory_api_url}/api/learning/process_interaction",
```

### memory_function.py:56
**Issue**: Referenced endpoint not found: {self.valves.memory_api_url}/api/memory/{user_id}

```
f"{self.valves.memory_api_url}/api/memory/{user_id}",
```

### memory_function.py:75
**Issue**: Referenced endpoint not found: {self.valves.memory_api_url}/api/memory/{user_id}

```
f"{self.valves.memory_api_url}/api/memory/{user_id}",
```

### model_manager.py:36
**Issue**: Referenced endpoint not found: {OLLAMA_BASE_URL}/api/tags

```
resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
```

### model_manager.py:69
**Issue**: Referenced endpoint not found: {OLLAMA_BASE_URL}/api/pull

```
resp = await client.post(f"{OLLAMA_BASE_URL}/api/pull", json={"name": model_name}, timeout=300.0)
```

### model_manager.py:149
**Issue**: Referenced endpoint not found: {OLLAMA_BASE_URL}/api/delete

```
resp = await client.request("DELETE", f"{OLLAMA_BASE_URL}/api/delete", json={"name": model_name})
```

### openwebui_api_bridge.py:126
