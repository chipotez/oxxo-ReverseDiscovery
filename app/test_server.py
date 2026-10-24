"""Run with SESSION_DIR pointing to a temporary directory, not the live session store."""
import unittest
from unittest.mock import patch
from server import app, oauth, SESSION_SECONDS, SESSION_POLICY

class WelcomeTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING']=True
        self.client=app.test_client()
    def authenticated(self):
        import time
        with self.client.session_transaction() as s:
            s.update(identity={'sub':'qa-test','name':'QA <script>alert(1)</script>','given_name':'QA <script>alert(1)</script>'},expires_at=time.time()+300,csrf='qa-csrf',id_token='PRIVATE-ID-TOKEN')
    def test_anonymous_welcome_requires_login(self):
        response=self.client.get('/bienvenida/')
        self.assertEqual(response.status_code,302)
        self.assertEqual(response.location,'/auth/login')
    def test_callback_rejects_missing_transaction(self):
        response=self.client.get('/auth/callback?code=forged&state=forged')
        self.assertEqual(response.status_code,400)
        self.assertNotIn(b'forged',response.data)
    def test_render_escapes_profile_and_omits_tokens(self):
        self.authenticated();response=self.client.get('/bienvenida/')
        self.assertEqual(response.status_code,200)
        self.assertIn(b'&lt;script&gt;',response.data)
        self.assertNotIn(b'Bienvenido,',response.data)
        self.assertNotIn(b'TU ESPACIO EN KOODARIA',response.data)
        self.assertIn(b'workspace-rail',response.data)
        self.assertIn(b'catalog-v1.js',response.data)
        self.assertIn(b'catalog-v1.css',response.data)
        self.assertIn(b'resource-flow-v1.js',response.data)
        self.assertIn(b'resource-flow-v1.css',response.data)
        self.assertNotIn(b'PRIVATE-ID-TOKEN',response.data)
        self.assertEqual(response.headers['Cache-Control'],'no-store')
    def test_expired_local_session_requires_login(self):
        self.authenticated()
        with self.client.session_transaction() as s:s['expires_at']=0
        self.assertEqual(self.client.get('/bienvenida/').location,'/auth/login')
    def test_logout_is_post_only_and_csrf_protected(self):
        self.authenticated()
        self.assertEqual(self.client.get('/auth/logout').status_code,405)
        self.assertEqual(self.client.post('/auth/logout',data={'csrf':'forged'}).status_code,400)
        self.assertEqual(self.client.get('/bienvenida/').status_code,200)
    def test_logout_clears_local_session_and_redirects_to_provider(self):
        self.authenticated();response=self.client.post('/auth/logout',data={'csrf':'qa-csrf'})
        self.assertEqual(response.status_code,302)
        self.assertTrue(response.location.startswith('https://login.koodaria.com/realms/koodaria/protocol/openid-connect/logout?'))
        self.assertEqual(self.client.get('/bienvenida/').location,'/auth/login')
    def test_identity_cookie_is_secure_and_opaque(self):
        self.authenticated();response=self.client.get('/bienvenida/')
        cookie=self.client.get_cookie('__Host-koodaria')
        self.assertTrue(cookie.secure and cookie.http_only)
        self.assertEqual(cookie.same_site,'Lax')
        self.assertNotIn('qa-test',cookie.value)
    def test_untrusted_host_rejected(self):
        self.assertEqual(self.client.get('/bienvenida/',headers={'Host':'attacker.invalid'}).status_code,400)

    def test_session_status_requires_valid_session(self):
        self.assertEqual(self.client.get('/auth/session').status_code,401)
        self.authenticated();r=self.client.get('/auth/session')
        self.assertEqual(r.json,{'subject':'qa-test','csrf':'qa-csrf'})
        self.assertEqual(r.headers['Cache-Control'],'no-store')
        self.assertNotIn(b'PRIVATE-ID-TOKEN',r.data)
        with self.client.session_transaction() as s:s['expires_at']=0
        self.assertEqual(self.client.get('/auth/session').status_code,401)

    def test_valid_session_login_preserves_safe_destination(self):
        self.authenticated()
        response=self.client.get('/auth/login',query_string={'next':'/bienvenida/#/herramientas/mapeo-recursos'})
        self.assertEqual(response.location,'/bienvenida/#/herramientas/mapeo-recursos')
        for destination in ['https://attacker.invalid','//attacker.invalid','//[broken','/auth/logout','/bienvenida/?external=yes','/bienvenida/\\evil']:
            self.assertEqual(self.client.get('/auth/login',query_string={'next':destination}).location,'/bienvenida/')

    def test_oidc_callback_restores_destination_and_refreshes_csrf(self):
        from flask import redirect
        destination='/bienvenida/#/herramientas/mapeo-recursos'
        with patch.object(oauth.keycloak,'authorize_redirect',return_value=redirect('/qa-provider')):
            self.client.get('/auth/login',query_string={'next':destination})
        token={'userinfo':{'sub':'qa-test','name':'QA'},'id_token':'QA-ID-TOKEN'}
        with patch.object(oauth.keycloak,'authorize_access_token',return_value=token):
            self.assertEqual(self.client.get('/auth/callback').location,destination)
        self.assertEqual(self.client.get('/auth/session').status_code,200)
        self.assertEqual(self.client.get('/bienvenida/').status_code,200)
        with self.client.session_transaction() as s:self.assertNotIn('return_to',s)

    def test_login_cookie_is_persistent_and_valid_for_two_hours(self):
        import time
        token={'userinfo':{'sub':'qa-persistent','name':'QA'},'id_token':'QA-ID-TOKEN'}
        started=time.time()
        with patch.object(oauth.keycloak,'authorize_access_token',return_value=token):
            self.assertEqual(self.client.get('/auth/callback').status_code,302)
        cookie=self.client.get_cookie('__Host-koodaria')
        self.assertIsNotNone(cookie.expires)
        self.assertAlmostEqual(cookie.expires.timestamp()-started,7200,delta=3)
        with self.client.session_transaction() as s:
            self.assertTrue(s.permanent)
            self.assertEqual(s['session_policy'],SESSION_POLICY)
        with patch('server.time.time',return_value=started+7190):
            self.assertEqual(self.client.get('/auth/session').status_code,200)
        with patch('server.time.time',return_value=started+7205):
            self.assertEqual(self.client.get('/auth/session').status_code,401)

    def test_valid_legacy_session_is_upgraded_once_without_reauthentication(self):
        import time
        self.authenticated()
        with self.client.session_transaction() as s:s['expires_at']=time.time()+1200
        self.assertEqual(self.client.get('/auth/session').status_code,200)
        with self.client.session_transaction() as s:
            upgraded=s['expires_at'];self.assertTrue(s.permanent)
            self.assertAlmostEqual(upgraded-time.time(),6600,delta=3)
        self.client.get('/auth/session')
        with self.client.session_transaction() as s:self.assertEqual(s['expires_at'],upgraded)

if __name__=='__main__':unittest.main()
