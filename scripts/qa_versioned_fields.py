"""Synthetic browser journey: publish a real field, preserve old nodes, upgrade and diagnose."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'synthetic_identity_only':True,'states':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 row=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA Fields '+Date.now(),template_id:'blank'})})).json();const r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:1,document:{name:c.name,nodes:[{id:'qa-vm',type:'resource',position:{x:0,y:0},data:{kind:'virtual',label:'QA VM'}}],edges:[]}})});if(!r.ok)throw Error(await r.text());return c}''')
 page.goto(base+'/bienvenida/#/estandares');tree=page.locator('.standards-tree-desktop');tree.get_by_role('button',name='Cómputo y plataformas',exact=True).click();tree.get_by_role('button',name='Servidores',exact=True).click();tree.get_by_role('button',name='Identificación de entidad',exact=True).click();add=page.get_by_role('button',name='Agregar campo',exact=False);add.wait_for();page.wait_for_timeout(500)
 label='QA RAM '+str(int(time.time()));add.click();dialog=page.get_by_role('dialog',name='Agregar campo',exact=True)
 def advance():dialog.get_by_role('button',name='Continuar',exact=True).click()
 dialog.get_by_label('Nombre del campo',exact=True).fill(label);dialog.get_by_label('Descripción breve',exact=True).fill('Memoria asignada para esta prueba sintética.');advance();dialog.get_by_label('Formato',exact=True).select_option('number');advance();dialog.get_by_role('checkbox').check();dialog.get_by_role('button',name='Guardar campo',exact=True).click();dialog.wait_for(state='hidden');page.get_by_text('Campo guardado',exact=False).wait_for()
 current=page.request.get(base+'/bienvenida/api/catalog/models/servers').json();field=next(f for s in current['schema']['sections'] if s['id']=='identification' for f in s['fields'] if f['label']==label);report['version']=current['version']
 # A duplicate is a real API failure, not a simulated toast. The original form stays intact.
 add.click();dialog.get_by_label('Nombre del campo',exact=True).fill(label);dialog.get_by_label('Descripción breve',exact=True).fill('QA duplicate');advance();advance();dialog.get_by_role('button',name='Guardar campo',exact=True).click();fault=page.get_by_role('dialog',name='No se pudo completar la operación',exact=True);fault.wait_for();assert 'KOD-CAT-002' in fault.inner_text();assert fault.locator('dd').nth(1).inner_text();page.screenshot(path='.artifacts/nesting/field-error.png');fault.get_by_role('button',name='Entendido',exact=True).click();dialog.get_by_role('button',name='Atrás',exact=True).click();dialog.get_by_role('button',name='Atrás',exact=True).click();assert dialog.get_by_label('Nombre del campo',exact=True).input_value()==label;dialog.get_by_role('button',name='Cancelar',exact=True).click()
 # All steps fit both themes and available width/height without shrinking the interface.
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(390,844),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});add.click();dialog.get_by_label('Nombre del campo',exact=True).fill('QA responsive');dialog.get_by_label('Descripción breve',exact=True).fill('QA explanation')
   for step in range(3):
    page.wait_for_timeout(100);bounds=dialog.evaluate('(e)=>({top:e.getBoundingClientRect().top,bottom:e.getBoundingClientRect().bottom,client:e.clientHeight,scroll:e.scrollHeight})');assert bounds['top']>=0 and bounds['bottom']<=h+1 and bounds['scroll']<=bounds['client']+2,(w,h,step,bounds);report['states'].append(dict(theme=theme,width=w,height=h,step=step+1))
    if step<2:advance()
   dialog.get_by_role('button',name='Cancelar',exact=True).click()
 page.set_viewport_size({'width':1440,'height':900});page.evaluate('document.documentElement.dataset.theme="light"')
 def open_map():
  page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=row['name'],exact=True)).click();page.locator('.react-flow__node[data-id="qa-vm"]').wait_for();page.wait_for_timeout(200)
 open_map();page.locator('.react-flow__node[data-id="qa-vm"] header').dblclick();summary=page.get_by_role('dialog',name='Resumen del recurso');summary.wait_for();summary.get_by_role('button',name='Actualizar campos a v'+str(current['version']),exact=True).click();page.wait_for_timeout(1200);summary.get_by_role('button',name='Abrir Identificación de entidad de QA VM',exact=True).click();identity=page.get_by_role('dialog',name='Identificación de entidad',exact=True);identity.wait_for();page.wait_for_timeout(600)
 for i in range(10):
  if identity.get_by_label(label,exact=True).count():break
  identity.get_by_role('button',name='Campos siguientes',exact=True).click()
 identity.get_by_label(label,exact=True).fill('256');page.wait_for_timeout(1300);saved=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json();data=saved['document']['nodes'][0]['data'];assert data['server_instance']['identification'][field['id']]==256;assert data['model_ref']['version']==current['version'];page.screenshot(path='.artifacts/nesting/field-form.png')
 page.reload();open_map();assert page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()['document']['nodes'][0]['data']['server_instance']['identification'][field['id']]==256
 assert not errors,errors;report.update(browser_errors=errors,published_field=True,duplicate_modal=True,input_preserved=True,explicit_upgrade=True,typed_value_roundtrip=True);Path('docs/evidence/versioned-fields-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS persistent field, version pin/upgrade, typed roundtrip, real coded error and 18 responsive steps');b.close()
