"""Provision the isolated realm using an administrative service account.

Defaults to validation only. Never accepts human passwords or bypasses MFA.
Credentials file: {"client_id": "...", "client_secret": "..."} with mode 600.
"""
import argparse
import json
import stat
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://login.themike.io'


def provision(credentials_file, apply=False):
    realm = json.loads((ROOT / 'infra/keycloak/koodaria-realm.json').read_text())
    assert realm['realm'] == 'koodaria' and realm['organizationsEnabled']
    if not apply:
        print('Validated koodaria realm configuration. No remote changes performed.')
        return
    if credentials_file is None:
        raise ValueError('--credentials-file is required with --apply')
    path = Path(credentials_file)
    if stat.S_IMODE(path.stat().st_mode) & 0o077:
        raise ValueError('Credentials file must be private (chmod 600).')
    credentials = json.loads(path.read_text())
    payload = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': credentials['client_id'],
        'client_secret': credentials['client_secret'],
    }).encode()
    request = urllib.request.Request(
        BASE + '/realms/master/protocol/openid-connect/token', data=payload)
    with urllib.request.urlopen(request, timeout=30) as response:
        token = json.load(response)['access_token']
    headers = {'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'}
    target = BASE + '/admin/realms/koodaria'
    try:
        with urllib.request.urlopen(urllib.request.Request(target, headers=headers), timeout=30):
            print('Realm koodaria already exists; left unchanged.')
            return
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    request = urllib.request.Request(BASE + '/admin/realms', method='POST',
                                     headers=headers, data=json.dumps(realm).encode())
    with urllib.request.urlopen(request, timeout=30) as response:
        assert response.status == 201
    print('Created koodaria realm. Existing realms unchanged. No users or organizations created.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials-file', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        provision(args.credentials_file, args.apply)
    except urllib.error.HTTPError as error:
        raise SystemExit('Keycloak request failed (HTTP %s); response omitted to protect credentials.' % error.code)
