import requests

base = 'http://localhost:8080'

r = requests.get(f'{base}/api/v1/tools/', timeout=10)
print('Status:', r.status_code)
print('JSON:', r.json())
