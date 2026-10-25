"""Versioning and graph persistence against disposable PostgreSQL only."""
import os,time,uuid,unittest
from server import app
from diagrams import connection
@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Disposable database required')
class ComponentModelsTests(unittest.TestCase):
 def setUp(self):
  app.config['TESTING']=True;self.client=app.test_client();self.owner='qa-model-'+uuid.uuid4().hex;self.other='qa-model-'+uuid.uuid4().hex
  for who in [self.owner,self.other]:
   with connection(who) as c:c.execute('SELECT qa_seed_member(%s)',(who,))
  self.login(self.owner)
 def login(self,who):
  with self.client.session_transaction() as s:s.clear();s.update(identity={'sub':who},expires_at=time.time()+7200,session_policy='absolute-2h-v1',csrf='qa-model')
 def call(self,method,path,body=None):return getattr(self.client,method)(path,json=body,headers={'X-CSRF-Token':'qa-model'})
 def model(self,key='servers'):return self.call('get','/bienvenida/api/catalog/models/'+key).json
 def add(self,section='identification',fmt='text',key='servers',**extra):
  m=self.model(key);body=dict(revision=m['revision'],section=section,field=dict(label='QA '+uuid.uuid4().hex[:12],description='QA field description',format=fmt,required=True,**extra))
  r=self.call('post','/bienvenida/api/catalog/models/'+key+'/fields',body);self.assertEqual(r.status_code,201,r.json);return r.json
 def graph(self):
  r=self.call('post','/bienvenida/api/diagrams',dict(name='QA model graph',template_id='blank'));self.assertEqual(r.status_code,201,r.json);return r.json
 def save(self,row,doc):return self.call('put','/bienvenida/api/diagrams/'+row['id'],dict(revision=row['revision'],document=doc))
 def loaded(self,row):return self.call('get','/bienvenida/api/diagrams/'+row['id']).json
 def test_add_duplicate_conflict_and_tenant_isolation(self):
  m=self.add();self.assertEqual(m['version'],2);field=m['schema']['sections'][0]['fields'][-1];path='/bienvenida/api/catalog/models/servers/fields'
  r=self.call('post',path,dict(revision=m['revision'],section='identification',field=field));self.assertEqual(r.status_code,409);self.assertEqual(r.json['error_code'],'KOD-CAT-002');self.assertIn('reference',r.json)
  r=self.call('post',path,dict(revision=1,section='identification',field=dict(field,label='Another')));self.assertEqual(r.status_code,409);self.assertEqual(r.json['error_code'],'KOD-CAT-003')
  self.login(self.other);self.assertNotEqual(self.model()['id'],m['id'])
  row=self.graph();doc=dict(name=row['name'],nodes=[dict(id='qa',type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label='VM',model_ref=dict(id=m['id'],version=2)))],edges=[])
  r=self.save(row,doc);self.assertEqual(r.status_code,403);self.assertEqual(r.json['error_code'],'KOD-CAT-004')
 def test_pin_upgrade_and_typed_values_roundtrip(self):
  row=self.graph();doc=dict(name=row['name'],nodes=[dict(id='qa',type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label='VM',server_instance={'identification':{'hostname':'qa.example'}}))],edges=[])
  self.assertEqual(self.save(row,doc).status_code,200);baseline=self.loaded(row)
  m=self.add(fmt='number');fid=m['schema']['sections'][0]['fields'][-1]['id'];baseline['document']['nodes'][0]['data']['model_ref']=dict(id=m['id'],version=m['version']);baseline['document']['nodes'][0]['data']['server_instance']['identification'][fid]=42
  self.assertEqual(self.save(baseline,baseline['document']).status_code,200);saved=self.loaded(row);self.assertEqual(saved['document']['nodes'][0]['data']['server_instance']['identification'][fid],42)
  self.add(section='evidence',fmt='boolean')
  self.assertEqual(self.save(saved,saved['document']).status_code,200);pinned=self.loaded(row);self.assertEqual(pinned['document']['nodes'][0]['data']['model_ref']['version'],2)
  pinned['document']['nodes'][0]['data']['server_instance']['identification'][fid]='not a number'
  r=self.save(pinned,pinned['document']);self.assertEqual(r.status_code,400);self.assertEqual(r.json['error_code'],'KOD-DIA-001');self.assertEqual(self.loaded(row)['revision'],pinned['revision'])
 def test_existing_baseline_does_not_silently_upgrade(self):
  row=self.graph();doc=dict(name=row['name'],nodes=[dict(id='qa',type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label='VM'))],edges=[])
  self.assertEqual(self.save(row,doc).status_code,200);self.add();before=self.loaded(row)
  self.assertEqual(self.save(before,before['document']).status_code,200);self.assertEqual(self.loaded(row)['document']['nodes'][0]['data']['model_ref']['version'],1)
 def test_undo_model_upgrade_restores_baseline_without_custom_values(self):
  import copy
  row=self.graph();doc=dict(name=row['name'],nodes=[dict(id='qa',type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label='VM'))],edges=[])
  self.assertEqual(self.save(row,doc).status_code,200);baseline=copy.deepcopy(self.loaded(row)['document']);m=self.add(fmt='number');fid=m['schema']['sections'][0]['fields'][-1]['id'];current=self.loaded(row);data=current['document']['nodes'][0]['data'];data['model_ref']=dict(id=m['id'],version=m['version']);data['server_instance']={'identification':{fid:42}}
  self.assertEqual(self.save(current,current['document']).status_code,200);baseline['nodes'][0]['data']['server_instance']={};self.assertEqual(self.save(self.loaded(row),baseline).status_code,200);restored=self.loaded(row)['document']['nodes'][0]['data'];self.assertEqual(restored['model_ref']['version'],1);self.assertNotIn(fid,restored.get('server_instance',{}).get('identification',{}))
 def test_connection_ports_and_retarget_preserve_flat_graph(self):
  row=self.graph();doc=dict(name=row['name'],nodes=[dict(id=i,type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label=i)) for i in ['a','b','c']],edges=[dict(id='link',source='a',target='b',sourceHandle='east',targetHandle='east',relation='connected')])
  self.assertEqual(self.save(row,doc).status_code,200);current=self.loaded(row);current['document']['edges'][0]['source']='c';current['document']['edges'][0]['targetHandle']='south';self.assertEqual(self.save(current,current['document']).status_code,200);saved=self.loaded(row)['document'];self.assertEqual(saved['edges'][0]['targetHandle'],'south');self.assertTrue(all('parentId' not in n for n in saved['nodes']))
 def test_custom_control_and_architecture_relationship(self):
  m=self.add(section='controls');control=next(s for s in m['schema']['sections'] if s['id']=='controls')['fields'][-1]['id']
  m=self.add(section='relationships',fmt='reference');rel=next(s for s in m['schema']['sections'] if s['id']=='relationships')['fields'][-1]['id']
  row=self.graph();doc=dict(name=row['name'],nodes=[dict(id=i,type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label=i,model_ref=dict(id=m['id'],version=m['version']),server_instance={'controls':{control:{'status':'configured','evidence':'QA evidence'}}})) for i in ['a','b']],edges=[dict(id='rel',source='a',target='b',relation=rel)])
  self.assertEqual(self.save(row,doc).status_code,200);self.assertEqual(self.loaded(row)['document']['edges'][0]['relation'],rel)
 def test_nonserver_fields_boolean_select_date(self):
  for fmt,options,value in [('boolean',{},False),('select',{'options':['One','Two']},'Two'),('date',{},'2026-10-24')]:
   m=self.add(key='custom_service',fmt=fmt,**options);field=m['schema']['sections'][0]['fields'][-1]['id'];row=self.graph();doc=dict(name=row['name'],nodes=[dict(id='s',type='resource',position=dict(x=0,y=0),data=dict(kind='custom_service',label='Service',component_instance={'identification':{field:value}}))],edges=[])
   self.assertEqual(self.save(row,doc).status_code,200);self.assertEqual(self.loaded(row)['document']['nodes'][0]['data']['component_instance']['identification'][field],value)
 def test_unknown_fields_and_invalid_options_are_rejected(self):
  m=self.model();r=self.call('post','/bienvenida/api/catalog/models/servers/fields',dict(revision=m['revision'],section='identification',field=dict(label='Invalid',description='QA',format='select',options=['Same','Same'])));self.assertEqual(r.status_code,400);self.assertEqual(r.json['error_code'],'KOD-CAT-001')
 def test_organization_scope_and_serialized_concurrent_edits(self):
  from concurrent.futures import ThreadPoolExecutor
  org='qa-org-'+uuid.uuid4().hex
  with connection(self.owner) as c:
   c.execute('SELECT qa_model_organization(%s,%s)',(self.owner,org));c.execute('SELECT qa_model_organization(%s,%s)',(self.other,org))
  m=self.model();self.login(self.other);self.assertEqual(self.model()['id'],m['id']);self.login(self.owner)
  def submit(i):
   client=app.test_client()
   with client.session_transaction() as state:state.update(identity={'sub':self.owner},expires_at=time.time()+7200,session_policy='absolute-2h-v1',csrf='qa-model')
   return client.post('/bienvenida/api/catalog/models/servers/fields',headers={'X-CSRF-Token':'qa-model'},json=dict(revision=m['revision'],section='identification',field=dict(label='Concurrent '+str(i),description='QA concurrency',format='text'))).status_code
  with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(submit,[1,2]))
  self.assertCountEqual(results,[201,409]);self.assertEqual(self.model()['version'],2)
  with connection(self.owner) as c:c.execute('SELECT qa_model_organization(%s,%s)',(self.other,'qa-org-'+uuid.uuid4().hex))
  self.login(self.other);self.assertNotEqual(self.model()['id'],m['id'])
 def test_guest_edits_pinned_shared_model_without_catalog_permissions(self):
  from access import sync_identity
  from unittest.mock import patch
  guest='qa-guest-'+uuid.uuid4().hex;email=uuid.uuid4().hex+'@example.invalid';sync_identity(dict(sub=guest,email=email,email_verified=True,name='QA Guest'))
  m=self.add();fid=m['schema']['sections'][0]['fields'][-1]['id'];row=self.graph();doc=dict(name=row['name'],nodes=[dict(id='vm',type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label='VM',server_instance={'identification':{fid:'Owner value'}}))],edges=[])
  self.assertEqual(self.save(row,doc).status_code,200)
  with patch('diagrams.notify_existing',return_value=False):shared=self.call('post','/bienvenida/api/diagrams/'+row['id']+'/shares',dict(email=email))
  self.assertEqual(shared.status_code,201,shared.json);self.login(guest);self.assertEqual(self.call('get','/bienvenida/api/catalog/models/servers').status_code,403)
  saved=self.loaded(row);saved['document']['nodes'][0]['data']['server_instance']['identification'][fid]='Guest edit';self.assertEqual(self.save(saved,saved['document']).status_code,200)
  self.assertEqual(self.loaded(row)['document']['nodes'][0]['data']['server_instance']['identification'][fid],'Guest edit')
 def test_bends_roundtrip_validation_and_legacy_preservation(self):
  import copy
  row=self.graph();doc=dict(name=row['name'],nodes=[dict(id=i,type='resource',position=dict(x=0,y=0),data=dict(kind='virtual',label=i)) for i in ['a','b']],edges=[dict(id='edge',source='a',target='b',type='default',bends=[dict(x=0,y=-60),dict(x=40,y=120),dict(x=5,y=-90)])])
  self.assertEqual(self.save(row,doc).status_code,200);current=self.loaded(row);bends=copy.deepcopy(current['document']['edges'][0]['bends']);del current['document']['edges'][0]['bends'];self.assertEqual(self.save(current,current['document']).status_code,200);self.assertEqual(self.loaded(row)['document']['edges'][0]['bends'],bends)
  for bad in [[dict(x=0,y=0)], [dict(x=0,y=0),dict(x=True,y=0),dict(x=0,y=0)], [dict(x=0,y=0),dict(x=0,y=10001),dict(x=0,y=0)]]:
   current=self.loaded(row);current['document']['edges'][0]['bends']=bad;self.assertEqual(self.save(current,current['document']).status_code,400);self.assertEqual(self.loaded(row)['revision'],current['revision'])
 def test_canvas_pdf_authorization_revision_and_image_validation(self):
  import base64
  from io import BytesIO
  from PIL import Image
  image=Image.new('RGB',(100,60),'#2f6557');out=BytesIO();image.save(out,format='PNG');png='data:image/png;base64,'+base64.b64encode(out.getvalue()).decode();row=self.graph();path='/bienvenida/api/diagrams/'+row['id']+'/pdf'
  r=self.call('post',path,dict(revision=row['revision'],image=png));self.assertEqual(r.status_code,200);self.assertEqual(r.mimetype,'application/pdf');self.assertTrue(r.data.startswith(b'%PDF'))
  big=BytesIO();Image.frombytes('RGB',(768,768),os.urandom(768*768*3)).save(big,format='PNG');large='data:image/png;base64,'+base64.b64encode(big.getvalue()).decode();self.assertGreater(len(large),1500000);self.assertEqual(self.call('post',path,dict(revision=row['revision'],image=large)).status_code,200)
  r=self.call('post',path,dict(revision=0,image=png));self.assertEqual(r.status_code,409)
  for bad in ['data:image/svg+xml;base64,PHN2Zy8+', 'data:image/png;base64,bad', 'https://example.invalid/image.png']:
   r=self.call('post',path,dict(revision=row['revision'],image=bad));self.assertEqual(r.status_code,400,r.json);self.assertEqual(r.json['error_code'],'KOD-PDF-001')
  self.login(self.other);self.assertEqual(self.call('post',path,dict(revision=row['revision'],image=png)).status_code,404)
 def test_auth_error_has_stable_code_and_unique_references(self):
  with self.client.session_transaction() as s:s.clear()
  a=self.call('get','/bienvenida/api/catalog/models/servers');b=self.call('get','/bienvenida/api/catalog/models/servers');self.assertEqual(a.status_code,401);self.assertEqual(a.json['error_code'],'KOD-AUTH-001');self.assertNotEqual(a.json['reference'],b.json['reference'])
