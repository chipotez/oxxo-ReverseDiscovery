"""Administrative API access with a private service-account file, without human passwords."""
import json
import stat
import urllib.request
import urllib.parse
from pathlib import Path


def admin_api(credentials_file, base='https://login.koodaria.com'):
    if not base.startswith('https://'):
        raise ValueError('HTTPS is required')
    path = Path(credentials_file)
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError('Credentials file must be private (chmod 600).')
    credentials = json.loads(path.read_text())
    payload = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': credentials['client_id'],
        'client_secret': credentials['client_secret'],
    }).encode()
    with urllib.request.urlopen(urllib.request.Request(
            base + '/realms/master/protocol/openid-connect/token', data=payload), timeout=30) as response:
        token = json.load(response)['access_token']

    def api(path, method='GET', body=None):
        request = urllib.request.Request(
            base + '/admin/' + path,
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
            return json.loads(raw) if raw else None
    return api
