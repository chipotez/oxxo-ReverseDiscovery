"""Real browser + PostgreSQL QA via an SSH-only disposable test harness.
The harness and synthetic session endpoint are never deployed to production.
"""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from pypdf import PdfReader
root=Path(__file__).resolve().parents[1]
base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');api=base+'/bienvenida/api/diagrams';report={'synthetic_identity_only':True,'real_postgresql_disposable_database':True,'checks':[],'states':[],'accessibility':[]}
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 context=browser.new_context(viewport={'width':1440,'height':900},accept_downloads=True)
 page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/__qa/session');page.wait_for_selector('.catalog-card')
 token=page.locator('meta[name=csrf-token]').get_attribute('content');headers={'X-CSRF-Token':token}
 while True:
  rows=context.request.get(api).json()
  if not rows['items']:break
  for row in rows['items']:context.request.delete(api+'/'+row['id'],data={'revision':row['revision']},headers=headers)
 page.goto(base+'/bienvenida/#/catalogo/observabilidad');page.locator('a[href="#/herramientas/mapeo-recursos"]').click();page.get_by_role('button',name='+ Nuevo diagrama',exact=True).wait_for();page.wait_for_timeout(400)
 def create(name):
  page.get_by_role('button',name='+ Nuevo diagrama',exact=True).click();dlg=page.locator('.resource-dialog');dlg.get_by_label('Nombre del diagrama').fill(name);dlg.get_by_role('button',name='Crear diagrama',exact=True).click();page.locator('.react-flow').wait_for()
 def saved():page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")',timeout=15000)
 def add(name,kind):
  page.get_by_role('button',name='+ Añadir',exact=True).click();dlg=page.locator('.resource-dialog');dlg.get_by_label('Nombre',exact=True).fill(name);dlg.locator('select[name=kind]').select_option(kind);dlg.get_by_role('button',name='Añadir',exact=True).click();page.wait_for_timeout(200)
 create('Pagos QA');add('Origen QA','origen');add('Servidor QA','servidor')
 source=page.locator('.react-flow__node').filter(has_text='Origen QA');target=page.locator('.react-flow__node').filter(has_text='Servidor QA')
 a=source.locator('.source').bounding_box();z=target.locator('.target').bounding_box();page.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2);page.mouse.down();page.mouse.move(z['x']+z['width']/2,z['y']+z['height']/2,steps=15);page.mouse.up();page.locator('.react-flow__edge').wait_for(state='attached')
 target.dblclick();page.locator('.resource-properties').get_by_label('IP o nombre DNS').fill('192.0.2.10');page.locator('.resource-properties').get_by_label('Puerto / protocolo').fill('443 / HTTPS');page.get_by_role('button',name='Cerrar propiedades').click();saved()
 report['checks'].append('create_connect_edit_autosave')
 page.reload();page.get_by_role('button',name='Abrir diagrama',exact=False).first.wait_for();page.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='Pagos QA').click();page.locator('.react-flow__node').filter(has_text='192.0.2.10').wait_for();assert page.locator('.react-flow__edge').count()==1;report['checks'].append('reopen_after_browser_reload')
 with page.expect_download() as d:page.get_by_role('button',name='PDF',exact=True).click()
 path=root/'.artifacts/online-diagrams-qa.pdf';d.value.save_as(path);reader=PdfReader(str(path));assert len(reader.pages)>=2;text='\n'.join(pg.extract_text() for pg in reader.pages);assert '192.0.2.10' in text and 'Origen QA' in text;report['checks'].append('pdf_includes_saved_resources_and_connections')
 # A failed write preserves the canvas; explicit retry persists it.
 def fail_write(route):
  if route.request.method=='PUT':route.fulfill(status=503,json={'error':'Conexión de prueba interrumpida. Tus cambios siguen aquí.'})
  else:route.continue_()
 page.route('**/bienvenida/api/diagrams/*',fail_write);add('Pendiente QA','datos');page.locator('.diagram-save-error').wait_for();assert page.locator('.react-flow__node').filter(has_text='Pendiente QA').count()==1
 page.unroute('**/bienvenida/api/diagrams/*',fail_write);page.get_by_role('button',name='Reintentar',exact=True).click();saved();report['checks'].append('failed_save_retains_changes_and_retry_works')
 # Second stale tab cannot overwrite a newer revision.
 other=context.new_page();other.goto(base+'/bienvenida/#/herramientas/mapeo-recursos');other.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='Pagos QA').click();other.locator('.react-flow').wait_for();other.wait_for_timeout(300)
 add('Cambio primera pestaña','externo');saved()
 other.get_by_role('button',name='+ Añadir',exact=True).click();dlg=other.locator('.resource-dialog');dlg.get_by_label('Nombre',exact=True).fill('Cambio segunda pestaña');dlg.get_by_role('button',name='Añadir',exact=True).click();other.locator('.diagram-save-error').wait_for();assert 'otra pestaña' in other.locator('.diagram-save-error').inner_text()
 other.get_by_role('button',name='Guardar como copia').click();other.wait_for_function('()=>document.querySelector("h1")?.textContent.includes("copia")');other.wait_for_timeout(400);other.close();report['checks'].append('concurrent_conflict_and_save_as_copy')
 page.get_by_role('button',name='Mis diagramas',exact=True).click();page.get_by_role('button',name='+ Nuevo diagrama',exact=True).wait_for();create('Segundo mapa QA');assert page.locator('.react-flow__node').count()==0;page.get_by_role('button',name='Mis diagramas',exact=True).click();page.wait_for_selector('.diagram-open');page.wait_for_function('()=>document.querySelectorAll(".diagram-open").length===3');report['checks'].append('multiple_independent_diagrams')
 # Fill the library so pagination is exercised at every tested viewport.
 for i in range(6):assert context.request.post(api,data={'name':f'Diagrama adicional QA {i+1}'},headers=headers).status==201
 page.reload();page.wait_for_selector('.diagram-open');page.wait_for_timeout(300)
 def axe():
  return page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}')
 page.route('**/__qa/axe.js',lambda route:route.fulfill(path=str(root/'.artifacts/axe.min.js'),content_type='application/javascript'))
 page.add_script_tag(url=base+'/__qa/axe.js')
 sizes=[(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for w,h in sizes:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(550)
   dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],('library',theme,w,h,dims)
   inner=page.locator('.diagram-library-body').evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inner[1]<=inner[0]+1,('library',theme,w,h,inner)
   report['states'].append(dict(view='library',theme=theme,width=w,height=h,no_document_or_panel_overflow=True))
   if w in [1440,320]:
    issues=axe();assert not issues,issues;report['accessibility'].append(dict(view='library',theme=theme,width=w,violations=issues))
   page.screenshot(path=str(root/f'.artifacts/diagram-library-{theme}-{w}-{h}.png'))
 page.set_viewport_size({'width':1440,'height':900});page.wait_for_timeout(500)
 # Use the most recently changed original map, found through API; not a real customer map.
 allrows=context.request.get(api+'?page_size=8').json()['items']+context.request.get(api+'?page=2&page_size=8').json()['items'];original=next(r for r in allrows if r['name']=='Pagos QA')
 # A list page is finite; open via its own visible card after sorting by updating that same map.
 document=context.request.get(api+'/'+original['id']).json();context.request.put(api+'/'+original['id'],data={'revision':document['revision'],'document':document['document']},headers=headers)
 page.reload();page.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='Pagos QA').click();page.locator('.react-flow').wait_for();page.locator('.react-flow__node').filter(has_text='Servidor QA').dblclick();page.add_script_tag(url=base+'/__qa/axe.js')
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for w,h in sizes:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150)
   dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],('editor',theme,w,h,dims)
   inner=page.locator('.resource-properties').evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inner[1]<=inner[0]+1,('editor',theme,w,h,inner)
   report['states'].append(dict(view='editor_properties',theme=theme,width=w,height=h,no_document_or_panel_overflow=True))
   if w in [1440,320]:
    issues=axe();assert not issues,issues;report['accessibility'].append(dict(view='editor',theme=theme,width=w,violations=issues))
   page.screenshot(path=str(root/f'.artifacts/online-editor-{theme}-{w}-{h}.png'))
 assert not errors,errors;report['browser_errors']=errors
 (root/'docs/evidence/diagrams-online-report.json').write_text(json.dumps(report,indent=2)+'\n')
 browser.close();print('Online diagram workflows, PostgreSQL persistence, PDF, conflict recovery and responsive checks passed.')
