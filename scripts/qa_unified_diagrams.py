"""Synthetic browser/PostgreSQL QA for the unified diagram tool. No real identity or email."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');api=base+'/bienvenida/api/diagrams'
catalog=json.loads((root/'app/frontend/src/diagram-catalog.json').read_text())
report={'synthetic_identity_only':True,'checks':[],'states':[],'accessibility':[]}
sizes=[(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 context=b.new_context(viewport={'width':1440,'height':900});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/__qa/session');csrf=page.locator('meta[name=csrf-token]').get_attribute('content');headers={'X-CSRF-Token':csrf}
 while True:
  previous=context.request.get(api).json()['items']
  if not previous:break
  for item in previous:assert context.request.delete(api+'/'+item['id'],data={'revision':item['revision']},headers=headers).status==204
 # Every starter is stored atomically and can be reopened/exported, with fresh IDs.
 for t in catalog['templates']:
  result=context.request.post(api,data={'name':'QA '+t['title'],'template_id':t['id']},headers=headers);assert result.status==201,result.text();row=result.json();assert len(row['document']['nodes'])==len(t['nodes']);assert row['revision']==1
  assert context.request.get(api+'/'+row['id']).json()['document']==row['document']
  assert context.request.get(api+'/'+row['id']+'/pdf').body().startswith(b'%PDF')
 assert context.request.post(api,data={'name':'QA invalid','template_id':'invalid'},headers=headers).status==400
 report['checks'].append('all_templates_created_atomically_reopened_and_exported_as_pdf')
 page.goto(base+'/bienvenida/#/catalogo/observabilidad');page.locator('a.catalog-card').first.wait_for();assert page.get_by_role('heading',name='Diagramas',exact=True).count()==1;assert not page.get_by_role('heading',name='Mapeo de servicios',exact=True).count();assert not page.get_by_role('heading',name='Mapeo de dependencias',exact=True).count()
 page.locator('a.catalog-card[href="#/herramientas/diagramas"]').click();page.get_by_role('heading',name='Diagramas',exact=True).wait_for()
 for alias in ['mapeo-recursos','mapeo-servicios','mapeo-dependencias']:
  page.goto(base+'/bienvenida/#/herramientas/'+alias);page.wait_for_function('()=>location.hash==="#/herramientas/diagramas"');page.get_by_role('heading',name='Diagramas',exact=True).wait_for()
 report['checks'].append('one_catalog_tool_and_legacy_links_resolve_to_online_library')
 def geometry(view,w,h):
  dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],(view,w,h,dims)
  target=page.locator('dialog[open]') if view.startswith('template') else page.locator('.resource-palette')
  inner=target.evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inner[1]<=inner[0]+1,(view,w,h,inner)
  body=target.locator('.template-name-form' if view=='template-name' else '.template-body' if view=='templates' else '.palette-body');inside=body.evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inside[1]<=inside[0]+1,(view,w,h,inside)
  report['states'].append({'view':view,'theme':page.evaluate('document.documentElement.dataset.theme'),'width':w,'height':h,'no_document_or_panel_overflow':True})
 def axe(view,w):
  page.route('**/__qa/axe.js',lambda r:r.fulfill(path=str(root/'.artifacts/axe.min.js'),content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js')
  issues=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}');assert not issues,issues;report['accessibility'].append({'view':view,'width':w,'violations':issues})
 page.get_by_role('button',name='+ Nuevo diagrama',exact=True).click();d=page.locator('dialog[open]');d.get_by_role('button',name='Infraestructura',exact=False).first.click()
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for w,h in sizes:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(250);geometry('templates',w,h)
   if w in [1440,320]:axe('templates',w)
   page.screenshot(path=str(root/f'.artifacts/unified-templates-{theme}-{w}-{h}.png'))
 page.set_viewport_size({'width':1440,'height':900});d.get_by_role('button',name='Continuar',exact=True).click();d.get_by_label('Nombre del diagrama').fill('QA unified editor')
 for w,h in sizes:
  page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(100);geometry('template-name',w,h)
 page.set_viewport_size({'width':1440,'height':900});d.get_by_role('button',name='Crear diagrama',exact=True).click();page.locator('.react-flow').wait_for();assert page.locator('.react-flow__node').count()==4
 page.get_by_role('button',name='Añadir recurso',exact=True).click();palette=page.get_by_role('complementary',name='Biblioteca de recursos');palette.wait_for()
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for w,h in sizes:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(250);geometry('palette',w,h)
   if w in [1440,320]:axe('palette',w)
   page.screenshot(path=str(root/f'.artifacts/unified-palette-{theme}-{w}-{h}.png'))
   palette.get_by_label('Buscar recursos').fill('a');page.wait_for_timeout(100);geometry('palette-results',w,h)
   palette.get_by_label('Buscar recursos').fill('');page.wait_for_timeout(100)
 page.set_viewport_size({'width':1440,'height':900});palette.get_by_label('Buscar recursos').fill('Aplicación');palette.get_by_role('button',name='Aplicación',exact=True).click();assert page.locator('.react-flow__node').count()==5
 palette.get_by_label('Buscar recursos').fill('Base de datos');palette.get_by_role('button',name='Base de datos',exact=True).drag_to(page.locator('.react-flow__pane'),target_position={'x':650,'y':220});page.wait_for_function('()=>document.querySelectorAll(".react-flow__node").length===6')
 palette.get_by_role('button',name='Cerrar recursos').click();assert page.get_by_role('button',name='Añadir recurso').evaluate('(e)=>e===document.activeElement')
 page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")')
 row=next(x for x in context.request.get(api).json()['items'] if x['name']=='QA unified editor');doc=context.request.get(api+'/'+row['id']).json()['document'];assert len(doc['nodes'])==6 and any(n['data']['kind']=='aplicacion' for n in doc['nodes'])
 # A touch-sized interaction inserts by tap and dismisses the panel to expose the canvas.
 page.set_viewport_size({'width':390,'height':844});page.get_by_role('button',name='Añadir recurso').click();palette.get_by_label('Buscar recursos').fill('Nota');palette.get_by_role('button',name='Nota',exact=True).click();assert not palette.count();page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")')
 page.get_by_role('button',name='Mis diagramas',exact=True).click();page.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='QA unified editor').click();page.wait_for_function('()=>document.querySelectorAll(".react-flow__node").length===7');report['checks'].append('palette_search_click_native_drag_mobile_tap_save_and_reopen')
 guest_context=b.new_context(viewport={'width':390,'height':844});guest=guest_context.new_page();guest.goto(base+'/__qa/session?as=guest')
 grant=context.request.post(api+'/'+row['id']+'/shares',data={'email':'qa-guest-browser@example.invalid'},headers=headers);assert grant.status==201
 guest.goto(base+'/bienvenida/#/herramientas/diagramas');guest.get_by_role('button',name='Compartidos conmigo',exact=True).wait_for();assert not guest.get_by_role('button',name='+ Nuevo diagrama').count()
 guest.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='QA unified editor').click();guest.get_by_role('button',name='Añadir recurso').click();gp=guest.get_by_role('complementary',name='Biblioteca de recursos');gp.get_by_label('Buscar recursos').fill('API');gp.get_by_role('button',name='API',exact=True).click();guest.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")')
 assert len(context.request.get(api+'/'+row['id']).json()['document']['nodes'])==8
 guest_csrf=guest.locator('meta[name=csrf-token]').get_attribute('content');assert guest_context.request.post(api,data={'name':'Denied','template_id':'infrastructure'},headers={'X-CSRF-Token':guest_csrf}).status==403
 report['checks'].append('guest_uses_palette_only_on_shared_document_and_cannot_create_from_template')
 assert not errors,errors;report['browser_errors']=errors
 (root/'docs/evidence/unified-diagrams-report.json').write_text(json.dumps(report,indent=2)+'\n');b.close();print('Unified templates, online persistence, legacy routes, palette interactions and responsive accessibility PASS')
