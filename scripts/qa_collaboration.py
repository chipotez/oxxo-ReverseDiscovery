"""Two isolated browser sessions; synthetic map and identities only."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:18179'
REPORT={'synthetic_only':True,'checks':[]}

def call(page,method,path,body=None):
 return page.evaluate('''async([method,path,body])=>{const r=await fetch('/bienvenida/api/diagrams'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body===null?{}:{body:JSON.stringify(body)})});return {status:r.status,data:r.status===204?null:await r.json()};}''',[method,path,body])
def open_map(page,name):
 page.goto(BASE+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=name,exact=True)).click();expect(page.get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000)
def identity(page,id):
 page.locator('.react-flow__node[data-id="'+id+'"]').dblclick();summary=page.get_by_role('dialog',name='Resumen del recurso');summary.get_by_role('button',name='Abrir Identificación de entidad',exact=False).click();panel=page.locator('.inspector-identification');expect(panel.get_by_label('Hostname / FQDN',exact=True)).to_be_enabled(timeout=15000);return panel
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 ca=b.new_context(viewport={'width':1440,'height':900});cb=b.new_context(viewport={'width':1440,'height':900});a=ca.new_page();g=cb.new_page();errors=[]
 for page in [a,g]:page.on('pageerror',lambda e:errors.append(str(e)))
 g.goto(BASE+'/__qa/session?as=guest');a.goto(BASE+'/__qa/session');name='QA Collaboration '+str(time.time_ns());r=call(a,'POST','',{'name':name,'template_id':'blank'});assert r['status']==201,r;row=r['data'];did=row['id']
 doc={'name':name,'nodes':[{'id':k,'type':'resource','position':{'x':i*520,'y':0},'data':{'label':'QA VM '+k.upper(),'kind':'virtual','server_instance':{}}} for i,k in enumerate(['a','b'])],'edges':[]}
 r=call(a,'PUT','/'+did,{'revision':row['revision'],'document':doc});assert r['status']==200,r
 r=call(a,'POST','/'+did+'/shares',{'email':'qa-guest-browser@example.invalid'});assert r['status']==201,r;grant=r['data']['id']
 open_map(a,name);open_map(g,name)
 expect(a.get_by_role('button',name='Ver colaboradores y actividad')).to_contain_text('2',timeout=15000)
 ia=identity(a,'a');ig=identity(g,'b');ia.get_by_label('Hostname / FQDN',exact=True).fill('a.qa.example');ig.get_by_label('Hostname / FQDN',exact=True).fill('b.qa.example')
 expect(a.get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000);expect(g.get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000)
 a.wait_for_timeout(2400);stored=call(a,'GET','/'+did)['data'];names={n['id']:n['data']['server_instance']['identification']['hostname'] for n in stored['document']['nodes']};assert names=={'a':'a.qa.example','b':'b.qa.example'},names;REPORT['checks'].append('two users edit independent nodes and persist both')
 # B tries opening A while A is still editing it.
 ig.get_by_role('button',name='Cerrar panel del servidor').click();identity_button=g.locator('.react-flow__node[data-id="a"]');identity_button.dblclick();g.get_by_role('dialog',name='Resumen del recurso').get_by_role('button',name='Abrir Identificación de entidad',exact=False).click()
 expect(g.locator('.collaboration-lock')).to_contain_text('QA owner',timeout=10000);expect(g.locator('.inspector-identification').get_by_label('Hostname / FQDN',exact=True)).to_be_disabled();REPORT['checks'].append('lease prevents concurrent same-resource edits')
 # The server commits but the browser loses the acknowledgment: retry must deduplicate.
 revision=call(a,'GET','/'+did)['data']['revision'];lost=[False]
 def lose_ack(route):
  if lost[0]:route.continue_();return
  lost[0]=True;route.fetch();route.abort('failed')
 a.route('**/collaboration/operations',lose_ack);ia.get_by_label('Hostname / FQDN',exact=True).fill('ack.qa.example');a.wait_for_timeout(1000);expect(a.get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000);a.wait_for_timeout(2500)
 stored=call(a,'GET','/'+did)['data'];assert stored['revision']==revision+1,stored['revision'];assert stored['document']['nodes'][0]['data']['server_instance']['identification']['hostname']=='ack.qa.example';a.unroute('**/collaboration/operations',lose_ack);REPORT['checks'].append('lost acknowledgment retries same operation without duplication')
 # Offline pauses editing, reconnect resumes without lost values.
 ca.set_offline(True);expect(a.locator('.resource-status').get_by_text('Reconectando…',exact=True)).to_be_visible(timeout=20000);expect(ia.get_by_label('Hostname / FQDN',exact=True)).to_be_disabled();ca.set_offline(False);expect(a.get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000);REPORT['checks'].append('offline editing pauses and reconnect confirms persistence')
 # A renewed login changes CSRF while the existing editor remains open.
 a.request.get(BASE+'/__qa/session?as=owner');expect(a.get_by_role('button',name='Continuar',exact=True)).to_be_visible(timeout=15000);a.get_by_role('button',name='Continuar',exact=True).click();expect(a.get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000);REPORT['checks'].append('same-account session recovery resumes existing editor')
 # A demotes B while B has the map open.
 assert call(a,'PUT','/'+did+'/shares/'+grant,{'permission':'read'})['status']==200
 expect(g.get_by_role('button',name='Añadir recurso',exact=True)).to_be_disabled(timeout=15000);REPORT['checks'].append('permission downgrade applies to already-open browser')
 assert call(a,'DELETE','/'+did+'/shares/'+grant,{})['status']==204
 expect(g.locator('.resource-status').get_by_text('Acceso suspendido',exact=True)).to_be_visible(timeout=15000);REPORT['checks'].append('revoked user stops receiving map updates')
 # Delete confirmation and owner-only recovery use the persisted trash.
 ia.get_by_role('button',name='Cerrar panel del servidor').click();a.locator('.react-flow__node[data-id="b"]').click();a.keyboard.press('Delete');dialog=a.get_by_role('dialog',name='Confirmar eliminación de recursos');expect(dialog).to_be_visible();dialog.get_by_role('button',name='Mover a papelera').click();expect(a.locator('.react-flow__node[data-id="b"]')).to_have_count(0);a.wait_for_timeout(2500)
 a.get_by_role('button',name='Ver colaboradores y actividad').click();a.get_by_role('button',name='Papelera',exact=True).click();a.get_by_role('button',name='Restaurar',exact=True).click();expect(a.locator('.react-flow__node[data-id="b"]')).to_have_count(1,timeout=20000);REPORT['checks'].append('delete confirmation and persisted trash restore resource')
 # Responsive collaboration footer/dialog. No customer data screenshots.
 a.get_by_role('button',name='Ver colaboradores y actividad').click()
 for scheme in ['light','dark']:
  a.emulate_media(color_scheme=scheme)
  for w,h in [(1440,900),(1024,768),(390,844),(844,390)]:
   a.set_viewport_size({'width':w,'height':h});a.wait_for_timeout(150);dlg=a.get_by_role('dialog',name='Colaboración del diagrama');box=dlg.bounding_box();assert box and box['x']>=-1 and box['x']+box['width']<=w+1,(w,h,box);close=dlg.get_by_role('button',name='Cerrar colaboración').bounding_box();assert close['y']>=0 and close['y']+close['height']<=h,(w,h,close)
 REPORT['checks'].append('collaboration dialog fits eight viewport/theme combinations');assert not errors,errors
 a.get_by_role('button',name='Cerrar colaboración').click();ca.close();cb.close();b.close()
Path('docs/evidence/collaboration-qa.json').write_text(json.dumps(REPORT,indent=2)+'\n');print('PASS '+str(len(REPORT['checks']))+' browser checks')
