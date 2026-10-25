"""Operating standards against a disposable database; no real identity or mail."""
import os,time,uuid,unittest
from server import app
from diagrams import connection
from standards import CATALOG

@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Disposable database required')
class StandardsTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING']=True;self.client=app.test_client();self.owner='qa-std-'+uuid.uuid4().hex;self.other='qa-std-'+uuid.uuid4().hex;self.guest='qa-std-'+uuid.uuid4().hex
        for who in [self.owner,self.other]:
            with connection(who) as c:c.execute('SELECT qa_seed_member(%s)',(who,))
        self.login(self.owner)
    def login(self,who):
        with self.client.session_transaction() as s:s.clear();s.update(identity={'sub':who},expires_at=time.time()+7200,session_policy='absolute-2h-v1',csrf='qa-standard')
    def send(self,method,path='',body=None):return getattr(self.client,method)('/bienvenida/api/standards'+path,json=body,headers={'X-CSRF-Token':'qa-standard'})
    def map(self,method,path='',body=None):return getattr(self.client,method)('/bienvenida/api/diagrams'+path,json=body,headers={'X-CSRF-Token':'qa-standard'})
    def create(self):
        r=self.send('post',body={'name':'QA Linux','family':'linux'});self.assertEqual(r.status_code,201,r.data);return r.json
    def publish(self,row):
        r=self.send('post','/'+row['id']+'/publish',{'revision':row['revision']});self.assertEqual(r.status_code,201,r.data);return r.json
    def test_server_schema_exposes_the_same_control_catalog_as_validation(self):
        from standards import SERVER_MODEL,FUNCTIONS
        controls=next(s for s in SERVER_MODEL['sections'] if s['id']=='controls')['fields']
        self.assertEqual({f['id'] for f in controls},set(FUNCTIONS))

    def test_draft_publication_immutable_history_and_conflict(self):
        row=self.create();self.assertEqual(len(row['draft']['requirements']),16);self.assertEqual(self.send('get','/published').json['items'],[])
        one=self.publish(row);draft=one['draft'];draft['requirements'][0]['tool']='QA monitor'
        saved=self.send('put','/'+row['id'],{'revision':one['revision'],'definition':draft});self.assertEqual(saved.status_code,200)
        self.assertEqual(self.send('put','/'+row['id'],{'revision':one['revision'],'definition':draft}).status_code,409)
        two=self.publish(saved.json);self.assertEqual(two['published_version'],2)
        versions=self.send('get','/'+row['id']+'/versions').json['items'];self.assertEqual([v['version'] for v in versions],[2,1]);self.assertEqual(versions[1]['definition']['requirements'][0]['tool'],'')
        import psycopg
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with connection(self.owner) as c:c.execute('UPDATE resource_standard_versions SET definition=%s WHERE standard_id=%s',('{}',row['id']))
    def test_private_catalog_and_guest_cannot_publish(self):
        row=self.publish(self.create());self.login(self.other)
        self.assertEqual(self.send('get').json['items'],[]);self.assertEqual(self.send('get','/'+row['id']+'/versions').json['items'],[])
        self.assertEqual(self.send('post','/'+row['id']+'/publish',{'revision':row['revision']}).status_code,404)
        self.login(self.guest)
        self.assertEqual(self.send('get').status_code,403);self.assertEqual(self.send('post',body={'name':'Denied'}).status_code,403)
    def test_bound_snapshot_stays_pinned_and_unknown_and_legacy_save_preserves_it(self):
        row=self.publish(self.create());created=self.map('post',body={'name':'QA binding','template_id':'infrastructure','standard':{'id':row['id'],'version':1}});self.assertEqual(created.status_code,201,created.data)
        doc=created.json['document'];bound=[n for n in doc['nodes'] if n['data'].get('standard')];self.assertEqual(len(bound),2)
        self.assertTrue(all(c['status']=='unknown' for n in bound for c in n['data']['standard']['coverage']))
        edited=row['draft'];edited['requirements'][0]['tool']='Version 2';updated=self.send('put','/'+row['id'],{'revision':row['revision'],'definition':edited}).json;self.publish(updated)
        saved=self.map('get','/'+created.json['id']).json;self.assertEqual(saved['document']['nodes'][1]['data']['standard']['version'],1)
        for n in doc['nodes']:n['data'].pop('standard',None)
        self.assertEqual(self.map('put','/'+created.json['id'],{'revision':1,'document':doc}).status_code,200)
        self.assertTrue(any(n['data'].get('standard') for n in self.map('get','/'+created.json['id']).json['document']['nodes']))
    def test_shared_snapshot_edit_does_not_expose_catalog_or_allow_forged_reference(self):
        row=self.publish(self.create());created=self.map('post',body={'name':'QA shared','template_id':'infrastructure','standard':{'id':row['id'],'version':1}}).json
        from access import sync_identity
        sync_identity({'sub':self.guest,'email':'qa-'+uuid.uuid4().hex+'@example.invalid','email_verified':True})
        # Use verified recipient lookup through the same API, without sending mail.
        from unittest.mock import patch
        guest_email=None
        with connection(self.guest) as c:guest_email=c.execute('SELECT email FROM workspace_principals').fetchone()['email']
        with patch('diagrams.notify_existing',return_value=False):self.assertEqual(self.map('post','/'+created['id']+'/shares',{'email':guest_email}).status_code,201)
        self.login(self.guest);doc=self.map('get','/'+created['id']).json['document'];node=next(n for n in doc['nodes'] if n['data'].get('standard'));node['data']['standard']['coverage'][0].update(status='configured',evidence='QA evidence',source='verified');node['data']['standard']['definition']['name']='Forged'
        self.assertEqual(self.map('put','/'+created['id'],{'revision':1,'document':doc}).status_code,200)
        result=self.map('get','/'+created['id']).json['document'];bound=next(n for n in result['nodes'] if n['data'].get('standard'))['data']['standard'];self.assertEqual(bound['name'],'QA Linux');self.assertEqual(bound['coverage'][0]['source'],'declared')
        self.assertEqual(self.send('get','/published').status_code,403)
        node['data']['standard']['version']=2
        self.assertEqual(self.map('put','/'+created['id'],{'revision':2,'document':doc}).status_code,400)
    def test_server_instance_roundtrip_schema_authority_and_old_client(self):
        from standards import SERVER_MODEL
        created=self.map('post',body={'name':'QA instance','template_id':'blank'}).json
        doc=created['document'];doc['nodes']=[dict(id='qa-vm',type='resource',position=dict(x=0,y=0),data=dict(label='QA VM',kind='virtual',resource_schema={'sections':[]},server_instance={'identification':{'ci':'QA-CI-1','hostname':'qa.internal'},'controls':{'monitoring':{'status':'configured','evidence':'QA declared'}},'evidence':{'state':'Operativo'},'relationships':{'depends':'QA DNS'}}))]
        saved=self.map('put','/'+created['id'],{'revision':created['revision'],'document':doc});self.assertEqual(saved.status_code,200,saved.data)
        saved_doc=self.map('get','/'+created['id']).json['document'];data=saved_doc['nodes'][0]['data'];self.assertEqual(data['resource_schema']['sections'],SERVER_MODEL['sections']);self.assertEqual(data['server_instance']['identification']['ci'],'QA-CI-1')
        import copy
        doc=copy.deepcopy(saved_doc);doc['nodes'][0]['data'].pop('server_instance');doc['nodes'][0]['data']['label']='QA renamed'
        again=self.map('put','/'+created['id'],{'revision':saved.json['revision'],'document':doc});self.assertEqual(again.status_code,200,again.data);self.assertEqual(self.map('get','/'+created['id']).json['document']['nodes'][0]['data']['server_instance'],data['server_instance'])
        doc=self.map('get','/'+created['id']).json['document'];doc['nodes'][0]['data']['server_instance']['identification']['invented']='Bad'
        self.assertEqual(self.map('put','/'+created['id'],{'revision':again.json['revision'],'document':doc}).status_code,400)
        doc['nodes'][0]['data']['server_instance']={'identification':{'hostname':'x'*501}}
        self.assertEqual(self.map('put','/'+created['id'],{'revision':again.json['revision'],'document':doc}).status_code,400)

    def test_legacy_rules_adapt_but_undefined_instance_field_is_dropped(self):
        row=self.create();doc=row['draft'];policy=self.server_model();identity=policy['identification'];policy['identification']=[f for f in identity if f['id'] not in ['environment','criticality']]+[dict(id='context',level='required',rule='QA old rule')];doc['server_model']=policy
        saved=self.send('put','/'+row['id'],{'revision':row['revision'],'definition':doc});self.assertEqual(saved.status_code,200,saved.data)
        by_id={f['id']:f for f in saved.json['draft']['server_model']['identification']};self.assertEqual(by_id['environment']['rule'],'QA old rule');self.assertEqual(by_id['criticality']['rule'],'QA old rule')
        from standards import instance
        values=instance({'identification':{'context':'QA previous combined value','environment':'Producción','criticality':'Alta'}});self.assertNotIn('context',values['identification']);self.assertEqual(values['identification']['environment'],'Producción');self.assertEqual(values['identification']['criticality'],'Alta')

    def server_model(self):
        from standards import SERVER_MODEL
        return {s['id']:[dict(id=f['id'],level='required',rule='QA expected rule') for f in s['fields']] for s in SERVER_MODEL['sections'] if s['id']!='controls'}
    def test_server_model_publication_snapshot_and_legacy_preservation(self):
        row=self.create();doc=row['draft'];doc['server_model']=self.server_model();doc['requirements'][0].update(level='conditional',condition='Only production')
        saved=self.send('put','/'+row['id'],{'revision':row['revision'],'definition':doc});self.assertEqual(saved.status_code,200,saved.data)
        published=self.publish(saved.json)
        mapped=self.map('post',body={'name':'QA server model','template_id':'infrastructure','standard':{'id':row['id'],'version':1}});self.assertEqual(mapped.status_code,201,mapped.data)
        bound=next(n['data']['standard'] for n in mapped.json['document']['nodes'] if n['data'].get('standard'))
        self.assertEqual(bound['definition']['server_model'],doc['server_model']);self.assertEqual(bound['definition']['requirements'][0]['condition'],'Only production')
        legacy=published['draft'];legacy.pop('server_model')
        for control in legacy['requirements']:control.pop('condition',None)
        saved=self.send('put','/'+row['id'],{'revision':published['revision'],'definition':legacy});self.assertEqual(saved.status_code,200,saved.data)
        self.assertEqual(saved.json['draft']['server_model'],doc['server_model']);self.assertEqual(saved.json['draft']['requirements'][0]['condition'],'Only production')
        updated=saved.json['draft'];updated['server_model']['evidence'][0]['rule']='QA revised rule'
        saved=self.send('put','/'+row['id'],{'revision':saved.json['revision'],'definition':updated});self.assertEqual(saved.status_code,200)
        self.publish(saved.json);versions=self.send('get','/'+row['id']+'/versions').json['items'];self.assertEqual(versions[1]['definition']['server_model'],doc['server_model'])
    def test_server_model_validation_rejects_incomplete_duplicate_and_oversized_rules(self):
        row=self.create()
        import copy
        for invalid in ['missing','duplicate','oversized','unknown']:
            doc=copy.deepcopy(row['draft']);doc['server_model']=self.server_model()
            if invalid=='missing':doc['server_model']['identification'].pop()
            if invalid=='duplicate':doc['server_model']['identification'][1]=doc['server_model']['identification'][0]
            if invalid=='oversized':doc['server_model']['evidence'][0]['rule']='x'*501
            if invalid=='unknown':doc['server_model']['evidence'][0]['level']='pretend-verified'
            self.assertEqual(self.send('put','/'+row['id'],{'revision':row['revision'],'definition':doc}).status_code,400,invalid)
    def test_validation_rejects_missing_controls_and_bad_status(self):
        row=self.create();doc=row['draft'];doc['requirements']=[]
        self.assertEqual(self.send('put','/'+row['id'],{'revision':1,'definition':doc}).status_code,400)
        self.assertEqual(self.send('post',body={'name':'Bad','family':'arbitrary'}).status_code,400)
        self.assertEqual(self.client.post('/bienvenida/api/standards',json={'name':'No csrf'}).status_code,403)
