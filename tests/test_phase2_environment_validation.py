from core.security import validate_environment

def test_validate_environment_returns_dict():
    result = validate_environment()
    assert isinstance(result, dict)
    assert 'status' in result
    # If ok, required keys should be present
    if result['status'] == 'ok':
        for k in ['redis_host','chroma_host','default_model','ollama_base_url']:
            assert k in result
