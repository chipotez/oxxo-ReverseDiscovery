"""Synthetic QA for canonical fields, all floating blocks and saved edge routing."""
import json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');model=json.loads(Path('app/frontend/src/server-standard-model.json').read_text());functions=json.loads(Path('app/frontend/src/operating-standards.json').read_text())['functions'];report={'states':[],'synthetic_identity_only':True}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/estandares')
 tree=page.locator('.standards-tree-desktop');tree.get_by_role('button',name='Cómputo y plataformas',exact=True).click();tree.get_by_role('button',name='Servidores',exact=True).click()
 expected={}
 for section in model['sections']:
  expected[section['id']]=functions if section['id']=='controls' else section['fields'];tree.get_by_role('button',name=section['label'],exact=True).click();table=page.get_by_role('table');table.wait_for();labels=[]
  for _ in range(20):
   page.wait_for_timeout(100);labels+=table.locator('tbody th').all_text_contents();n=page.get_by_role('button',name='Campos siguientes',exact=True)
   if n.is_disabled():break
   n.click()
  assert set(labels)==set(f['label'] for f in expected[section['id']]),(section['id'],labels)
 page.goto(base+'/bienvenida/#/catalogo');created=page.evaluate('''async()=>{let h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};let c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA unified '+Date.now(),template_id:'blank'})})).json();let doc={name:c.name,nodes:['a','b'].map((id,i)=>({id,type:'resource',position:{x:i*450,y:0},data:{label:'QA VM '+id,kind:'virtual'}})),edges:[{id:'edge',source:'a',target:'b',type:'smoothstep'}]};let r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:c.revision,document:doc})});if(!r.ok)throw Error(await r.text());return c}''')
 page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=created['name'],exact=True)).click();page.locator('.server-instance-node').first.wait_for();assert page.locator('.react-flow__attribution').count()==0
 for section in model['sections']:
  page.get_by_role('button',name='Editar '+section['label']+' de QA VM a',exact=True).click();panel=page.get_by_role('dialog',name=section['label'],exact=True);panel.wait_for();page.wait_for_timeout(300)
  boxes=[page.locator('.react-flow__node[data-id="a"]').bounding_box(),panel.bounding_box()];gap=boxes[1]['x']-boxes[0]['x']-boxes[0]['width'];assert 16<=gap<=32,gap
  assert not panel.locator('.identity-fields label>span').count()
  if section['id']=='identification':assert panel.locator('input').count()==8;assert not panel.get_by_role('navigation',name='Páginas del bloque').count()
  seen=set()
  for _ in range(20):
   for field in expected[section['id']]:
    if section['id']=='controls':
     sel=panel.get_by_label('Estado de '+field['label'],exact=True)
     if sel.count():sel.select_option('configured');panel.get_by_label('Evidencia de '+field['label'],exact=True).fill('QA evidence');seen.add(field['label'])
    else:
     el=panel.get_by_label(field['label'],exact=True)
     if el.count():el.fill('Producción' if field['id']=='environment' else 'Alta' if field['id']=='criticality' else 'QA '+field['id']);seen.add(field['label'])
   n=panel.get_by_role('button',name='Campos siguientes',exact=True)
   if not n.count() or n.is_disabled():break
   n.click();page.wait_for_timeout(100)
  assert seen==set(f['label'] for f in expected[section['id']]),(section['id'],seen)
  for theme in ['light','dark']:
   page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
   for w,h in [(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]:
    page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(200);body=panel.locator('.identity-form-body').evaluate('(e)=>[e.clientHeight,e.scrollHeight]');box=panel.bounding_box();assert body[1]<=body[0]+2,(section['id'],w,h,body);assert box['y']>=0 and box['y']+box['height']<=h+1,(section['id'],w,h,box);report['states'].append(dict(section=section['id'],theme=theme,width=w,height=h))
  page.set_viewport_size({'width':1440,'height':900});panel.get_by_role('button',name='Cerrar panel del servidor',exact=True).click();page.wait_for_timeout(250)
 point=page.locator('.react-flow__edge-interaction').evaluate('(e)=>{const p=e.getPointAtLength(e.getTotalLength()/2);const s=new DOMPoint(p.x,p.y).matrixTransform(e.getScreenCTM());return {x:s.x,y:s.y}}');page.mouse.click(point['x'],point['y']);page.get_by_label('Trazo de conexión',exact=True).select_option('default');page.wait_for_timeout(1300);doc=ctx.request.get(base+'/bienvenida/api/diagrams/'+created['id']).json()['document'];assert doc['edges'][0]['type']=='default';values=doc['nodes'][0]['data']['server_instance'];assert values['identification']['environment']=='Producción';assert values['identification']['criticality']=='Alta';assert len(values['identification'])==8;assert len(values['controls'])==16;assert len(values['evidence'])==5;assert len(values['relationships'])==5
 page.reload();page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=created['name'],exact=True)).click();page.get_by_role('button',name='Editar Identificación de entidad de QA VM a',exact=True).click();panel=page.get_by_role('dialog',name='Identificación de entidad',exact=True);assert panel.get_by_label('Ambiente',exact=True).input_value()=='Producción';page.wait_for_timeout(300);page.screenshot(path='.artifacts/component-catalog/unified-inspector.png');assert not errors,errors;report.update(browser_errors=errors,standard_field_parity=True,all_block_roundtrip=True,curve_persisted=True,attribution_hidden=True);Path('docs/evidence/unified-inspector-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS field parity, 64 inspector states, all block saves and curved edge');b.close()
