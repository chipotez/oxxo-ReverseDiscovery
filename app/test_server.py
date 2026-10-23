"""Run with SESSION_DIR pointing to a temporary directory, not the live session store."""
import unittest
from unittest.mock import patch
from server import app, oauth

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

if __name__=='__main__':unittest.main()
