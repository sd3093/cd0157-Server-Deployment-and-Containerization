"""Record real responses from the public EKS service; never log JWTs."""
from datetime import datetime, timezone
import json
import sys
import time
from urllib.error import HTTPError
from urllib.request import Request, urlopen

root = sys.argv[1].rstrip('/')
results = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'base_url': root, 'checks': []}

def call(path, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(root + path, data=json.dumps(data).encode() if data else None, headers=headers)
    try:
        with urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read())
    except HTTPError as exc:
        return exc.code, None

status, body = call('/')
assert (status, body) == (200, 'Healthy'), (status, body)
results['checks'].append({'method': 'GET', 'path': '/', 'status': status, 'response': body})
status, body = call('/auth', {'email': 'review@example.com', 'password': 'test-only'})
assert status == 200 and isinstance(body['token'], str)
token = body['token']
assert len(token.split('.')) == 3
results['checks'].append({'method': 'POST', 'path': '/auth', 'status': status, 'response': {'token': '[omitted: JWT verified via /contents]'}})
status, body = call('/contents', token=token)
assert status == 200 and body['email'] == 'review@example.com'
assert body['exp'] > time.time() and body['nbf'] <= time.time()
assert set(body) == {'email', 'exp', 'nbf'}
results['checks'].append({'method': 'GET', 'path': '/contents', 'status': status, 'response': body})
for token, condition in [(None, 'missing token'), ('not-a-valid-token', 'invalid token')]:
    status, body = call('/contents', token=token)
    assert status == 401
    results['checks'].append({'method': 'GET', 'path': '/contents', 'case': condition, 'status': status})
results['result'] = 'PASS'
print(json.dumps(results, indent=2))
