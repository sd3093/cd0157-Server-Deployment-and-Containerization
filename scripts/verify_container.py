"""Verify the three rubric endpoints over HTTP in the built container."""
import base64
import hashlib
import hmac
import json
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

def call(url, data=None, token=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    req = Request(url, data=json.dumps(data).encode() if data else None, headers=headers)
    try:
        with urlopen(req, timeout=10) as response:
            return response.status, json.loads(response.read())
    except HTTPError as exc:
        return exc.code, None

container = None
secret = secrets.token_hex(32)
with tempfile.TemporaryDirectory(prefix='udacity-flask-test-') as tmp:
    env_file = Path(tmp) / '.env_file'
    env_file.write_text('JWT_SECRET=' + secret + '\nLOG_LEVEL=INFO\n')
    env_file.chmod(0o600)
    try:
        container = subprocess.check_output([
            'docker', 'run', '-d', '--platform', 'linux/amd64', '--env-file', str(env_file),
            '-p', '127.0.0.1::8080', 'udacity-flask-eks:resubmit-20261118'], text=True).strip()
        address = subprocess.check_output(['docker', 'port', container, '8080/tcp'], text=True).strip()
        root = 'http://' + address
        for attempt in range(20):
            try:
                status, body = call(root + '/')
                break
            except (URLError, ConnectionError):
                time.sleep(0.5)
        assert (status, body) == (200, 'Healthy')
        print('GET /: HTTP 200, Healthy', flush=True)
        status, body = call(root + '/auth', {'email': 'review@example.com', 'password': 'test-only'})
        assert status == 200
        token = body['token']
        message, signature = token.rsplit('.', 1)
        actual = base64.urlsafe_b64decode(signature + '=' * (-len(signature) % 4))
        assert hmac.compare_digest(actual, hmac.new(secret.encode(), message.encode(), hashlib.sha256).digest())
        print('POST /auth: HTTP 200; JWT signature matches the secret supplied through the env file', flush=True)
        status, body = call(root + '/contents', token=token)
        assert status == 200 and body['email'] == 'review@example.com'
        assert body['exp'] > time.time() and body['nbf'] <= time.time()
        assert 'password' not in body
        print('GET /contents: HTTP 200; expected email, valid exp/nbf, no password', flush=True)
        for token in (None, 'not-a-valid-token'):
            assert call(root + '/contents', token=token)[0] == 401
        print('GET /contents with absent or invalid token: HTTP 401', flush=True)
        print('PASS: all three endpoints and env-file signing verified through Gunicorn in Docker', flush=True)
    finally:
        if container:
            subprocess.run(['docker', 'rm', '-f', container], check=True, stdout=subprocess.DEVNULL)
