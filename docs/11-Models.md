# Models

`models/models.py` defines Pydantic models for:
- Chat: messages, requests, responses (OpenAI-compatible shapes)
- Health: health report schemas
- Errors: standardized error payloads
- Uploads/Memory: request/response shapes used by routes

These models validate input/output across the API and help keep contracts explicit.
