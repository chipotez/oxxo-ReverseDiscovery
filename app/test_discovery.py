"""Disposable-DB connector contract. Provider calls mocked; no real keys or customer data."""
import os,time,uuid,unittest
from unittest.mock import patch,MagicMock
from cryptography.fernet import Fernet
from server import app
from diagrams import connection
from discovery import cipher,call_provider,perform
from faults import Fault
@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Disposable database required')
class DiscoveryTests(unittest.TestCase):
 def setUp(self):
  self.env=patch.dict(os.environ,DISCOVERY_ENCRYPTION_KEY=Fernet.generate_key().decode());self.env.start();self.addCleanup(self.env.stop)
  app.config['TESTING']=True;self.client=app.test_client();self.owner='qa-model-discovery-'+uuid.uuid4().hex;self.other=self.owner+'-other'
  for who in [self.owner,self.other]:
   with connection(who) as c:c.execute('SELECT qa_seed_member(%s)',(who,))
  self.login(self.owner)
 def login(self,who):
  with self.client.session_transaction() as s:s.clear();s.update(identity={'sub':who},expires_at=time.time()+7200,session_policy='absolute-2h-v1',csrf='qa-discovery')
 def call(self,method,path='',body=None):return getattr(self.client,method)('/bienvenida/api/discovery'+path,json=body,headers={'X-CSRF-Token':'qa-discovery','Content-Type':'application/json'})
 def create(self):
  r=self.call('post',body=dict(name='QA '+uuid.uuid4().hex,site='datadoghq.com',api_key='qa-api-key-placeholder',app_key='qa-app-key-placeholder'));self.assertEqual(r.status_code,201,r.json);return r.json
 def test_encryption_scope_guest_and_csrf(self):
  row=self.create();self.assertNotIn('credentials',row)
  with connection(self.owner) as c:
   stored=c.execute('SELECT credentials FROM discovery_connections WHERE id=%s',(row['id'],)).fetchone()['credentials'];self.assertNotIn('qa-api-key',stored);self.assertIn(b'qa-api-key',cipher().decrypt(stored.encode()))
  self.login(self.other);self.assertEqual(self.call('get').json['items'],[]);self.assertEqual(self.call('delete','/'+row['id']).status_code,404)
  self.login(self.owner);self.assertEqual(self.client.post('/bienvenida/api/discovery',json={}).status_code,403)
  self.login('qa-unknown-guest');self.assertEqual(self.call('get').status_code,403);self.assertEqual(self.call('post',body={}).status_code,403)
 def test_stages_revision_confirm_and_secret_retention(self):
  row=self.create();cid='/'+row['id'];self.assertEqual(self.call('post',cid+'/confirm',{}).status_code,409)
  row=self.call('put',cid,dict(name=row['name'],site=row['site'],revision=row['revision'])).json
  run=self.call('post',cid+'/test/start',{}).json
  with patch('discovery.perform',side_effect=[None,None,None,([dict(name='qa-host',external_id='1',tags=['env:test'],platform='Linux',source='Datadog')],1)]) as provider:
   self.assertEqual(self.call('post',cid+'/test/step',dict(run_id=run['run_id'],stage=2)).status_code,409)
   for i in range(4):
    r=self.call('post',cid+'/test/step',dict(run_id=run['run_id'],stage=i));self.assertEqual(r.status_code,200,r.json)
   self.assertEqual(provider.call_count,4)
  self.assertEqual(r.json['status'],'verified');self.assertEqual(r.json['sample_total'],1);self.assertEqual(self.call('post',cid+'/confirm',{}).json['status'],'saved')
  self.assertEqual(self.call('put',cid,dict(name='New',site=row['site'],revision=1)).status_code,409)
 def test_failed_stage_persists_without_secret(self):
  row=self.create();cid='/'+row['id'];run=self.call('post',cid+'/test/start',{}).json
  with patch('discovery.perform',side_effect=Fault('KOD-CON-003')):
   r=self.call('post',cid+'/test/step',dict(run_id=run['run_id'],stage=0))
  self.assertEqual(r.status_code,400);self.assertEqual(r.json['status'],'failed');self.assertEqual(r.json['error_code'],'KOD-CON-003');self.assertIn('reference',r.json);self.assertNotIn('credentials',r.json)
  self.assertEqual(self.call('get').json['items'][0]['status'],'failed')
 def test_site_allowlist_and_missing_cipher(self):
  self.assertEqual(self.call('post',body=dict(name='QA',site='http://127.0.0.1',api_key='qa-placeholder',app_key='qa-placeholder')).status_code,400)
  with patch.dict(os.environ,DISCOVERY_ENCRYPTION_KEY='invalid'):
   r=self.call('post',body=dict(name='QA',site='datadoghq.com',api_key='qa-placeholder',app_key='qa-placeholder'));self.assertEqual(r.status_code,503);self.assertEqual(r.json['error_code'],'KOD-CON-007')
 def test_http_bounds_no_redirects_and_response_codes(self):
  for status,expected in [(403,'KOD-CON-003'),(429,'KOD-CON-004'),(302,'KOD-CON-001')]:
   with patch('discovery.requests.Session') as session:
    client=session.return_value.__enter__.return_value;r=client.get.return_value.__enter__.return_value;r.status_code=status
    with self.assertRaises(Fault) as fault:call_provider('datadoghq.com','/api/v1/hosts',dict(api_key='qa',app_key='qa'))
    self.assertEqual(fault.exception.code,expected);self.assertFalse(client.trust_env);self.assertFalse(client.get.call_args.kwargs['allow_redirects'])
  with patch('discovery.requests.Session') as session:
   client=session.return_value.__enter__.return_value;r=client.get.return_value.__enter__.return_value;r.status_code=200;r.iter_content.return_value=[b'x'*1000001]
   with self.assertRaises(Fault) as fault:call_provider('datadoghq.com','/api/v1/hosts',dict(api_key='qa',app_key='qa'))
   self.assertEqual(fault.exception.code,'KOD-CON-005')
 def test_host_normalization(self):
  row=dict(site='datadoghq.com',credentials=cipher().encrypt(b'{"api_key":"qa","app_key":"qa"}').decode())
  with patch('discovery.call_provider',return_value=dict(host_list=[dict(id=9,name='qa-host',meta=dict(platform='Linux'),tags_by_source={'agent':['env:qa']})],total_matching=50)):
   hosts,total=perform(3,row);self.assertEqual(total,50);self.assertEqual(hosts[0]['tags'],['env:qa']);self.assertEqual(hosts[0]['platform'],'Linux')

 def test_shared_org_scope(self):
  org='qa-org-'+uuid.uuid4().hex
  with connection(self.owner) as c:
   c.execute('SELECT qa_model_organization(%s,%s)',(self.owner,org));c.execute('SELECT qa_model_organization(%s,%s)',(self.other,org))
  row=self.create();self.login(self.other);self.assertEqual(self.call('get').json['items'][0]['id'],row['id'])
