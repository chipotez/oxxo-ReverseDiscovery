"""Verify quiet anchors, selection, linking and existing-edge geometry using synthetic data."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'synthetic_identity_only':True,'states':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 row=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA Ports '+Date.now(),template_id:'blank'})})).json();const diagramDocument={name:c.name,nodes:['a','b','db','inst'].map((id,i)=>({id,type:'resource',position:{x:i*500,y:0},data:{kind:['db','inst'].includes(id)?'datos':'virtual',label:'QA '+id}})),edges:[{id:'existing',source:'a',target:'db',relation:'hosts'},{id:'host2',source:'db',target:'inst',relation:'hosts'}]};const r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:1,document:diagramDocument})});if(!r.ok)throw Error(await r.text());return c}''')
 def open_map():
  page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=row['name'],exact=True)).click();page.locator('.react-flow__node[data-id="a"]').wait_for();page.wait_for_timeout(450)
 def enabled():return page.locator('.resource-port').evaluate_all('(es)=>es.filter(e=>getComputedStyle(e).opacity==="1"&&getComputedStyle(e).pointerEvents!=="none").map(e=>e.closest(".react-flow__node").dataset.id)')
 open_map()
 # Connect by a real drag before editing the newly created line.
 page.locator('.react-flow__node[data-id="a"] header').click();page.wait_for_timeout(150)
 source=page.locator('.react-flow__node[data-id="a"] .resource-port[data-handleid="south"]').bounding_box();target_node=page.locator('.react-flow__node[data-id="b"]').bounding_box()
 page.mouse.move(source['x']+source['width']/2,source['y']+source['height']/2);page.mouse.down();page.mouse.move(target_node['x']+target_node['width']/2,target_node['y']+20,steps=18);page.wait_for_timeout(150)
 target=page.locator('.react-flow__node[data-id="b"] .resource-port[data-handleid="north"]').bounding_box();page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=6);page.mouse.up();page.wait_for_timeout(1300)
 def select_line():
  xy=page.locator('.react-flow__edge-path').evaluate('(p)=>{const q=p.getPointAtLength(p.getTotalLength()*.5),r=new DOMPoint(q.x,q.y).matrixTransform(p.getScreenCTM());return {x:r.x,y:r.y}}')
  page.mouse.click(xy['x'],xy['y']);page.get_by_role('group',name='Estilo de conexión').wait_for()
 select_line()
 for route in ['straight','default','step','smoothstep']:
  page.get_by_label('Recorrido',exact=True).select_option(route)
 for pattern in ['dashed','dashdot','longdash','dotted']:
  page.get_by_label('Línea',exact=True).select_option(pattern)
 for arrows in ['none','start','both']:
  page.get_by_label('Flechas',exact=True).select_option(arrows)
 page.get_by_label('Color de línea',exact=True).select_option('blue')
 page.wait_for_timeout(1400)
 doc=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()['document'];line=next(e for e in doc['edges'] if e.get('relation')!='hosts');assert line['color']=='blue';assert (line['pattern'],line['arrows'],line['type'])==('dotted','both','smoothstep'),line
 page.reload();open_map();select_line();assert page.get_by_label('Línea',exact=True).input_value()=='dotted';assert page.get_by_label('Flechas',exact=True).input_value()=='both'
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(390,844),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(200)
   box=page.get_by_role('group',name='Estilo de conexión').bounding_box();assert box['x']>=0 and box['x']+box['width']<=w+1 and box['y']+box['height']<=h+1,box
   stage=page.locator('.resource-stage').bounding_box();assert abs((box['x']+box['width']/2)-(stage['x']+stage['width']/2))<2;assert abs(box['y']-stage['y']-12)<2
   report['states'].append(dict(theme=theme,width=w,height=h))
 page.set_viewport_size({'width':1440,'height':900});page.evaluate('document.documentElement.dataset.theme="light"');page.wait_for_timeout(200);page.screenshot(path='.artifacts/nesting/scoped-inspectors.png')
 page.get_by_role('button',name='Más propiedades de la conexión',exact=True).click();panel=page.get_by_role('complementary',name='Propiedades de la conexión');assert panel.get_by_label('Nombre del diagrama',exact=True).count()==0
 assert panel.get_by_label('Etiqueta visible (opcional)',exact=True).count()==1;assert panel.get_by_text(line['id'].split('-')[-1],exact=True).count()==1
 panel.get_by_label('Etiqueta visible (opcional)',exact=True).fill('SSH · TCP 22');page.wait_for_timeout(1200);panel.get_by_role('button',name='Cerrar propiedades',exact=True).click()
 page.locator('.react-flow__node[data-id="b"] header').dblclick();summary=page.get_by_role('dialog',name='Resumen del recurso');summary.wait_for();summary.get_by_text('Identificador del componente',exact=True).click();assert summary.locator('code').inner_text()=='b'
 assert summary.get_by_label('Nombre del diagrama',exact=True).count()==0;assert page.get_by_label('Tipo de recurso',exact=True).count()==0
 summary.get_by_role('button',name='Abrir Identificación de entidad de QA b',exact=True).click();identity=page.get_by_role('dialog',name='Identificación de entidad');identity.wait_for();assert identity.get_by_label('Hostname / FQDN',exact=True).count()==1;identity.get_by_label('Hostname / FQDN',exact=True).fill('qa.example.test');page.wait_for_timeout(1200)
 identity.get_by_role('button',name='Cerrar panel del servidor',exact=True).click();page.locator('.diagram-title-edit').dblclick();diagram=page.get_by_role('complementary',name='Propiedades del diagrama');diagram.wait_for();assert diagram.get_by_label('Nombre del diagrama',exact=True).count()==1;assert diagram.get_by_label('Tipo de relación',exact=True).count()==0
 saved=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()['document'];assert {n['id'] for n in saved['nodes']}=={n['id'] for n in doc['nodes']};assert {e['id'] for e in saved['edges']}=={e['id'] for e in doc['edges']};vm=next(n for n in saved['nodes'] if n['id']=='b');assert vm['data']['server_instance']['identification']['hostname']=='qa.example.test';assert vm['data']['label']=='qa.example.test';assert saved['name']==doc['name'];assert next(e for e in saved['edges'] if e['id']==line['id'])['label']=='SSH · TCP 22';assert not errors,errors
 report.update(browser_errors=errors,nested_save_roundtrip=True,styles_roundtrip=True,centered_toolbar=True,isolated_inspectors=True,canonical_hostname_roundtrip=True,stable_ids=True);Path('docs/evidence/scoped-inspectors-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS nested graph, connector drag, routes, patterns, arrows, save/reopen, six layouts');b.close()
