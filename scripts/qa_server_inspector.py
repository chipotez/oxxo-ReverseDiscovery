"""Disposable QA: four-sided connections, inspector placement, autosave and sizes."""
import json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');report={'states':[],'synthetic_identity_only':True}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 result=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA inspector '+Date.now(),template_id:'blank'})})).json();const doc={name:c.name,nodes:['a','b'].map((id,i)=>({id:'vm-'+id,type:'resource',position:{x:0,y:i*350},data:{label:'QA VM '+id.toUpperCase(),kind:'virtual'}})),edges:[]};let r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:c.revision,document:doc})});if(!r.ok)throw Error(await r.text());return c}''')
 page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=result['name'],exact=True)).click();a=page.locator('.react-flow__node[data-id="vm-a"]');a.wait_for();page.wait_for_timeout(500)
 assert a.locator('.react-flow__handle').count()==4
 source=a.locator('[data-handleid="south"]').bounding_box();target=page.locator('.react-flow__node[data-id="vm-b"] [data-handleid="north"]').bounding_box();page.mouse.move(source['x']+source['width']/2,source['y']+source['height']/2);page.mouse.down();page.mouse.move(target['x']+target['width']/2,target['y']+target['height']/2,steps=15);page.mouse.up();page.wait_for_timeout(1300)
 doc=ctx.request.get(base+'/bienvenida/api/diagrams/'+result['id']).json()['document'];assert len(doc['edges'])==1,doc['edges'];assert doc['edges'][0]['sourceHandle']=='south';assert doc['edges'][0]['targetHandle']=='north'
 page.get_by_role('button',name='Editar Identificación de entidad de QA VM A',exact=True).click();panel=page.get_by_role('dialog',name='Identificación de entidad',exact=True);panel.wait_for();page.wait_for_timeout(500);assert a.bounding_box()['x']+a.bounding_box()['width']<panel.bounding_box()['x']
 expected={}
 while True:
  for el in panel.locator('input').all():
   label=el.get_attribute('aria-label');value='QA '+label;el.fill(value);expected[label]=value
  next_button=panel.get_by_role('button',name='Campos siguientes',exact=True)
  if not next_button.count() or next_button.is_disabled():break
  next_button.click();page.wait_for_timeout(100)
 page.wait_for_timeout(1500);panel.get_by_text('Guardado automático',exact=True).wait_for();assert panel.locator('.identity-sync').is_visible()
 doc=ctx.request.get(base+'/bienvenida/api/diagrams/'+result['id']).json()['document'];assert doc['nodes'][0]['position']=={'x':0,'y':0};assert len(doc['nodes'][0]['data']['server_instance']['identification'])==7
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(400)
   dim=panel.evaluate('(e)=>({top:e.getBoundingClientRect().top,bottom:e.getBoundingClientRect().bottom,width:e.clientWidth,scrollWidth:e.scrollWidth})');assert dim['top']>=0 and dim['bottom']<=h and dim['scrollWidth']<=dim['width']+2,(w,h,dim)
   body=panel.locator('.identity-form-body').evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert body[1]<=body[0]+2,(w,h,body)
   save=panel.get_by_role('button',name='Guardar',exact=True).bounding_box();assert save['y']+save['height']<=h
   report['states'].append(dict(theme=theme,width=w,height=h,no_overflow=True))
 page.set_viewport_size({'width':1440,'height':900});page.wait_for_timeout(500);page.screenshot(path='.artifacts/component-catalog/server-inspector.png');panel.get_by_role('button',name='Cerrar identificación',exact=True).click();page.reload();page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=result['name'],exact=True)).click();page.get_by_role('button',name='Editar Identificación de entidad de QA VM A',exact=True).click();panel=page.get_by_role('dialog',name='Identificación de entidad',exact=True);assert panel.get_by_label('ID único / CI',exact=True).input_value()=='QA ID único / CI';page.route('**/__qa/axe.js',lambda r:r.fulfill(path='.artifacts/axe.min.js',content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js')
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  violations=page.evaluate('async()=>{let r=await axe.run(".server-identity-panel",{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>v.id)}');assert not violations,(theme,violations)
 assert not errors,errors;report.update(browser_errors=errors,cardinal_connection_roundtrip=True,identity_roundtrip=True,node_coordinates_unchanged=True);Path('docs/evidence/server-inspector-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS inspector placement, autosave, cardinal connection and 16 viewport/theme states');b.close()
