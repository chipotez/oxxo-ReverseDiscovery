"""Koodaria welcome: server-side OIDC; browser receives only an opaque session cookie."""
import os
import secrets
import time
from datetime import timedelta
from urllib.parse import urlencode
from flask import Flask, abort, redirect, render_template, request, session
from flask_session import Session
from cachelib.file import FileSystemCache
from authlib.integrations.flask_client import OAuth

ISSUER = 'https://login.koodaria.com/realms/koodaria'
ORIGIN = 'https://koodaria.com'
app = Flask(__name__, static_url_path='/workspace-assets')
app.config.update(
    SECRET_KEY=os.environ['APP_SECRET_KEY'],
    SESSION_TYPE='cachelib',
    SESSION_CACHELIB=FileSystemCache(os.environ.get('SESSION_DIR', '/app/sessions'), threshold=10000, mode=0o600),
    SESSION_COOKIE_NAME='__Host-koodaria', SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_PATH='/', PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_REFRESH_EACH_REQUEST=False, TRUSTED_HOSTS=['koodaria.com', 'localhost', '127.0.0.1'],
    MAX_CONTENT_LENGTH=16384,
)
Session(app)
oauth = OAuth(app)
oauth.register('keycloak', client_id='koodaria-web',
    client_secret=os.environ['OIDC_CLIENT_SECRET'],
    server_metadata_url=ISSUER+'/.well-known/openid-configuration',
    client_kwargs={'scope':'openid profile email', 'code_challenge_method':'S256'},
)

@app.after_request
def secure(response):
    response.headers['Cache-Control']='no-store'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self' https://login.koodaria.com/realms/koodaria/protocol/openid-connect/logout"
    return response

@app.get('/auth/login')
def login():
    if session.get('identity') and session.get('expires_at',0)>time.time():
        return redirect('/bienvenida/')
    session.clear()
    session.permanent=True
    return oauth.keycloak.authorize_redirect(ORIGIN+'/auth/callback', nonce=secrets.token_urlsafe(32))

@app.get('/auth/callback')
def callback():
    try:
        token=oauth.keycloak.authorize_access_token()
        identity=token.get('userinfo')
        if not identity or not identity.get('sub'):
            raise ValueError('Missing verified identity')
    except Exception:
        session.clear()
        return render_template('error.html'),400
    # Invalidate the pre-authentication session to prevent session fixation.
    session.clear()
    session['authenticated']=True
    app.session_interface.regenerate(session)
    session['identity']={k:identity.get(k,'') for k in ('sub','given_name','name','email')}
    session['id_token']=token['id_token']
    session['expires_at']=time.time()+1800
    session['csrf']=secrets.token_urlsafe(32)
    return redirect('/bienvenida/')

@app.get('/bienvenida/')
def welcome():
    if not session.get('identity') or session.get('expires_at',0)<=time.time():
        return redirect('/auth/login')
    identity=session['identity']
    name=identity.get('name') or identity.get('given_name') or 'Mi cuenta'
    initials=''.join(word[0] for word in name.split()[:2]).upper()
    return render_template('welcome.html', name=name, first_name=identity.get('given_name') or name.split()[0], initials=initials, csrf=session['csrf'], account_url=ISSUER+'/account/')

@app.post('/auth/logout')
def logout():
    if not session.get('csrf') or not secrets.compare_digest(request.form.get('csrf',''),session['csrf']):
        abort(400)
    id_token=session.get('id_token')
    session.clear()
    # Keycloak terminates SSO as well as the local application session.
    params={'client_id':'koodaria-web','post_logout_redirect_uri':ORIGIN+'/'}
    if id_token:params['id_token_hint']=id_token
    return redirect(ISSUER+'/protocol/openid-connect/logout?'+urlencode(params))

@app.get('/healthz')
def health():
    return 'ok\n'
