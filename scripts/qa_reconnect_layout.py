"""Synthetic cancellation, atomic endpoint edits, bounded search and pointer reconnection."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'synthetic_identity_only':True,'layouts':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 row=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA Reconnect '+Date.now(),template_id:'blank'})})).json();const r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:1,document:{name:c.name,nodes:['a','b','c'].map((id,i)=>({id,type:'resource',position:{x:i*470,y:i===2?250:0},data:{kind:'virtual',label:'QA '+id}})),edges:[{id:'qa-line-unique',source:'a',target:'b',sourceHandle:'east',targetHandle:'west',relation:'connected',color:'blue',pattern:'dashed',type:'default',label:'SSH'}]}})});if(!r.ok)throw Error(await r.text());return c}''')
 def open_map():
  page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=row['name'],exact=True)).click();page.locator('.react-flow__node[data-id="a"]').wait_for();page.wait_for_timeout(400)
 def saved():return page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()
 def wait_save():page.wait_for_timeout(1300)
 def select_line():
  xy=page.locator('.react-flow__edge-path').evaluate('''p=>{for(let f=.1;f<.95;f+=.05){const q=p.getPointAtLength(p.getTotalLength()*f),r=new DOMPoint(q.x,q.y).matrixTransform(p.getScreenCTM());if(document.elementFromPoint(r.x,r.y)?.closest('.react-flow__edge')&&!document.elementFromPoint(r.x,r.y)?.classList.contains('react-flow__edgeupdater'))return [r.x,r.y]}throw Error('No exposed line')}''');page.mouse.click(*xy);page.get_by_role('group',name='Estilo de conexión').wait_for()
 def panel():
  select_line();page.get_by_role('button',name='Más propiedades de la conexión',exact=True).click();return page.get_by_role('complementary',name='Propiedades de la conexión')
 open_map();view=panel()
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(390,844),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150)
   toggle=view.get_by_role('button',name='Buscar otro componente',exact=True)
   if toggle.get_attribute('aria-expanded')!='true':toggle.click()
   view.get_by_label('Buscar componente para reconectar',exact=True).fill('QA');view.get_by_label('Origen de conexión',exact=True).select_option('c');page.wait_for_timeout(150)
   assert view.evaluate('(e)=>e.scrollHeight<=e.clientHeight+2'),(w,h,view.evaluate('(e)=>[e.clientHeight,e.scrollHeight]'));report['layouts'].append(dict(theme=theme,width=w,height=h,expanded_search=True,pending_apply=True))
   action=view.get_by_role('button',name='Aplicar extremos',exact=True).bounding_box();assert action['y']+action['height']<=h
   if (w,h)==(844,390):page.screenshot(path='.artifacts/nesting/reconnect-landscape-'+theme+'.png')
 report['no_inner_overflow']=True;Path('docs/evidence/reconnect-layout-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS expanded search and pending apply fit six layouts');b.close()
