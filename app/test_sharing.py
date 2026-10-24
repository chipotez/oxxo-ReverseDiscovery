"""Sharing authorization integration: disposable principals, no real mail or identity writes."""
import os,time,unittest,uuid
from unittest.mock import patch
from server import app
from diagrams import connection
from access import sync_identity

@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Requires disposable database')
class SharingTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING']=True;self.client=app.test_client();suffix=uuid.uuid4().hex
        self.owner='qa-owner-'+suffix;self.guest='qa-guest-'+suffix;self.stranger='qa-stranger-'+suffix;self.email=suffix+'@example.invalid'
        with connection(self.owner) as c:c.execute('SELECT qa_seed_member(%s)',(self.owner,))
        sync_identity({'sub':self.guest,'email':self.email,'email_verified':True,'name':'QA Guest'})
        self.login(self.owner)
    def login(self,sub):
        with self.client.session_transaction() as s:s.clear();s.update(identity={'sub':sub},expires_at=time.time()+7200,csrf='qa-sharing-token',session_policy='absolute-2h-v1')
    def send(self,method,path='',body=None):return getattr(self.client,method)('/bienvenida/api/diagrams'+path,json=body,headers={'X-CSRF-Token':'qa-sharing-token'})
    def create(self):
        response=self.send('post',body={'name':'QA private diagram'});self.assertEqual(response.status_code,201,response.data);return response.json
    def tearDown(self):
        self.login(self.owner)
        with connection(self.owner) as c:
            c.execute('DELETE FROM resource_diagrams WHERE owner_sub=%s',(self.owner,));c.execute('DELETE FROM diagram_folders WHERE owner_sub=%s',(self.owner,))
    def share(self,row):
        with patch('diagrams.notify_existing',return_value=False):r=self.send('post','/'+row['id']+'/shares',{'email':self.email})
        self.assertEqual(r.status_code,201,r.data);return r.json
    def test_guest_can_only_read_edit_export_granted_diagram_and_revocation_is_immediate(self):
        allowed,hidden=self.create(),self.create();grant=self.share(allowed)
        self.login(self.guest)
        self.assertFalse(self.send('get','/capabilities').json['can_create'])
        self.assertEqual(self.send('get','?scope=shared').json['total'],1)
        self.assertEqual(self.send('get','?scope=mine').json['total'],0)
        self.assertEqual(self.send('get','/'+hidden['id']).status_code,404)
        self.assertEqual(self.send('get','/'+allowed['id']).json['access'],'editor')
        changed={**allowed['document'],'name':'QA collaborative edit'}
        self.assertEqual(self.send('put','/'+allowed['id'],{'revision':1,'document':changed}).status_code,200)
        self.assertEqual(self.send('get','/'+allowed['id']+'/pdf').status_code,200)
        self.assertEqual(self.send('post',body={'name':'Forbidden'}).status_code,403)
        self.assertEqual(self.send('post','/folders',{'name':'Forbidden'}).status_code,403)
        self.assertEqual(self.send('post','/move',{'folder_id':None,'items':[{'id':allowed['id'],'revision':2}]}).status_code,403)
        self.assertEqual(self.send('delete','/'+allowed['id'],{'revision':2}).status_code,409)
        self.assertEqual(self.send('post','/'+allowed['id']+'/shares',{'email':'other@example.invalid'}).status_code,403)
        self.assertEqual(self.send('get','/'+allowed['id']+'/shares').status_code,404)
        self.login(self.owner);self.assertEqual(self.send('delete','/'+allowed['id']+'/shares/'+grant['id'],{}).status_code,204)
        self.login(self.guest)
        self.assertEqual(self.send('get','?scope=shared').json['total'],0)
        self.assertEqual(self.send('get','/'+allowed['id']).status_code,404)
        self.assertEqual(self.send('put','/'+allowed['id'],{'revision':2,'document':changed}).status_code,404)
        with connection(self.guest) as c:self.assertIsNone(c.execute('SELECT id FROM resource_diagrams WHERE id=%s',(allowed['id'],)).fetchone())
    def test_unknown_email_without_mail_identity_configuration_fails_without_creating_grant(self):
        row=self.create()
        with patch.dict(os.environ,{'SMTP_HOST':'','INVITE_CLIENT_SECRET':''}):r=self.send('post','/'+row['id']+'/shares',{'email':'unknown@example.invalid'})
        self.assertEqual(r.status_code,503)
        self.assertEqual(self.send('get','/'+row['id']+'/shares').json['items'],[])
    def test_pending_onboarding_requires_matching_verified_subject(self):
        row=self.create();new='qa-new-'+uuid.uuid4().hex;email='pending-'+uuid.uuid4().hex+'@example.invalid'
        with patch('diagrams.IdentityProvider') as provider:
            provider.return_value.provision.return_value=(new,True)
            r=self.send('post','/'+row['id']+'/shares',{'email':email})
            self.assertEqual(r.status_code,201,r.data);self.assertEqual(r.json['status'],'pending');provider.return_value.send_onboarding.assert_called_once_with(new)
        sync_identity({'sub':self.stranger,'email':email,'email_verified':True})
        self.login(self.stranger);self.assertEqual(self.send('get','?scope=shared').json['total'],0)
        sync_identity({'sub':new,'email':email,'email_verified':False})
        self.login(new);self.assertEqual(self.send('get','?scope=shared').json['total'],0)
        sync_identity({'sub':new,'email':email,'email_verified':True})
        self.assertEqual(self.send('get','?scope=shared').json['total'],1)
        self.assertEqual(self.send('post',body={'name':'Forbidden'}).status_code,403)
    def test_shared_user_cannot_change_owner_or_group_even_with_direct_database_update(self):
        import psycopg
        row=self.create();self.share(row)
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with connection(self.guest) as c:c.execute('UPDATE resource_diagrams SET owner_sub=%s WHERE id=%s',(self.guest,row['id']))
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with connection(self.guest) as c:c.execute("INSERT INTO workspace_principals(subject,tier) VALUES(%s,'member')",(self.stranger,))
    def test_recipient_cannot_see_group_and_cannot_read_another_share_roster(self):
        f=self.send('post','/folders',{'name':'Private group'}).json
        row=self.send('post',body={'name':'Grouped private map','folder_id':f['id']}).json
        self.share(row);self.login(self.guest)
        self.assertIsNone(self.send('get','/'+row['id']).json['folder_id'])
        self.assertEqual(self.send('get','/folders').json['items'],[])
        self.assertEqual(self.send('get','?folder='+f['id']).json['total'],0)
    def test_invalid_email_and_duplicate_invitation_throttle(self):
        row=self.create()
        self.assertEqual(self.send('post','/'+row['id']+'/shares',{'email':'bad\nemail@host'}).status_code,400)
        self.share(row)
        self.assertEqual(self.send('post','/'+row['id']+'/shares',{'email':self.email}).status_code,429)

