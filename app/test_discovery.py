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

 def test_diagnostics_allowlist_and_json_validation(self):
  import json
  headers={'Content-Type':'application/json; charset=utf-8','X-RateLimit-Remaining':'42','Set-Cookie':'qa-sensitive-cookie','X-Datadog-Secret':'qa-hidden'}
  with patch('discovery.requests.Session') as session:
   client=session.return_value.__enter__.return_value;r=client.get.return_value.__enter__.return_value;r.status_code=200;r.headers=headers;r.iter_content.return_value=[b'{"valid":true}'];trace={}
   self.assertTrue(call_provider('datadoghq.com','/api/v1/validate',dict(api_key='qa-key-private',app_key='qa-app-private'),diagnostics=trace)['valid'])
   self.assertEqual(trace['http_status'],200);self.assertEqual(trace['response_headers']['X-RateLimit-Remaining'],42);self.assertEqual(trace['response_bytes'],14)
   for secret in ['qa-sensitive-cookie','qa-hidden','qa-key-private','qa-app-private','Set-Cookie']:self.assertNotIn(secret,json.dumps(trace))
   self.assertTrue(trace['checks']['https_verified']);self.assertTrue(trace['checks']['json_object']);self.assertIn('DD-API-KEY',trace['request_headers'])
   r.headers={'Content-Type':'text/html'}
   with self.assertRaises(Fault) as exc:call_provider('datadoghq.com','/api/v1/hosts',dict(api_key='qa',app_key='qa'),diagnostics={})
   self.assertEqual(exc.exception.code,'KOD-CON-005')
 def test_connectivity_401_is_not_authenticated_success(self):
  with patch('discovery.requests.Session') as session:
   client=session.return_value.__enter__.return_value;r=client.get.return_value.__enter__.return_value;r.status_code=401;r.headers={'Content-Type':'application/json'};trace={}
   self.assertEqual(call_provider('datadoghq.com','/api/v1/validate',diagnostics=trace),{})
   self.assertEqual(trace['http_status'],401);self.assertEqual(trace['request_headers'],['Accept']);self.assertTrue(trace['checks']['http_reachable'])
   with self.assertRaises(Fault) as exc:call_provider('datadoghq.com','/api/v1/validate',dict(api_key='qa',app_key='qa'),diagnostics={})
   self.assertEqual(exc.exception.code,'KOD-CON-002')
 def test_diagnostics_persist_for_failed_permission_step(self):
  row=self.create();cid='/'+row['id'];run=self.call('post',cid+'/test/start',{}).json
  def probe(stage,row,trace):
   trace.update(http_status=403,endpoint='/api/v1/hosts',method='GET',checks={'https_verified':True})
   raise Fault('KOD-CON-003')
  with patch('discovery.perform',side_effect=probe):r=self.call('post',cid+'/test/step',dict(run_id=run['run_id'],stage=0))
  self.assertEqual(r.status_code,400);stage=self.call('get').json['items'][0]['stages'][0];self.assertEqual(stage['diagnostics']['http_status'],403);self.assertFalse(stage['diagnostics']['checks']['response_contract'])

 def verified(self):
  row=self.create()
  with connection(self.owner) as c:c.execute("UPDATE discovery_connections SET status='saved' WHERE id=%s",(row['id'],))
  return row
 def test_capability_probe_persists_scope_and_host_records(self):
  row=self.verified();cid='/'+row['id'];listed=self.call('get',cid+'/capabilities');self.assertEqual(len(listed.json['items']),8)
  def provider(site,path,keys,params,diagnostics=None,accept_list=False):
   diagnostics.update(http_status=200,endpoint=path)
   return dict(host_list=[dict(id=123,name='qa-complete-host',meta=dict(platform='Linux',cpuCores=8),tags_by_source={'agent':['env:qa']},apps=['postgres'])],total_matching=605)
  with patch('discovery.call_provider',side_effect=provider) as remote:
   result=self.call('post',cid+'/capabilities/hosts/probe',{});self.assertEqual(result.json['status'],'available')
   result=self.call('get',cid+'/resources/hosts?query=qa-host&page=2&limit=5');self.assertEqual(result.status_code,200,result.json)
   self.assertEqual(result.json['items'][0]['meta']['cpuCores'],8);self.assertEqual(result.json['total'],605);self.assertTrue(result.json['has_more'])
   self.assertEqual(remote.call_args.args[3]['start'],10);self.assertEqual(remote.call_args.args[3]['filter'],'qa-host')
  self.assertEqual(self.call('get',cid+'/capabilities').json['items'][0]['status'],'available')
  self.login(self.other);self.assertEqual(self.call('get',cid+'/capabilities').status_code,404);self.assertEqual(self.call('get',cid+'/resources/hosts').status_code,404)
  self.login('qa-unknown-guest');self.assertEqual(self.call('get',cid+'/capabilities').status_code,403)
 def test_capability_denial_is_not_a_transport_failure(self):
  row=self.verified();cid='/'+row['id']
  def denied(site,path,keys,params,diagnostics=None,**kwargs):
   diagnostics['http_status']=403;raise Fault('KOD-CON-003')
  with patch('discovery.call_provider',side_effect=denied):
   result=self.call('post',cid+'/capabilities/users/probe',{});self.assertEqual(result.status_code,200);self.assertEqual(result.json['status'],'denied')
  self.assertEqual(self.call('get',cid+'/resources/users').status_code,403)
  with patch('discovery.call_provider',side_effect=Fault('KOD-CON-001')):
   result=self.call('post',cid+'/capabilities/apm/probe',{});self.assertEqual(result.json['status'],'unknown')
  self.assertEqual(self.call('post',cid+'/capabilities/arbitrary/probe',{}).status_code,400)
  self.assertEqual(self.call('get',cid+'/resources/hosts?limit=10000').status_code,400)
 def test_capabilities_invalidated_by_connection_change(self):
  row=self.verified();cid='/'+row['id']
  with patch('discovery.call_provider',return_value={'host_list':[]}):self.assertEqual(self.call('post',cid+'/capabilities/hosts/probe',{}).json['status'],'available')
  self.assertEqual(self.call('put',cid,dict(name=row['name'],site=row['site'],revision=row['revision'])).status_code,200)
  with connection(self.owner) as c:self.assertEqual(c.execute('SELECT count(*) AS n FROM discovery_capabilities WHERE connection_id=%s',(row['id'],)).fetchone()['n'],0)
  self.assertEqual(self.call('get',cid+'/capabilities').status_code,409)
 def test_api_collection_contracts_and_cursor(self):
  row=self.verified();cid='/'+row['id']
  with patch('discovery.call_provider',return_value=[]) as remote:
   self.assertEqual(self.call('post',cid+'/capabilities/monitors/probe',{}).json['status'],'available');self.assertTrue(remote.call_args.kwargs['accept_list'])
  with patch('discovery.call_provider',return_value={'wrong':[]}):self.assertEqual(self.call('post',cid+'/capabilities/logs/probe',{}).json['status'],'unknown')
  with patch('discovery.call_provider',return_value={'data':[]}):self.assertEqual(self.call('post',cid+'/capabilities/events/probe',{}).json['status'],'available')
  with patch('discovery.call_provider',return_value={'data':[{'id':'qa-event'}],'meta':{'page':{'after':'qa-cursor'}}}) as remote:
   result=self.call('get',cid+'/resources/events?cursor=before&limit=5');self.assertEqual(result.json['next_cursor'],'qa-cursor');self.assertTrue(result.json['has_more']);self.assertEqual(remote.call_args.args[3]['page[cursor]'],'before')
 def test_other_families_can_be_probed_when_hosts_denied(self):
  row=self.create();cid='/'+row['id']
  with connection(self.owner) as c:
   from psycopg.types.json import Jsonb
   c.execute("UPDATE discovery_connections SET status='failed',stages=%s WHERE id=%s",(Jsonb([{'status':'complete'},{'status':'complete'},{'status':'failed'}]),row['id']))
  with patch('discovery.call_provider',return_value={'data':[]}):self.assertEqual(self.call('post',cid+'/capabilities/apm/probe',{}).json['status'],'available')
