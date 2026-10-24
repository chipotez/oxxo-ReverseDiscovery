# Test-only harness. Not part of any application image or production route.
import os,time,secrets
assert os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable'
assert os.environ['DIAGRAM_DATABASE_URL'].endswith('/koodaria_diagrams_qa')
from server import app
from flask import session,redirect
app.config.update(SESSION_COOKIE_NAME='qa-koodaria',SESSION_COOKIE_SECURE=False)
@app.get('/__qa/session')
def fixture():
 session.clear();session.update(identity={'sub':'qa-browser-diagrams','name':'QA Diagramas','given_name':'QA'},expires_at=time.time()+7200,csrf=secrets.token_hex(24))
 return redirect('/bienvenida/')
app.run(host='0.0.0.0',port=8000)
