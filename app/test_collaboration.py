"""Disposable DB only: real concurrent principals, no customer records or credentials."""
import copy,os,time,unittest,uuid
from unittest.mock import patch
from server import app
from diagrams import connection
from access import sync_identity
from collaboration import apply_changes

def change(collection,id,path,before,after):return dict(collection=collection,id=id,path=path,before=before,after=after)
def slot(v):return dict(exists=True,value=v)

class DeltaTests(unittest.TestCase):
 def test_disjoint_fields_and_conflict(self):
  d=dict(name='QA',nodes=[dict(id='n',data=dict(label='A',address=''))],edges=[])
  c=change('nodes','n',['data','label'],slot('A'),slot('B'))
  result,_=apply_changes(d,[c]);self.assertEqual(result['nodes'][0]['data']['label'],'B');self.assertEqual(d['nodes'][0]['data']['label'],'A')
  with self.assertRaises(Exception):apply_changes(result,[c])

 def test_edge_route_is_mutable_but_node_type_is_not(self):
  d=dict(name='QA',nodes=[dict(id='n',type='resource')],edges=[dict(id='e',type='smoothstep')])
  result,_=apply_changes(d,[change('edges','e',['type'],slot('smoothstep'),slot('default'))]);self.assertEqual(result['edges'][0]['type'],'default')
  with self.assertRaises(Exception):apply_changes(d,[change('nodes','n',['type'],slot('resource'),slot('resourceGroup'))])

