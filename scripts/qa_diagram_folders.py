"""Folder browser QA against the disposable PostgreSQL instance; synthetic maps only."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');api=base+'/bienvenida/api/diagrams'
report={'synthetic_identity_only':True,'real_postgresql_disposable_database':True,'checks':[],'states':[],'accessibility':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);context=b.new_context(viewport={'width':1440,'height':900});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/__qa/session');csrf=page.locator('meta[name=csrf-token]').get_attribute('content');headers={'X-CSRF-Token':csrf}
 while True:
  rows=context.request.get(api).json()['items']
  if not rows:break
  for row in rows:assert context.request.delete(api+'/'+row['id'],data={'revision':row['revision']},headers=headers).status==204
 for f in context.request.get(api+'/folders').json()['items']:assert context.request.delete(api+'/folders/'+f['id'],data={'revision':f['revision']},headers=headers).status==204
 page.goto(base+'/bienvenida/#/herramientas/mapeo-recursos');page.get_by_role('button',name='+ Nueva carpeta',exact=True).wait_for()
 def dialog():return page.locator('dialog[open]')
 def create_map(name):
  page.get_by_role('button',name='+ Nuevo diagrama',exact=True).click();dialog().get_by_label('Nombre del diagrama').fill(name);dialog().get_by_role('button',name='Crear diagrama',exact=True).click();page.locator('.react-flow').wait_for();page.get_by_role('button',name='Mis diagramas',exact=True).click();page.get_by_role('button',name='+ Nueva carpeta').wait_for()
 create_map('Oracle QA 1');create_map('Oracle QA 2')
 page.get_by_role('button',name='+ Nueva carpeta',exact=True).click();dialog().get_by_label('Nombre de la carpeta').fill('Oracle · Producción QA');dialog().get_by_role('button',name='Crear carpeta',exact=True).click();page.locator('dialog[open]').wait_for(state='hidden')
 page.get_by_role('button',name='Abrir carpeta',exact=False).filter(has_text='Oracle · Producción QA').wait_for()
 page.get_by_label('Seleccionar Oracle QA 1',exact=True).check();page.get_by_label('Seleccionar Oracle QA 2',exact=True).check();page.get_by_role('button',name='Mover (2)',exact=True).click();dialog().get_by_label('Carpeta de destino').select_option(label='Oracle · Producción QA');dialog().get_by_role('button',name='Mover',exact=True).click();page.locator('dialog[open]').wait_for(state='hidden')
 page.get_by_role('button',name='Abrir carpeta',exact=False).filter(has_text='Oracle · Producción QA').click();page.wait_for_function('()=>document.querySelectorAll(".diagram-open").length===2');assert page.get_by_label('Ver ubicación').input_value() not in ['all','root','none'];report['checks'].append('create_folder_bulk_select_move_and_open')
 page.reload();page.get_by_role('button',name='Abrir carpeta',exact=False).filter(has_text='Oracle · Producción QA').click();page.wait_for_function('()=>document.querySelectorAll(".diagram-open").length===2');report['checks'].append('folder_membership_survives_reload')
 create_map('Oracle QA 3');page.get_by_role('button',name='Mover Oracle QA 3 a carpeta',exact=True).wait_for();page.get_by_role('button',name='Mover Oracle QA 3 a carpeta',exact=True).click();dialog().get_by_label('Carpeta de destino').select_option('');dialog().get_by_role('button',name='Mover',exact=True).click();page.locator('dialog[open]').wait_for(state='hidden');page.wait_for_function('()=>document.querySelectorAll(".diagram-open").length===2');report['checks'].append('new_diagram_inside_folder_and_move_to_unfiled')
 page.get_by_role('button',name='Renombrar carpeta',exact=True).click();dialog().get_by_label('Nombre de la carpeta').fill('Oracle RAC QA');dialog().get_by_role('button',name='Guardar nombre',exact=True).click();page.locator('dialog[open]').wait_for(state='hidden');page.get_by_label('Ver ubicación').locator('option',has_text='Oracle RAC QA').wait_for(state='attached')
 page.get_by_role('button',name='Mis diagramas',exact=True).click();page.get_by_role('button',name='Eliminar carpeta Oracle RAC QA',exact=True).wait_for();page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Eliminar carpeta Oracle RAC QA',exact=True).click();page.wait_for_function('()=>document.querySelectorAll(".diagram-open").length===3');assert context.request.get(api+'?folder=none').json()['total']==3;report['checks'].append('rename_folder_and_delete_without_losing_diagrams')
 for i in range(9):assert context.request.post(api+'/folders',data={'name':f'Carpeta de prueba QA {i+1}'},headers=headers).status==201
 page.reload();page.wait_for_selector('.diagram-open');page.wait_for_timeout(300)
 page.route('**/__qa/axe.js',lambda r:r.fulfill(path=str(root/'.artifacts/axe.min.js'),content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js')
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for w,h in [(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(400)
   dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],(theme,w,h,dims)
   inner=page.locator('.diagram-library-body').evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inner[1]<=inner[0]+1,(theme,w,h,inner)
   report['states'].append(dict(theme=theme,width=w,height=h,no_document_or_panel_overflow=True))
   if w in [1440,320]:
    violations=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}');assert not violations,violations;report['accessibility'].append(dict(theme=theme,width=w,violations=violations))
   page.screenshot(path=str(root/f'.artifacts/diagram-folders-{theme}-{w}-{h}.png'))
 assert not errors,errors;report['browser_errors']=errors
 (root/'docs/evidence/diagram-folders-report.json').write_text(json.dumps(report,indent=2)+'\n');print('Folder creation, bulk move, reopen, rename, safe delete and responsive checks passed.');b.close()
