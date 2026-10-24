"""Synthetic browser checks for recursive hosting and compact node summaries."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');report={'synthetic_identity_only':True,'states':[],'accessibility':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':1000});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 row=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA Nested '+Date.now(),template_id:'blank'})})).json();const nodes=[{id:'vm',type:'resource',position:{x:0,y:0},data:{kind:'virtual',label:'QA VM',server_instance:{identification:{hostname:'vm.qa.example',environment:'Producción',criticality:'Alta'}}}},{id:'db',type:'resource',position:{x:500,y:0},data:{kind:'datos',label:'QA Database'}},{id:'ftp',type:'resource',position:{x:900,y:0},data:{kind:'custom_service',label:'QA FTP'}}];const r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:1,document:{name:c.name,nodes,edges:[{id:'vm-db',source:'vm',target:'db',relation:'hosts'},{id:'db-ftp',source:'db',target:'ftp',relation:'hosts'}]}})});if(!r.ok)throw Error(await r.text());return c}''')
 def open_map():
  page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=row['name'],exact=True)).click();page.locator('.react-flow__node[data-id="ftp"]').wait_for();page.wait_for_timeout(700)
 def nested():
  bounds=page.locator('.react-flow__node').evaluate_all('(els)=>Object.fromEntries(els.map(e=>{let r=e.getBoundingClientRect();return [e.dataset.id,{x:r.x,y:r.y,right:r.right,bottom:r.bottom}]}))')
  for a,c in [('vm','db'),('db','ftp')]:
   parent,child=bounds[a],bounds[c];assert child['x']>parent['x'] and child['y']>parent['y'] and child['right']<parent['right'] and child['bottom']<parent['bottom'],bounds
 open_map();nested()
 geometry=page.locator('.server-instance-node').evaluate_all('(es)=>es.map(e=>{const r=e.getBoundingClientRect(),h=e.querySelector("header").getBoundingClientRect(),a=e.querySelector(".hosted-add").getBoundingClientRect(),i=e.querySelector(".server-standard-icons").getBoundingClientRect();return {height:e.parentElement.style.height,inside:i.bottom<=r.bottom,aligned:a.top>=h.top&&a.bottom<=h.bottom}})')
 assert all(v['inside'] and v['aligned'] for v in geometry),geometry
 report['compact_geometry']=geometry
 assert page.locator('.react-flow__edge').count()==0
 assert page.locator('.documentation-empty').count()==0
 assert page.locator('.node-summary').first.inner_text().count('Producción')==1
 page.get_by_role('button',name='Editar Identificación de entidad de QA FTP',exact=True).click();panel=page.get_by_role('dialog',name='Identificación de entidad');panel.get_by_label('Nombre',exact=True).fill('QA FTP updated');panel.get_by_role('button',name='Cerrar panel del servidor',exact=True).click();page.wait_for_timeout(1400)
 assert page.get_by_text('Guardado en línea',exact=True).count();page.reload();open_map();nested();page.get_by_role('button',name='Editar Identificación de entidad de QA FTP updated',exact=True).wait_for()
 # A new component must be inside its selected host immediately and after saving.
 page.get_by_role('button',name='Añadir componente alojado en QA VM',exact=True).click();page.get_by_label('Buscar recursos',exact=True).fill('Base de datos');page.get_by_role('button',name='Base de datos',exact=True).click();page.wait_for_timeout(1400)
 doc=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()['document'];assert len(doc['nodes'])==4 and len(doc['edges'])==3
 # Change the node type that previously caused incompatible instance restoration.
 vm=page.locator('.react-flow__node[data-id="vm"]');vm.locator('header').first.click();page.get_by_role('button',name='Propiedades',exact=True).click();props=page.get_by_role('complementary',name='Propiedades');props.locator('select').first.select_option('hipervisor');page.wait_for_timeout(1400)
 assert page.get_by_text('Guardado en línea',exact=True).count();doc=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()['document'];assert next(n for n in doc['nodes'] if n['id']=='vm')['data']['kind']=='hipervisor'
 props.get_by_role('button',name='Cerrar propiedades',exact=True).click()
 page.route('**/__qa/axe.js',lambda r:r.fulfill(path='.artifacts/axe.min.js',content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js')
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  page.set_viewport_size({'width':1440,'height':1000});page.wait_for_timeout(300)
  violations=page.evaluate('async()=>{const r=await axe.run(".server-instance-node",{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))}')
  assert not violations,violations;report['accessibility'].append({'theme':theme,'violations':violations})
  for w,h in [(1440,1000),(1024,600),(390,844),(320,568),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(300);nested();assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1');report['states'].append({'theme':theme,'width':w,'height':h})
 page.set_viewport_size({'width':1440,'height':1000});page.evaluate('document.documentElement.dataset.theme="light"');page.get_by_role('button',name='Ajustar',exact=True).click();page.wait_for_timeout(400);page.screenshot(path='.artifacts/nesting/dense-nodes.png')
 response=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']+'/pdf');assert response.ok;Path('.artifacts/nesting/dense-nodes.pdf').write_bytes(response.body())
 vm=page.locator('.react-flow__node[data-id="vm"]');vm.locator('header').first.click();page.keyboard.press('Delete');page.wait_for_timeout(1400)
 doc=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()['document'];assert len(doc['nodes'])==3 and all(e['source']!='vm' and e['target']!='vm' for e in doc['edges']);report['delete_host_retains_children']=True
 assert not errors,errors;report.update(browser_errors=errors,recursive_containment=True,roundtrip=True,add_inside=True,type_change_saved=True);Path('docs/evidence/dense-nodes-report.json').write_text(json.dumps(report,indent=2)+'\n');b.close();print('PASS nested containment, new child, persistence, type-change regression, 10 viewports and AA node audits')