@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Requires disposable database')
class CollaborationTests(unittest.TestCase):
 def setUp(self):
  app.config['TESTING']=True;self.client=app.test_client();suffix=uuid.uuid4().hex;self.owner='qa-collab-owner-'+suffix;self.guest='qa-collab-guest-'+suffix;self.email=suffix+'@example.invalid';self.a=str(uuid.uuid4());self.b=str(uuid.uuid4())
  with connection(self.owner) as c:c.execute('SELECT qa_seed_member(%s)',(self.owner,))
  sync_identity(dict(sub=self.guest,email=self.email,email_verified=True,name='QA Guest'));self.login(self.owner)
  self.row=self.send('post','',dict(name='QA collaboration',template_id='blank')).json;self.did=self.row['id']
  doc=dict(name='QA collaboration',nodes=[dict(id=k,type='resource',position=dict(x=i*400,y=0),data=dict(kind='virtual',label=k,server_instance={})) for i,k in enumerate(['a','b','child'])],edges=[])
  r=self.send('put','/'+self.did,dict(revision=self.row['revision'],document=doc));self.assertEqual(r.status_code,200,r.data)
  with patch('diagrams.notify_existing',return_value=False):self.grant=self.send('post','/'+self.did+'/shares',dict(email=self.email)).json
  self.row=self.send('get','/'+self.did).json
 def tearDown(self):
  with connection(self.owner) as c:c.execute('DELETE FROM resource_diagrams WHERE id=%s',(self.did,))
 def login(self,who):
  with self.client.session_transaction() as s:s.clear();s.update(identity=dict(sub=who,name='QA Owner' if who==self.owner else 'QA Guest'),expires_at=time.time()+7200,csrf='qa-collab-token',session_policy='absolute-2h-v1')
 def send(self,method,path,body=None):return getattr(self.client,method)('/bienvenida/api/diagrams'+path,json=body,headers={'X-CSRF-Token':'qa-collab-token'})
 def sync(self,cid,resource=None):return self.send('post','/'+self.did+'/collaboration/sync',dict(client_id=cid,resource_id=resource))
 def op(self,cid,changes,oid=None):
  self.sync(cid)
  return self.send('post','/'+self.did+'/collaboration/operations',dict(client_id=cid,operation_id=oid or str(uuid.uuid4()),base_revision=self.row['revision'],changes=changes))
 def edit(self,k,field,old,new):return change('nodes',k,['data',field],slot(old),slot(new))
 def test_disjoint_concurrent_edits_idempotency_and_same_field_conflict(self):
  ca=[self.edit('a','label','a','QA A')];oid=str(uuid.uuid4());self.assertEqual(self.op(self.a,ca,oid).status_code,200)
  self.login(self.guest);r=self.op(self.b,[self.edit('b','label','b','QA B')]);self.assertEqual(r.status_code,200,r.data)
  self.assertEqual([n['data']['label'] for n in r.json['document']['nodes']],['QA A','QA B','child'])
  r=self.op(self.b,[self.edit('a','label','a','Lost')]);self.assertEqual(r.status_code,409);self.assertEqual(r.json['error_code'],'KOD-COL-001')
  self.login(self.owner);r=self.op(self.a,ca,oid);self.assertEqual(r.status_code,200);self.assertTrue(r.json['duplicate']);self.assertEqual(r.json['revision'],4)
  self.assertEqual(self.send('get','/'+self.did+'/collaboration/history').json['items'][0]['actor'],'QA Guest')
 def test_lease_release_expiration_delete_and_trash_restore(self):
  self.login(self.guest);self.assertEqual(self.sync(self.b,'a').json['reservation']['resource_id'],'a')
  self.login(self.owner);self.assertEqual(self.sync(self.a,'a').json['reservation']['blocked_by'],'QA Guest')
  node=self.row['document']['nodes'][0];c=change('nodes','a',[],slot(node),dict(exists=False))
  self.assertEqual(self.op(self.a,[c]).status_code,409)
  self.login(self.guest)
  with connection(self.guest) as db:db.execute("UPDATE diagram_collaborators SET expires_at=now()-interval '1 second' WHERE client_id=%s",(self.b,))
  self.login(self.owner);r=self.op(self.a,[c]);self.assertEqual(r.status_code,200,r.data)
  rows=self.send('get','/'+self.did+'/collaboration/trash').json['items'];self.assertEqual(rows[0]['names'],['a'])
  self.assertEqual(self.send('post','/'+self.did+'/collaboration/trash/'+rows[0]['id']+'/restore',{}).status_code,200)
  self.assertEqual(len(self.send('get','/'+self.did).json['document']['nodes']),3)
 def test_readonly_and_revocation_on_open_session(self):
  self.login(self.guest);self.assertEqual(self.sync(self.b).status_code,200)
  self.login(self.owner);self.assertEqual(self.send('put','/'+self.did+'/shares/'+self.grant['id'],dict(permission='read')).status_code,200)
  self.login(self.guest);p=self.sync(self.b,'a');self.assertEqual(p.status_code,200);self.assertFalse(p.json['can_edit']);self.assertIsNone(p.json['reservation']['resource_id'])
  self.assertEqual(self.send('get','/'+self.did).json['access'],'viewer');self.assertEqual(self.op(self.b,[self.edit('a','label','a','No')]).status_code,403)
  self.login(self.owner);self.assertEqual(self.send('delete','/'+self.did+'/shares/'+self.grant['id'],{}).status_code,204)
  self.login(self.guest);self.assertEqual(self.sync(self.b).status_code,403);self.assertEqual(self.op(self.b,[self.edit('b','label','b','No')]).status_code,403)
 def test_batch_rolls_back_and_no_forged_session(self):
  r=self.op(self.a,[self.edit('a','label','a','First'),self.edit('b','label','stale','Other')]);self.assertEqual(r.status_code,409)
  self.assertEqual(self.send('get','/'+self.did).json['document']['nodes'][0]['data']['label'],'a')
  self.sync(self.a);self.login(self.guest);self.assertEqual(self.sync(self.a).status_code,403)
 def test_active_child_protects_parent_and_cycle_validation(self):
  edge=dict(id='host',source='a',target='child',relation='hosts');r=self.op(self.a,[change('edges','host',[],dict(exists=False),slot(edge))]);self.assertEqual(r.status_code,200,r.data)
  self.row=r.json;self.login(self.guest);self.sync(self.b,'child');self.login(self.owner)
  node=self.row['document']['nodes'][0]
  self.assertEqual(self.op(self.a,[change('nodes','a',[],slot(node),dict(exists=False))]).status_code,409)
  self.assertEqual(self.op(self.a,[change('edges','host',[],slot(self.row['document']['edges'][0]),dict(exists=False))]).status_code,409)
 def test_schema_publication_does_not_change_existing_instance(self):
  node=self.row['document']['nodes'][0];ref=node['data']['model_ref'];self.sync(self.a)
  # Another publication must not modify the model bound to this node.
  with connection(self.owner) as c:
   from component_models import latest
   current=latest(c,'servers',ensure=True)
  client=self.client
  response=client.post('/bienvenida/api/catalog/models/servers/fields',json=dict(revision=current['revision'],section='identification',field=dict(label='QA new field',description='QA only',format='text')),headers={'X-CSRF-Token':'qa-collab-token'})
  self.assertEqual(response.status_code,201,response.data)
  r=self.op(self.a,[self.edit('a','label','a','Still pinned')]);self.assertEqual(r.status_code,200,r.data);self.assertEqual(r.json['document']['nodes'][0]['data']['model_ref'],ref)

 def test_threads_serialize_disjoint_updates_without_lost_write(self):
  from concurrent.futures import ThreadPoolExecutor
  def worker(who,cid,node):
   with app.test_client() as client:
    with client.session_transaction() as sess:sess.update(identity=dict(sub=who,name='QA concurrent'),expires_at=time.time()+7200,csrf='parallel')
    base='/bienvenida/api/diagrams/'+self.did+'/collaboration';headers={'X-CSRF-Token':'parallel'}
    client.post(base+'/sync',json=dict(client_id=cid),headers=headers)
    response=client.post(base+'/operations',json=dict(client_id=cid,operation_id=str(uuid.uuid4()),base_revision=self.row['revision'],changes=[self.edit(node,'label',node,'Thread '+node)]),headers=headers)
    return response.status_code
  with ThreadPoolExecutor(max_workers=2) as executor:results=list(executor.map(lambda v:worker(*v),[(self.owner,self.a,'a'),(self.guest,self.b,'b')]))
  self.assertEqual(results,[200,200]);labels=[n['data']['label'] for n in self.send('get','/'+self.did).json['document']['nodes']];self.assertEqual(labels[:2],['Thread a','Thread b'])
 def test_unregistered_client_cannot_impersonate_another_lease(self):
  self.sync(self.a,'a');self.login(self.guest)
  r=self.send('post','/'+self.did+'/collaboration/operations',dict(client_id=self.a,operation_id=str(uuid.uuid4()),base_revision=self.row['revision'],changes=[self.edit('a','label','a','Forged')]))
  self.assertEqual(r.status_code,409)
 def test_legacy_writer_blocked_while_collaboration_active(self):
  self.sync(self.a)
  self.assertEqual(self.send('put','/'+self.did,dict(revision=self.row['revision'],document=self.row['document'])).status_code,409)

