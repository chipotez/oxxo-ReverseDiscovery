"""Run as Podman owner on the build host; uses only disposable synthetic sessions."""
import os,secrets,subprocess,uuid
image=os.environ.get('KOODARIA_QA_IMAGE','localhost/koodaria-workspace:session-2h-20261023')
volume='koodaria-session-qa-'+uuid.uuid4().hex
# These credentials exist only for synthetic sessions in an isolated disposable volume.
env=dict(os.environ,APP_SECRET_KEY=secrets.token_hex(32),OIDC_CLIENT_SECRET='qa-disposable-only')
subprocess.run(['podman','volume','create',volume],check=True,stdout=subprocess.DEVNULL)
base=['podman','run','--rm','--network','none','--read-only','--tmpfs','/tmp:rw,size=16m','-v',volume+':/app/sessions:U,Z','-e','SESSION_DIR=/app/sessions','-e','APP_SECRET_KEY','-e','OIDC_CLIENT_SECRET',image,'python','-c']
first='''import os,json,time
os.umask(0o077)
from unittest.mock import patch
from server import app,oauth
from pathlib import Path
client=app.test_client()
with patch.object(oauth.keycloak,'authorize_access_token',return_value={'userinfo':{'sub':'qa-restart','name':'QA'},'id_token':'QA-ID-TOKEN'}):
 assert client.get('/auth/callback').status_code==302
cookie=client.get_cookie('__Host-koodaria')
assert cookie.expires and cookie.secure and cookie.http_only
assert 7190<cookie.expires.timestamp()-time.time()<=7200
Path('/app/sessions/qa-cookie.json').write_text(json.dumps({'value':cookie.value,'expires':cookie.expires.isoformat()}))
assert client.get('/auth/session').status_code==200
'''
second='''import json
from pathlib import Path
from server import app
client=app.test_client()
client.set_cookie('__Host-koodaria',json.loads(Path('/app/sessions/qa-cookie.json').read_text())['value'])
r=client.get('/auth/session')
assert r.status_code==200 and r.json['subject']=='qa-restart'
'''
try:
 subprocess.run(base+[first],check=True,env=env)
 subprocess.run(base+[second],check=True,env=env)
 print('Persistent two-hour cookie accepted after destroying and recreating the application container.')
finally:subprocess.run(['podman','volume','rm',volume],check=True,stdout=subprocess.DEVNULL)
