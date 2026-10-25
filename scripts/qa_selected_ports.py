"""Verify quiet anchors, selection, linking and existing-edge geometry using synthetic data."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'synthetic_identity_only':True,'states':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 row=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA Ports '+Date.now(),template_id:'blank'})})).json();const diagramDocument={name:c.name,nodes:['a','b'].map((id,i)=>({id,type:'resource',position:{x:i*500,y:0},data:{kind:'virtual',label:'QA '+id}})),edges:[{id:'existing',source:'a',target:'b',type:'smoothstep'}]};const r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:1,document:diagramDocument})});if(!r.ok)throw Error(await r.text());return c}''')
 def open_map():
  page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=row['name'],exact=True)).click();page.locator('.react-flow__node[data-id="a"]').wait_for();page.wait_for_timeout(450)
 def enabled():return page.locator('.resource-port').evaluate_all('(es)=>es.filter(e=>getComputedStyle(e).opacity==="1"&&getComputedStyle(e).pointerEvents!=="none").map(e=>e.closest(".react-flow__node").dataset.id)')
 open_map();assert not enabled();assert page.locator('.react-flow__edge').count()==1
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(390,844),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(300)
   for id in ['a','b']:
    page.locator('.react-flow__node[data-id="'+id+'"] header').click();page.wait_for_timeout(150);assert enabled()==[id]*4,(id,enabled());assert page.locator('.react-flow__edge').count()==1
   page.locator('.react-flow__pane').click(position={'x':15,'y':15});page.wait_for_timeout(150);assert not enabled();report['states'].append(dict(theme=theme,width=w,height=h))
 page.set_viewport_size({'width':1440,'height':900});page.evaluate('document.documentElement.dataset.theme="light"');page.wait_for_timeout(300)
 page.locator('.react-flow__node[data-id="a"] header').click();page.wait_for_timeout(150)
 source=page.locator('.react-flow__node[data-id="a"] .resource-port[data-handleid="south"]').bounding_box();target_node=page.locator('.react-flow__node[data-id="b"]').bounding_box()
 page.mouse.move(source['x']+source['width']/2,source['y']+source['height']/2);page.mouse.down();page.mouse.move(target_node['x']+target_node['width']/2,target_node['y']+20,steps=18);page.wait_for_timeout(200);assert enabled()==['b']*4,enabled()
 target=page.locator('.react-flow__node[data-id="b"] .resource-port[data-handleid="north"]').bounding_box();page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=6);page.mouse.up();page.wait_for_timeout(1500)
 doc=page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()['document'];assert len(doc['edges'])==2,doc['edges'];assert any(e.get('sourceHandle')=='south' and e.get('targetHandle')=='north' for e in doc['edges']);assert enabled()==['b']*4
 page.locator('.react-flow__pane').click(position={'x':15,'y':15});page.wait_for_timeout(150);assert not enabled();assert page.locator('.react-flow__edge').count()==2
 page.reload();open_map();assert not enabled();assert page.locator('.react-flow__edge').count()==2;page.screenshot(path='.artifacts/nesting/selected-ports.png');assert not errors,errors;report.update(browser_errors=errors,selected_only=True,existing_lines_preserved=True,drag_connect_roundtrip=True);Path('docs/evidence/selected-ports-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS selected-only ports, six responsive/theme states, drag-link and reopen');b.close()
