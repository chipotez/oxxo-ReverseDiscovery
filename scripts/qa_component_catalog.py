import json,time,os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');report={'states':[],'accessibility':[],'checks':[],'synthetic_identity_only':True};sizes=[(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session')
 def entry(label):return page.locator('button.standard-entry').filter(has=page.get_by_role('heading',name=label,exact=True))
 def start():
  page.goto(base+'/bienvenida/#/catalogo');page.get_by_role('heading',name='Tu espacio de trabajo',exact=True).wait_for();page.goto(base+'/bienvenida/#/estandares');entry('Cómputo y plataformas').wait_for()
 def view(name):
  page.set_viewport_size({'width':1440,'height':900})
  if name=='home':page.goto(base+'/bienvenida/#/catalogo');page.get_by_role('heading',name='Tu espacio de trabajo',exact=True).wait_for();return
  start()
  if name=='categories':return
  if name.startswith('server'):
   entry('Cómputo y plataformas').click();entry('Servidores').click()
   if name=='server-identification':entry('Identificación de entidad').click()
   return
  entry('Datos y bases de datos').click()
  if name=='data-families':return
  entry('Bases de datos').click()
  if name=='database-types':return
  entry('Base de datos').click()
  if name=='database-model':return
  entry('Capacidades y controles').click();page.get_by_role('table').wait_for()
 def check(name,theme,w,h,selector):
  page.wait_for_timeout(130);dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],(name,theme,w,h,dims)
  box=page.locator(selector).evaluate('(e)=>[e.clientWidth,e.scrollWidth,e.clientHeight,e.scrollHeight]');assert box[1]<=box[0]+2 and box[3]<=box[2]+2,(name,theme,w,h,box)
  report['states'].append(dict(view=name,theme=theme,width=w,height=h,no_overflow=True))
 def audit(name,theme):
  page.route('**/__qa/axe.js',lambda r:r.fulfill(path='.artifacts/axe.min.js',content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js');v=page.evaluate('async()=>{let r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>v.id)}');assert not v,(name,theme,v);report['accessibility'].append(dict(view=name,theme=theme,violations=v))
 for name in ['home','categories','data-families','database-types','database-model','database-controls','server-model','server-identification']:
  view(name)
  if name=='home':assert page.locator('.catalog-area-icon').count()==7;assert not page.locator('.catalog-art').count()
  for theme in ['light','dark']:
   page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
   for w,h in sizes:page.set_viewport_size({'width':w,'height':h});check(name,theme,w,h,'#contenido' if name=='home' else '.standards-list-body')
   page.set_viewport_size({'width':1440,'height':900});page.wait_for_timeout(120)
   if name in ['home','categories','database-controls']:audit(name,theme);page.screenshot(path=f'.artifacts/component-catalog/{name}-{theme}.png')
 # supplier and technology search, not duplicated vendor-specific component types
 start();page.get_by_label('Proveedor del catálogo',exact=True).select_option('Oracle');page.get_by_label('Buscar componentes',exact=True).fill('PostgreSQL');entry('Datos y bases de datos').wait_for();assert not entry('Personas y organización').count();page.get_by_label('Buscar componentes',exact=True).fill('zzzzzz');page.get_by_text('No hay componentes con estos filtros.',exact=True).wait_for();report['checks'].append('provider_and_technology_filters')
 # Each category has at least one reachable generic or server model
 catalog=json.loads(Path('app/frontend/src/component-catalog.json').read_text())
 for c in catalog['categories']:
  start();page.locator('.standards-tree-desktop').get_by_role('button',name=c['label'],exact=True).click();sub=c['children'][0];entry(sub['label']).click()
  if sub['id']!='servers':entry(next(r['label'] for r in catalog['resources'] if r['kind']==sub['kinds'][0])).click()
  entry('Identificación de entidad').wait_for()
 report['checks'].append('twelve_categories_share_four_block_structure')
 # Real disposable database: palette uses same resource catalog, node context saved online
 page.goto(base+'/bienvenida/#/catalogo');title='QA catálogo '+str(time.time_ns());created=page.evaluate('''async name=>{let r=await fetch('/bienvenida/api/diagrams',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},body:JSON.stringify({name,template_id:'blank'})});if(!r.ok)throw Error(await r.text());return r.json()}''',title)
 page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=title,exact=True)).click();page.get_by_role('button',name='Añadir recurso',exact=True).click();palette=page.get_by_role('complementary',name='Biblioteca de recursos');palette.wait_for()
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in sizes:page.set_viewport_size({'width':w,'height':h});check('palette',theme,w,h,'.palette-body')
 page.set_viewport_size({'width':1440,'height':900});palette.get_by_label('Buscar recursos',exact=True).fill('PostgreSQL');palette.get_by_role('button',name='Instancia de base de datos',exact=True).wait_for();palette.get_by_role('button',name='Instancia de base de datos',exact=True).click();page.get_by_role('button',name='Cerrar recursos',exact=True).click();page.get_by_role('button',name='Propiedades',exact=True).click();page.get_by_text('Proveedor, tecnología y ubicación',exact=True).click();page.get_by_label('Proveedor',exact=True).fill('Oracle');page.get_by_label('Tecnología / versión',exact=True).fill('Oracle 19c');page.get_by_label('Ubicación / región',exact=True).fill('QA datacenter');page.wait_for_timeout(1300);page.get_by_text('Guardado en línea',exact=True).wait_for();doc=ctx.request.get(base+'/bienvenida/api/diagrams/'+created['id']).json();node=doc['document']['nodes'][0];assert node['data']['kind']=='instancia_db';assert node['data']['provider']=='Oracle';assert node['data']['technology']=='Oracle 19c';assert node['data']['location']=='QA datacenter';report['checks'].append('shared_diagram_palette_and_saved_provider_technology_location')
 # permissions unchanged
 guest=b.new_context();gp=guest.new_page();gp.goto(base+'/__qa/session?as=guest');assert guest.request.get(base+'/bienvenida/api/standards').status==403;assert guest.request.post(base+'/bienvenida/api/diagrams',data={}).status in [400,403];report['checks'].append('guest_standards_and_create_restrictions_preserved');assert not errors,errors;report['browser_errors']=errors;Path('docs/evidence/component-catalog-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(report['states']),'responsive states and component catalog workflow',flush=True);b.close()
