"""One-hour capabilities, isolated browser sessions, real RLS; disposable database only."""
import os,re,time,unittest,uuid
from server import app
from diagrams import connection

@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Disposable database required')
class TemporaryLinks(unittest.TestCase):
 def setUp(self):
  app.config['TESTING']=True
  self.owner='qa-link-'+uuid.uuid4().hex;self.client=app.test_client();self.visitor=app.test_client();self.password='QA-link-password-unique-2026'
  with connection(self.owner) as c:c.execute('SELECT qa_seed_member(%s)',(self.owner,))
  with self.client.session_transaction() as s:s.update(identity=dict(sub=self.owner,name='Owner'),expires_at=time.time()+7200,csrf='qa',session_policy='absolute-2h-v1')
  self.row=self.send(self.client,'post','',dict(name='Temporary QA',template_id='blank')).json;self.did=self.row['id']
  self.link=self.send(self.client,'post','/'+self.did+'/links',dict(password=self.password)).json
  self.path='/bienvenida/colaborar/';self.token=self.link['url'].split('#')[1]
 def tearDown(self):
  with connection(self.owner) as c:c.execute('DELETE FROM resource_diagrams WHERE id=%s',(self.did,))
 def send(self,client,method,path,body=None,visit=None):
  headers={'X-CSRF-Token':'qa','Content-Type':'application/json'}
  if visit:headers['X-Koodaria-Visit']=visit
  return getattr(client,method)('/bienvenida/api/diagrams'+path,json=body,headers=headers)
 def join(self,password=None):
  r=self.visitor.get(self.path);self.assertEqual(r.status_code,200)
  with self.visitor.session_transaction() as s:csrf=s['csrf']
  r=self.visitor.post(self.path,data=dict(token=self.token,csrf=csrf,name='QA Visitor',email='visitor@example.invalid',password=password or self.password),follow_redirects=True)
  if r.status_code==200:
   with self.visitor.session_transaction() as s:self.visit=next(iter(s['diagram_visits']));s['csrf']='qa'
  return r
 def test_join_scoped_edit_and_revoke(self):
  self.assertEqual(self.join('wrong-password').status_code,403);self.assertEqual(self.join().status_code,200)
  r=self.send(self.visitor,'get','/'+self.did,visit=self.visit);self.assertEqual(r.status_code,200,r.data)
  cid=str(uuid.uuid4());sync=self.send(self.visitor,'post','/'+self.did+'/collaboration/sync',dict(client_id=cid),self.visit);self.assertEqual(sync.status_code,200,sync.data);self.assertTrue(sync.json['can_edit'])
  changed=self.send(self.visitor,'post','/'+self.did+'/collaboration/operations',dict(client_id=cid,operation_id=str(uuid.uuid4()),base_revision=r.json['revision'],changes=[dict(collection='document',id=None,path=['name'],before=dict(exists=True,value='Temporary QA'),after=dict(exists=True,value='Edited by visitor'))]),self.visit)
  self.assertEqual(changed.status_code,200,changed.data)
  ownercid=str(uuid.uuid4());self.send(self.client,'post','/'+self.did+'/collaboration/sync',dict(client_id=ownercid))
  conflict=self.send(self.client,'post','/'+self.did+'/collaboration/operations',dict(client_id=ownercid,operation_id=str(uuid.uuid4()),base_revision=r.json['revision'],changes=[dict(collection='document',id=None,path=['name'],before=dict(exists=True,value='Temporary QA'),after=dict(exists=True,value='Conflicting edit'))]));self.assertEqual(conflict.status_code,409)
  self.assertEqual(self.send(self.visitor,'get','/'+self.did+'/comment-people',visit=self.visit).status_code,200)
  with connection(self.owner) as c:
   audit=c.execute('SELECT display_name FROM diagram_operations WHERE diagram_id=%s ORDER BY revision DESC LIMIT 1',(self.did,)).fetchone();self.assertEqual(audit['display_name'],'QA Visitor')
  for path in ('','/folders','/'+self.did+'/shares','/'+self.did+'/links','/'+str(uuid.uuid4())):
   self.assertEqual(self.send(self.visitor,'get',path,visit=self.visit).status_code,403,path)
  self.assertEqual(self.send(app.test_client(),'get','/'+self.did,visit=self.visit).status_code,403)
  records=self.send(self.client,'get','/'+self.did+'/links').json;self.assertEqual(records['visits'][0]['display_name'],'QA Visitor');self.assertEqual(records['visits'][0]['email'],'visitor@example.invalid')
  self.assertEqual(self.send(self.client,'delete','/'+self.did+'/links/'+self.link['id']).status_code,204)
  self.assertEqual(self.send(self.visitor,'get','/'+self.did,visit=self.visit).status_code,403);self.assertEqual(self.join().status_code,410)
 def test_secrets_expiry_csrf_and_owner_preservation(self):
  with connection(self.owner) as c:
   r=c.execute('SELECT * FROM diagram_links WHERE id=%s',(self.link['id'],)).fetchone();self.assertNotEqual(r['password_hash'],self.password);self.assertEqual(len(r['token_hash']),64);self.assertEqual((r['expires_at']-r['created_at']).total_seconds(),3600)
  self.assertEqual(self.visitor.post(self.path,data=dict(password=self.password)).status_code,403)
  self.assertEqual(self.join().status_code,200)
  with self.visitor.session_transaction() as s:
   self.assertNotIn('identity',s);s['diagram_visits'][self.visit]['expires_at']=time.time()-1;s.modified=True
  self.assertEqual(self.send(self.visitor,'get','/'+self.did,visit=self.visit).status_code,403)
  self.visitor=self.client;self.assertEqual(self.join().status_code,200)
  with self.client.session_transaction() as s:self.assertEqual(s['identity']['sub'],self.owner)
  with connection(self.owner) as c:c.execute("UPDATE diagram_links SET expires_at=now()-interval '1 second' WHERE id=%s",(self.link['id'],))
  self.assertEqual(self.send(self.visitor,'get','/'+self.did,visit=self.visit).status_code,403)

 def test_password_and_attempt_limits(self):
  self.assertEqual(self.send(self.client,'post','/'+self.did+'/links',dict(password='short')).status_code,400)
  for i in range(10):self.assertEqual(self.join('incorrect-password').status_code,403)
  self.assertEqual(self.join('incorrect-password').status_code,429)
