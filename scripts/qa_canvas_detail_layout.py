"""Synthetic waypoints, direct fields, scoped comparison and identical PDF image."""
import base64,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image,ImageChops
import fitz
base='http://localhost:18179';report={'synthetic_identity_only':True}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 row=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA Canvas '+Date.now(),template_id:'blank'})})).json();const doc={name:c.name,nodes:['vm','db','inst','outside'].map((id,i)=>({id:'11111111-2222-3333-4444-'+id,type:'resource',position:{x:i===3?900:0,y:i===3?140:0},data:{kind:i===3?'servidor':i?'datos':'virtual',label:['QA VM','QA Oracle','QA Instancia','QA Independiente'][i],...(i===0?{server_instance:{identification:{hostname:'qa.vm.example',environment:'Producción',criticality:'Alta'},evidence:{product:'QA technology'},controls:{monitoring:{status:'configured',evidence:'QA evidence'}}}}:{})}})),edges:[{id:'host-one',source:'11111111-2222-3333-4444-vm',target:'11111111-2222-3333-4444-db',relation:'hosts'},{id:'host-two',source:'11111111-2222-3333-4444-db',target:'11111111-2222-3333-4444-inst',relation:'hosts'},{id:'aaaaaaaa-bbbb-cccc-dddd-lastsegment',source:'11111111-2222-3333-4444-inst',target:'11111111-2222-3333-4444-outside',sourceHandle:'east',targetHandle:'north',type:'default',color:'purple',pattern:'dashdot',arrows:'both',relation:'connected',label:'SSH · TCP 22'}]};const r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:1,document:doc})});if(!r.ok)throw Error(await r.text());return c}''')
 def open_map():
  page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=row['name'],exact=True)).click();page.locator('.react-flow__node').first.wait_for();page.wait_for_timeout(300)
 def saved():return page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()
 def select_line():
  xy=page.locator('.react-flow__edge-path').evaluate('''p=>{for(let f=.15;f<.9;f+=.05){const q=p.getPointAtLength(p.getTotalLength()*f),r=new DOMPoint(q.x,q.y).matrixTransform(p.getScreenCTM());if(document.elementFromPoint(r.x,r.y)?.closest('.react-flow__edge')&&!document.elementFromPoint(r.x,r.y)?.classList.contains('react-flow__edgeupdater'))return [r.x,r.y]}throw Error('No visible line')}''');page.mouse.click(*xy);page.get_by_role('group',name='Estilo de conexión').wait_for()
 open_map();select_line()
 report['layouts']=[]
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(390,844),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(200)
   toolbar=page.get_by_role('group',name='Estilo de conexión');r=toolbar.bounding_box();assert r['x']>=0 and r['y']>=0 and r['x']+r['width']<=w+1 and r['y']+r['height']<=h,(w,h,r)
   assert toolbar.evaluate('(e)=>e.scrollWidth<=e.clientWidth+2')
   report['layouts'].append(dict(theme=theme,width=w,height=h,toolbar_fits=True))
 page.set_viewport_size({'width':1440,'height':900});page.evaluate("document.documentElement.dataset.theme='light'")
 handle=page.locator('[data-bend="1"]');handle.focus();page.keyboard.press('ArrowDown');page.wait_for_timeout(1400);assert next(e for e in saved()['document']['edges'] if e['relation']=='connected')['bends'][1]['y']==10
 page.get_by_role('button',name='Restablecer recorrido',exact=True).click();page.wait_for_timeout(1400);assert all(v=={'x':0,'y':0} for v in next(e for e in saved()['document']['edges'] if e['relation']=='connected')['bends'])
 assert not errors,errors
 Path('docs/evidence/canvas-detail-layout-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS six toolbar layouts, keyboard and reset');b.close()
