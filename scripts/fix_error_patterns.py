#!/usr/bin/env python3
"""Quick fix for error_patterns.py context parameter issue"""

import re

# Read the file
with open('utilities/error_patterns.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove context parameter from log_service_status calls
patterns_to_fix = [
    r',\s*context=context if config\.log_traceback else None',
    r',\s*context=context',
    r'context=\{[^}]*"request_id":[^}]*\}'
]

for pattern in patterns_to_fix:
    content = re.sub(pattern, '', content)

# Also fix specific context parameter calls
content = content.replace(
    'log_service_status(\n            config.service_type.value.upper(),\n            "info",\n            f"🔄 Starting {operation_name}",\n            context={"request_id": context["request_id"]}\n        )',
    'log_service_status(\n            config.service_type.value.upper(),\n            "info",\n            f"🔄 Starting {operation_name}"\n        )'
)

# Write back
with open('utilities/error_patterns.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed context parameter issues in error_patterns.py")
