"""Synthetic browser regression for an expired session on an already rendered page."""
import json
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
html=(root/'app/templates/welcome.html').read_text()
for key,value in {'name':'QA','first_name':'QA','initials':'QA','csrf':'qa-initial','subject':'qa-original','account_url':'/qa-account'}.items():html=html.replace('{{ '+key+' }}',value)
row=dict(id='dc4c1f64-5784-4bd2-8c6c-b87832f9af54',name='Diagrama QA',revision=1,document=dict(name='Diagrama QA',nodes=[],edges=[]))
state={'expired':True,'subject':'qa-original','csrf':'qa-initial','writes':0,'csrf_rejections':0}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 context=b.new_context(viewport={'width':1366,'height':768});errors=[]
 context.route('**/__qa/session-ui',lambda r:r.fulfill(body=html,content_type='text/html'))
 context.route('**/workspace-assets/*',lambda r:r.fulfill(path=str(root/'app/static'/r.request.url.split('/')[-1])))
 context.route('**/auth/login?**',lambda r:r.fulfill(body='<p>Proveedor sintético de acceso</p>',content_type='text/html'))
 def status(r):
  r.fulfill(status=401 if state['expired'] else 200,json={'subject':state['subject'],'csrf':state['csrf']})
 context.route('**/auth/session',status)
 def api(r):
  method=r.request.method
  if state['expired']:r.fulfill(status=401,json={'error':'La sesión venció.','code':'session_expired'});return
  if method=='PUT':
   if r.request.headers.get('x-csrf-token')!=state['csrf']:
    state['csrf_rejections']+=1;r.fulfill(status=403,json={'error':'CSRF','code':'csrf_invalid'});return
   state['writes']+=1;row['document']=r.request.post_data_json['document'];row['revision']+=1;r.fulfill(json={'revision':row['revision']});return
  if method=='POST':r.fulfill(status=201,json=row);return
  r.fulfill(json={'items':[],'total':0,'page':1,'page_size':8})
 context.route('**/bienvenida/api/diagrams**',api)
 context.route('**/bienvenida/api/diagrams/*',api)
 page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('https://koodaria.com/__qa/session-ui#/herramientas/mapeo-recursos');page.wait_for_url('**/auth/login?**')
 assert parse_qs(urlsplit(page.url).query)['next']==['/bienvenida/#/herramientas/mapeo-recursos']
 state['expired']=False
 page.goto('https://koodaria.com/__qa/session-ui#/herramientas/mapeo-recursos');page.get_by_role('button',name='+ Nuevo diagrama').click();d=page.locator('.resource-dialog');d.get_by_label('Nombre del diagrama').fill('Diagrama QA');d.get_by_role('button',name='Crear diagrama').click();page.locator('.react-flow').wait_for()
 def add(name):
  page.get_by_role('button',name='+ Añadir',exact=True).click();d.get_by_label('Nombre',exact=True).fill(name);d.get_by_role('button',name='Añadir',exact=True).click()
 state['expired']=True;add('Sin perder este recurso')
 page.get_by_role('link',name='Iniciar sesión ↗').wait_for();assert '/__qa/session-ui' in page.url
 with page.expect_popup() as popup:page.get_by_role('link',name='Iniciar sesión ↗').click()
 popup.value.wait_for_load_state();popup.value.close()
 state.update(expired=False,subject='qa-different',csrf='qa-after-login')
 page.get_by_role('button',name='Continuar',exact=True).click();page.get_by_text('Inicia sesión con la misma cuenta',exact=False).wait_for();assert state['writes']==0
 assert page.locator('.react-flow__node').count()==1
 state['subject']='qa-original';page.get_by_role('button',name='Continuar',exact=True).click();page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")',timeout=3000)
 assert state['writes']==1 and len(row['document']['nodes'])==1
 state['csrf']='qa-rotated-in-other-tab';add('Segundo recurso QA');page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")')
 assert state['csrf_rejections']==1 and state['writes']==2
 assert len(row['document']['nodes'])==2
 assert not errors,errors
 (root/'docs/evidence/session-recovery-report.json').write_text(json.dumps({'synthetic_identity_only':True,'safe_library_reauthentication':True,'destination_preserved':True,'unsaved_editor_retained':True,'different_subject_rejected':True,'new_csrf_resumes_save':True,'csrf_rotation_retry_once':True,'browser_errors':errors},indent=2)+'\n')
 b.close();print('Expired-session recovery, same-account guard and CSRF renewal passed.')
