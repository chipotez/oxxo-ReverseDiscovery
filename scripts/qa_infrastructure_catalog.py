import json,re
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'states':[],'checks':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.on('dialog',lambda d:(_ for _ in ()).throw(AssertionError('Unexpected native dialog '+d.message)))
 page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/estandares');page.get_by_role('heading',name='Estándares',level=1).wait_for()
 result=page.evaluate('''async()=>{let r=await fetch('/bienvenida/api/standards',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},body:JSON.stringify({name:'QA infraestructura '+Date.now(),family:'linux'})});if(!r.ok)throw Error(await r.text());return r.json()}''');name=result['name']
 def entry(label):return page.locator('.standards-tree-desktop').get_by_role('button',name=label,exact=True) if label=='Infraestructura' else page.locator('button.standard-entry').filter(has=page.get_by_role('heading',name=label,exact=True))
 def root():
  page.evaluate("location.hash='/catalogo'");page.get_by_role('heading',name='¿Qué quieres desarrollar?').wait_for();
  with page.expect_response(lambda r:r.url.endswith('/bienvenida/api/standards') and r.request.method=='GET'):page.evaluate("location.hash='/estandares'")
  entry('Infraestructura').wait_for();page.wait_for_timeout(80)
 def go(view):
  root()
  if view=='root':return
  entry('Infraestructura').click()
  if view=='categories':return
  entry('Cómputo').click()
  if view=='compute':return
  entry('Servidores').click();page.locator('.resource-toolbar').get_by_role('button',name='Definiciones',exact=True).click()
  if view=='servers':return
  # find synthetic definition with pagination
  for i in range(20):
   if entry(name).count():break
   page.get_by_role('navigation',name='Páginas de estándares').get_by_role('button').last.click()
  entry(name).click();page.get_by_label('Nombre de la definición',exact=True).wait_for()
  if view=='dialog':
   page.get_by_label('Responsable del estándar',exact=True) if False else None
   page.get_by_label('Nombre de la definición',exact=True).fill(name+' editado');page.get_by_role('button',name='Volver en estándares').click();page.get_by_role('dialog').wait_for()
 def check(theme,w,h,view):
  page.wait_for_timeout(120)
  dims=page.evaluate('''()=>{let els=[document.documentElement,...document.querySelectorAll('.standards-list-body,.standard-detail-body,dialog[open]')];return els.map(e=>({tag:e.tagName,sw:e.scrollWidth,cw:e.clientWidth,sh:e.scrollHeight,ch:e.clientHeight}));}''')
  for d in dims:assert d['sw']<=d['cw']+2 and d['sh']<=d['ch']+2,(theme,w,h,view,d)
  if view=='dialog':
   for text in ['Seguir editando','Salir sin guardar','Guardar y salir']:
    rect=page.get_by_role('button',name=text,exact=True).bounding_box();assert rect and rect['y']>=0 and rect['y']+rect['height']<=h,(text,rect,h)
  report['states'].append(dict(theme=theme,width=w,height=h,view=view,no_overflow=True))
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]:
   for view in ['root','categories','compute','servers','editor','dialog']:
    page.set_viewport_size({'width':1440,'height':900});go(view);page.set_viewport_size({'width':w,'height':h});check(theme,w,h,view)
    if (w,h)==(1440,900) and view in ['categories','dialog']:page.screenshot(path=f'.artifacts/infrastructure-{theme}-{view}.png')
    if view=='dialog':page.get_by_role('button',name='Salir sin guardar',exact=True).click();entry('Servidor Linux').wait_for()
 # Verify each domain and every subcategory, including paginated catalogue entries
 page.set_viewport_size({'width':1440,'height':900})
 catalog=json.loads(Path('app/frontend/src/component-catalog.json').read_text());by_kind={r['kind']:r for r in catalog['resources']}
 for category in catalog['categories']:
  for sub in category['children']:
   root();entry('Infraestructura').click()
   for i in range(3):
    if entry(category['label']).count():break
    page.get_by_role('navigation',name='Páginas de estándares').get_by_role('button').last.click()
   entry(category['label']).click();entry(sub['label']).click()
   if sub['id']=='servers':page.get_by_role('heading',name='Servidores',level=1).wait_for()
   else:page.get_by_role('heading',name=by_kind[sub['kinds'][0]]['label'],exact=True).wait_for()
 report['checks'].append('all_domains_subcategories_and_types_reachable')
 # cancel, save failure, save and leave, internal route guard, discard
 go('dialog');page.get_by_role('button',name='Seguir editando',exact=True).click();assert page.get_by_label('Nombre de la definición',exact=True).input_value()==name+' editado'
 page.get_by_role('button',name='Volver en estándares').click();page.route('**/bienvenida/api/standards/'+result['id'],lambda r:r.fulfill(status=500,content_type='application/json',body='{"error":"Fallo de prueba"}') if r.request.method=='PUT' else r.continue_());page.get_by_role('button',name='Guardar y salir',exact=True).click();page.get_by_role('dialog').get_by_role('alert').wait_for();assert page.get_by_role('dialog').is_visible();page.unroute('**/bienvenida/api/standards/'+result['id']);page.get_by_role('button',name='Guardar y salir',exact=True).click();entry(name+' editado').wait_for();name+=' editado'
 report['checks'].append('cancel_preserves_edits_failed_save_stays_open_successful_save_exits')
 go('editor');page.get_by_label('Nombre de la definición',exact=True).fill(name+' descarte');page.evaluate("location.hash='/catalogo/observabilidad/gobierno'");page.get_by_role('dialog').wait_for();page.get_by_role('button',name='Seguir editando',exact=True).click();page.wait_for_timeout(200);assert page.url.endswith('#/estandares');page.evaluate("location.hash='/catalogo/observabilidad/gobierno'");page.get_by_role('dialog').wait_for();page.get_by_role('button',name='Salir sin guardar',exact=True).click();page.get_by_role('heading',name='Gobierno',level=1).wait_for();stored=ctx.request.get(base+'/bienvenida/api/standards').json();assert next(x for x in stored['items'] if x['id']==result['id'])['name']==name
 report['checks'].append('sidebar_route_guard_cancel_and_discard_preserve_saved_data')
 assert not errors,errors;report['browser_errors']=errors;Path('docs/evidence/infrastructure-catalog-report.json').write_text(json.dumps(report,indent=2)+'\n');b.close();print('PASS',len(report['states']),'responsive states; taxonomy and save/discard navigation verified')
