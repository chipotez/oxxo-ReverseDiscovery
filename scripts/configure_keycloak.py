"""Configure Koodaria's realm and mandatory password/TOTP flow; validation only by default.
Install infra/keycloak/themes/koodaria on the server before applying.
"""
import argparse
import json
import urllib.error
from pathlib import Path
from keycloak_admin import admin_api

ROOT = Path(__file__).resolve().parents[1]
FLOW = 'koodaria-browser-2fa'


def configure(credentials_file, base):
    api = admin_api(credentials_file, base)
    realm = api('realms/koodaria')
    settings = json.loads((ROOT / 'infra/keycloak/koodaria-realm.json').read_text())
    realm.update(settings)
    api('realms/koodaria', 'PUT', realm)
    for action in api('realms/koodaria/authentication/required-actions'):
        if action['alias'] == 'CONFIGURE_TOTP':
            action.update(enabled=True, defaultAction=True)
            api('realms/koodaria/authentication/required-actions/CONFIGURE_TOTP', 'PUT', action)
    if not any(f['alias'] == FLOW for f in api('realms/koodaria/authentication/flows')):
        api('realms/koodaria/authentication/flows/browser/copy', 'POST', {'newName': FLOW})
    path = 'realms/koodaria/authentication/flows/' + FLOW + '/executions'
    in_otp = False
    for execution in api(path):
        provider = execution.get('providerId')
        if execution.get('level') == 0 and execution['displayName'].endswith(' Organization'):
            execution.update(requirement='DISABLED', priority=26)
        elif execution['displayName'].endswith('Browser - Conditional 2FA'):
            execution.update(requirement='REQUIRED', priority=20)
            in_otp = True
        elif in_otp and provider == 'conditional-user-configured':
            execution.update(requirement='DISABLED', priority=10)
        elif in_otp and provider == 'conditional-credential':
            execution.update(requirement='DISABLED', priority=20)
        elif provider == 'auth-otp-form':
            execution.update(requirement='REQUIRED', priority=30)
        else:
            continue
        # Include priority: sending only id/requirement resets it in Keycloak 26.8.
        api(path, 'PUT', execution)
    realm = api('realms/koodaria')
    realm['browserFlow'] = FLOW
    api('realms/koodaria', 'PUT', realm)
    for client in api('realms/koodaria/clients'):
        if client.get('directAccessGrantsEnabled'):
            client['directAccessGrantsEnabled'] = False
            api('realms/koodaria/clients/' + client['id'], 'PUT', client)
    if not any(o['alias'] == 'kyndryl' for o in api('realms/koodaria/organizations')):
        api('realms/koodaria/organizations', 'POST', {
            'name': 'Kyndryl', 'alias': 'kyndryl', 'enabled': True,
            'description': 'Organización de Kyndryl. Cada empresa cliente tendrá una organización independiente.'})
    print('Koodaria configured. No real users or customer domains created.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials-file', type=Path)
    parser.add_argument('--server', default='https://login.koodaria.com')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        print('Validated configuration entry point. No remote changes performed.')
    elif args.credentials_file is None:
        parser.error('--credentials-file is required with --apply')
    else:
        try:
            configure(args.credentials_file, args.server)
        except urllib.error.HTTPError as error:
            raise SystemExit('Keycloak request failed (HTTP %s); response omitted.' % error.code)
