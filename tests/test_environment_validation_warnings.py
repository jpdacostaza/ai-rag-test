import os
from core.security import validate_environment, perform_environment_validation

def test_environment_validation_handles_missing_vars(monkeypatch):
    # Clear potential env vars
    for k in ['REDIS_HOST','CHROMA_HOST','DEFAULT_MODEL','OLLAMA_BASE_URL','SECRET_KEY','ALLOWED_ORIGINS','TRUSTED_HOSTS']:
        monkeypatch.delenv(k, raising=False)
    result = validate_environment()
    assert isinstance(result, dict)
    # status remains ok (pure function) even if missing, but keys should be present or error captured
    assert 'status' in result
    perform_environment_validation()  # Should log but not raise