if __name__=='__main__':unittest.main()

class InvitationRetryTests(unittest.TestCase):
    def test_passwordless_pending_user_can_retry_without_unmanaged_attributes(self):
        from invitations import IdentityProvider
        provider=object.__new__(IdentityProvider)
        provider.find=lambda email:{'id':'qa-pending','enabled':True,'requiredActions':['UPDATE_PASSWORD','CONFIGURE_TOTP']}
        provider.call=lambda path:[]
        self.assertEqual(provider.provision('qa@example.invalid','qa-owner'),('qa-pending',True))
        self.assertEqual(provider.onboarding_actions,['UPDATE_PASSWORD','CONFIGURE_TOTP'])
    def test_existing_password_and_mfa_are_not_reset_by_sharing(self):
        from invitations import IdentityProvider
        provider=object.__new__(IdentityProvider)
        provider.find=lambda email:{'id':'qa-existing','enabled':True,'emailVerified':True,'requiredActions':['UPDATE_PASSWORD']}
        provider.call=lambda path:[{'type':'password'},{'type':'otp'}]
        self.assertEqual(provider.provision('qa@example.invalid','qa-owner'),('qa-existing',False))
        self.assertFalse(hasattr(provider,'onboarding_actions'))

    def test_unverified_existing_account_only_gets_email_verification(self):
        from invitations import IdentityProvider
        provider=object.__new__(IdentityProvider)
        provider.find=lambda email:{'id':'qa-unverified','enabled':True,'emailVerified':False,'requiredActions':[]}
        provider.call=lambda path:[{'type':'password'},{'type':'otp'}]
        self.assertEqual(provider.provision('qa@example.invalid','qa-owner'),('qa-unverified',True))
        self.assertEqual(provider.onboarding_actions,['VERIFY_EMAIL'])
