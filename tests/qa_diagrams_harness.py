# Test-only harness, outside app/ and never included in production images.
import os,time,secrets
assert os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable'
assert os.environ['DIAGRAM_DATABASE_URL'].endswith('/koodaria_diagrams_qa')
from server import app
from flask import session,redirect,request
from diagrams import connection
from access import sync_identity
app.config.update(SESSION_COOKIE_NAME='qa-koodaria',SESSION_COOKIE_SECURE=False)
@app.get('/__qa/session')
def fixture():
    kind=request.args.get('as','owner')
    identities={'owner':('qa-browser-diagrams','qa-owner-browser@example.invalid'),'guest':('qa-browser-guest','qa-guest-browser@example.invalid'),'stranger':('qa-browser-stranger','qa-stranger-browser@example.invalid')}
    if kind not in identities:return '',400
    sub,email=identities[kind]
    if kind=='owner':
        with connection(sub) as conn:conn.execute('SELECT qa_seed_member(%s)',(sub,))
    identity={'sub':sub,'name':'QA '+kind,'given_name':'QA','email':email,'email_verified':True}
    sync_identity(identity)
    session.clear();session.update(identity=identity,expires_at=time.time()+7200,session_policy='absolute-2h-v1',csrf=secrets.token_hex(24))
    return redirect('/bienvenida/')
app.run(host='0.0.0.0',port=8000)
