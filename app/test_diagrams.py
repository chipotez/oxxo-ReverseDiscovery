"""Integration tests against a disposable PostgreSQL database, never customer rows."""
import os
import time
import unittest
import uuid
from server import app
from diagrams import connection,validate,InvalidDiagram

class DiagramValidationTests(unittest.TestCase):
    def test_untrusted_document_rejected(self):
        for value in [None,[],{},dict(name='x',nodes=[{}],edges=[]),dict(name='x',nodes=[],edges=[{}])]:
            with self.assertRaises(InvalidDiagram):validate(value)
    def test_nonfinite_position_and_cross_group_rejected(self):
        node=dict(id='qa',type='resource',position=dict(x=float('nan'),y=0),data=dict(label='QA',kind='servidor'))
        with self.assertRaises(InvalidDiagram):validate(dict(name='QA',nodes=[node],edges=[]))
        node['position']['x']=0;node['parentId']='missing'
        with self.assertRaises(InvalidDiagram):validate(dict(name='QA',nodes=[node],edges=[]))

@unittest.skipUnless(os.environ.get('DIAGRAM_TEST_DATABASE')=='disposable','Requires explicitly disposable database')
class DiagramIntegrationTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING']=True
        self.client=app.test_client();self.owner='qa-'+str(uuid.uuid4());self.other='qa-'+str(uuid.uuid4());self.login(self.owner)
    def login(self,subject):
        with self.client.session_transaction() as s:s.update(identity={'sub':subject},expires_at=time.time()+300,csrf='qa-token')
    def tearDown(self):
        for owner in (self.owner,self.other):
            with connection(owner) as c:
                c.execute('DELETE FROM resource_diagrams WHERE owner_sub=%s',(owner,))
                c.execute('DELETE FROM diagram_folders WHERE owner_sub=%s',(owner,))
    def send(self,method,path='',value=None):return getattr(self.client,method)('/bienvenida/api/diagrams'+path,json=value,headers={'X-CSRF-Token':'qa-token'})
    def create(self):
        r=self.send('post',value={'name':'Diagrama QA'});self.assertEqual(r.status_code,201,r.data);return r.json
    def test_folder_bulk_move_filter_rename_delete_preserves_diagrams(self):
        folder=self.send('post','/folders',dict(name='Oracle Producción')).json
        self.assertEqual(self.send('post','/folders',dict(name='oracle producción')).status_code,409)
        a,b=self.create(),self.create()
        result=self.send('post','/move',dict(folder_id=folder['id'],items=[dict(id=x['id'],revision=x['revision']) for x in [a,b]]))
        self.assertEqual(result.json['moved'],2)
        self.assertEqual(self.send('get','?folder='+folder['id']).json['total'],2)
        self.assertEqual(self.send('get','?folder=none').json['total'],0)
        root=self.send('get','?folder=root').json
        self.assertEqual(root['total'],1);self.assertEqual(root['items'][0]['resources'],2)
        self.assertEqual(self.send('get','/'+a['id']).json['folder_id'],folder['id'])
        renamed=self.send('put','/folders/'+folder['id'],dict(name='Oracle RAC',revision=1))
        self.assertEqual(renamed.status_code,200)
        self.assertEqual(self.send('delete','/folders/'+folder['id'],dict(revision=2)).status_code,204)
        self.assertEqual(self.send('get','?folder=none').json['total'],2)
        self.assertIsNone(self.send('get','/'+a['id']).json['folder_id'])
        self.assertEqual(self.send('get','/'+b['id']).json['document'],b['document'])

    def test_folder_isolation_and_atomic_move_conflict(self):
        folder=self.send('post','/folders',dict(name='Privada QA')).json
        mine=self.create()
        self.login(self.other);other=self.create()
        self.assertEqual(self.send('get','/folders').json['items'],[])
        self.assertEqual(self.send('get','?folder='+folder['id']).status_code,404)
        self.assertEqual(self.send('post',value=dict(name='No autorizado',folder_id=folder['id'])).status_code,404)
        self.assertEqual(self.send('put','/folders/'+folder['id'],dict(name='x',revision=1)).status_code,409)
        self.assertEqual(self.send('delete','/folders/'+folder['id'],dict(revision=1)).status_code,409)
        self.assertEqual(self.send('post','/move',dict(folder_id=folder['id'],items=[dict(id=other['id'],revision=1)])).status_code,404)
        import psycopg
        with self.assertRaises(psycopg.errors.InsufficientPrivilege):
            with connection(self.other) as c:c.execute('UPDATE resource_diagrams SET folder_id=%s WHERE id=%s',(folder['id'],other['id']))
        self.login(self.owner)
        result=self.send('post','/move',dict(folder_id=folder['id'],items=[dict(id=mine['id'],revision=1),dict(id=other['id'],revision=1)]))
        self.assertEqual(result.status_code,409)
        self.assertIsNone(self.send('get','/'+mine['id']).json['folder_id'])
        self.assertEqual(self.send('post','/move',dict(folder_id=folder['id'],items=[dict(id=mine['id'],revision=99)])).status_code,409)
        created=self.send('post',value=dict(name='Dentro de carpeta',folder_id=folder['id']))
        self.assertEqual(created.status_code,201)
        self.assertEqual(created.json['folder_id'],folder['id'])

    def test_create_list_update_reopen_conflict_and_pdf(self):
        first=self.create();second=self.create();self.assertNotEqual(first['id'],second['id'])
        self.assertEqual(self.send('get').json['total'],2)
        document=dict(name='Plataforma QA',nodes=[dict(id='server',type='resource',position=dict(x=0,y=0),data=dict(label='Servidor sintético',kind='servidor',address='192.0.2.10',port='443 / HTTPS'))],edges=[])
        path='/'+first['id'];r=self.send('put',path,dict(revision=1,document=document));self.assertEqual(r.status_code,200,r.data);self.assertEqual(r.json['revision'],2)
        self.assertEqual(self.send('get',path).json['document'],document)
        self.assertEqual(self.send('put',path,dict(revision=1,document=document)).status_code,409)
        pdf=self.send('get',path+'/pdf');self.assertEqual(pdf.status_code,200);self.assertTrue(pdf.data.startswith(b'%PDF-'));self.assertEqual(pdf.mimetype,'application/pdf');self.assertIn('attachment',pdf.headers['Content-Disposition']);self.assertEqual(pdf.headers['Cache-Control'],'no-store')
        self.assertEqual(self.send('delete',path,dict(revision=1)).status_code,409)
        self.assertEqual(self.send('delete',path,dict(revision=2)).status_code,204)
        self.assertEqual(self.send('get',path).status_code,404)
    def test_other_subject_cannot_list_read_edit_delete_or_export(self):
        row=self.create();self.login(self.other);path='/'+row['id']
        self.assertEqual(self.send('get').json['total'],0)
        for endpoint in (path,path+'/pdf'):self.assertEqual(self.send('get',endpoint).status_code,404)
        self.assertEqual(self.send('put',path,dict(revision=1,document=row['document'])).status_code,404)
        self.assertEqual(self.send('delete',path,dict(revision=1)).status_code,409)
        # Database policies independently enforce isolation without an application WHERE.
        with connection(self.other) as c:self.assertIsNone(c.execute('SELECT id FROM resource_diagrams WHERE id=%s',(row['id'],)).fetchone())
    def test_session_and_csrf_required(self):
        row=self.create()
        self.assertEqual(self.client.post('/bienvenida/api/diagrams',json={'name':'x'}).status_code,403)
        with self.client.session_transaction() as s:s['expires_at']=0
        for method,path in [('get',''),('post',''),('get','/'+row['id']+'/pdf')]:self.assertEqual(self.send(method,path,dict(name='x')).status_code,401)
    def test_pagination_and_invalid_payload(self):
        for _ in range(9):self.create()
        one=self.send('get').json;two=self.send('get','?page=2').json
        self.assertEqual(len(one['items']),8);self.assertEqual(len(two['items']),1)
        self.assertTrue(set(v['id'] for v in one['items']).isdisjoint(v['id'] for v in two['items']))
        row=one['items'][0]
        self.assertEqual(self.send('put','/'+row['id'],dict(revision=1,document={'name':'x','nodes':[{}],'edges':[]})).status_code,400)
        self.assertEqual(self.send('get','?page=invalid').status_code,400)

if __name__=='__main__':unittest.main()