@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Requires disposable database')
class EditorToolsTests(unittest.TestCase):
 setUp=CollaborationTests.setUp
 tearDown=CollaborationTests.tearDown
 login=CollaborationTests.login
 send=CollaborationTests.send
 sync=CollaborationTests.sync
 op=CollaborationTests.op
 def test_flags_roundtrip_and_lock(self):
  r=self.op(self.a,[change('nodes','a',['data','positionLocked'],dict(exists=False),slot(True)),change('nodes','a',['data','collapsed'],dict(exists=False),slot(True))]);self.assertEqual(r.status_code,200,r.data)
  n=r.json['document']['nodes'][0];self.assertTrue(n['data']['positionLocked']);self.assertTrue(n['data']['collapsed'])
  r=self.op(self.a,[change('nodes','a',['position','x'],slot(0),slot(50))]);self.assertEqual(r.status_code,409,r.data)
 def test_comments_mentions_resolve_and_revoke(self):
  r=self.send('post','/'+self.did+'/comments',dict(anchor_type='node',anchor_id='a',body='Revisar backup',mentions=[self.guest]));self.assertEqual(r.status_code,201,r.data);comment=r.json['item']
  self.login(self.guest);r=self.send('get','/'+self.did+'/comments');self.assertEqual(len(r.json['items']),1)
  r=self.send('patch','/'+self.did+'/comments/'+comment['id'],dict(revision=1,resolved=True));self.assertEqual(r.status_code,200,r.data)
  r=self.send('patch','/'+self.did+'/comments/'+comment['id'],dict(revision=1,resolved=False));self.assertEqual(r.status_code,409)
  r=self.send('post','/'+self.did+'/comments',dict(anchor_type='edge',anchor_id='missing',body='Test',mentions=[]));self.assertEqual(r.status_code,400)
  self.login(self.owner);self.send('delete','/'+self.did+'/shares/'+self.grant['id'],{});self.login(self.guest);r=self.send('get','/'+self.did+'/comments');self.assertIn(r.status_code,[403,404])
