import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'states':[],'checks':[],'accessibility':[],'synthetic_identity_only':True}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/estandares')
 def entry(label):return page.locator('button.standard-entry').filter(has=page.get_by_role('heading',name=label,exact=True))
 def root():
  page.evaluate("location.hash='/catalogo'");page.get_by_role('heading',name='¿Qué quieres desarrollar?').wait_for()
  with page.expect_response(lambda r:r.url.endswith('/bienvenida/api/standards') and r.request.method=='GET'):page.evaluate("location.hash='/estandares'")
  entry('Infraestructura').wait_for();page.wait_for_timeout(60);entry('Infraestructura').click();entry('Cómputo').click();entry('Servidores').click();page.get_by_role('heading',name='Servidores',level=1).wait_for()
 root();sections=json.loads(Path('app/frontend/src/server-standard-model.json').read_text())['sections'];assert len(page.locator('button.standard-entry').all())==4
 def check(theme,w,h,view,panel):
  page.wait_for_timeout(100);dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],(view,theme,w,h,dims)
  sizes=page.locator(panel).evaluate('(e)=>[e.clientWidth,e.scrollWidth,e.clientHeight,e.scrollHeight]');assert sizes[1]<=sizes[0]+2 and sizes[3]<=sizes[2]+2,(view,theme,w,h,sizes)
  report['states'].append(dict(theme=theme,width=w,height=h,view=view,no_overflow=True))
 def audit(view,theme):
  page.route('**/__qa/axe.js',lambda r:r.fulfill(path='.artifacts/axe.min.js',content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js');v=page.evaluate('async()=>{let r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>v.id)}');assert not v,(view,theme,v);report['accessibility'].append(dict(view=view,theme=theme,violations=v))
 sizes=[(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for spec in [None]+sections+['criteria']:
   page.set_viewport_size({'width':1440,'height':900});root()
   if spec=='criteria':page.get_by_role('button',name='Criterios',exact=True).click();view='criteria'
   elif spec:entry(spec['label']).click();view=spec['id']
   else:view='server-overview'
   for w,h in sizes:page.set_viewport_size({'width':w,'height':h});check(theme,w,h,view,'.standards-list-body')
   page.set_viewport_size({'width':1440,'height':900});page.wait_for_timeout(100)
   if view=='server-overview':audit(view,theme);page.screenshot(path=f'.artifacts/server-model-{theme}.png')
 report['checks'].append('four_server_blocks_fields_controls_and_criteria_reachable')
 # Create through UI, exercise editable model policy and conditional control
 page.set_viewport_size({'width':1440,'height':900});root();page.get_by_role('button',name='Definiciones',exact=True).click();page.get_by_role('button',name='+ Nueva definición',exact=True).click();d=page.get_by_role('dialog');name='QA modelo servidor '+str(time.time_ns());d.get_by_label('Nombre',exact=True).fill(name);d.get_by_role('button',name='Crear borrador').click();page.get_by_role('button',name='Estructura',exact=True).click()
 for block in ['identification','evidence','relationships']:
  page.get_by_role('button',name='Campo',exact=True).click();page.get_by_label('Bloque del servidor',exact=True).select_option(block);page.get_by_role('button',name='Regla',exact=True).click();page.get_by_label('Regla de documentación',exact=True).fill('QA regla '+block)
 page.get_by_role('button',name='Guardar borrador',exact=True).click();page.get_by_text('Borrador guardado.',exact=True).wait_for()
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for block in ['identification','evidence','relationships']:
   page.get_by_role('button',name='Campo',exact=True).click();page.get_by_label('Bloque del servidor',exact=True).select_option(block)
   for step in ['Campo','Exigencia','Regla']:
    page.get_by_role('button',name=step,exact=True).click()
    for w,h in sizes:page.set_viewport_size({'width':w,'height':h});check(theme,w,h,'policy-'+block+'-'+step,'.standard-detail-body')
  page.set_viewport_size({'width':1440,'height':900});audit('policy-editor',theme)
 page.get_by_role('button',name='Requisitos',exact=True).click();page.get_by_label('Exigencia',exact=True).select_option('conditional');page.get_by_role('button',name='Condición',exact=True).click();page.get_by_label('Condición de aplicación',exact=True).fill('Solo producción con carga crítica')
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in sizes:page.set_viewport_size({'width':w,'height':h});check(theme,w,h,'conditional-control','.standard-detail-body')
 page.set_viewport_size({'width':1440,'height':900});page.get_by_role('button',name='Guardar borrador',exact=True).click();page.get_by_text('Borrador guardado.',exact=True).wait_for();page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Publicar versión',exact=True).click();page.get_by_text('Versión 1 publicada.',exact=True).wait_for()
 row=next(x for x in ctx.request.get(base+'/bienvenida/api/standards').json()['items'] if x['name']==name);assert row['draft']['requirements'][0]['condition']=='Solo producción con carga crítica';assert all(row['draft']['server_model'][key][0]['rule']=='QA regla '+key for key in ['identification','evidence','relationships']);assert row['published_version']==1
 page.get_by_role('button',name='Volver en estándares',exact=True).click();page.wait_for_timeout(100)
 for _ in range(20):
  page.wait_for_timeout(150)
  if entry(name).count():break
  page.get_by_role('navigation',name='Páginas de estándares').get_by_role('button').last.click()
 entry(name).click();page.get_by_role('button',name='Estructura',exact=True).click();page.get_by_label('Bloque del servidor',exact=True).select_option('relationships');page.get_by_role('button',name='Regla',exact=True).click();assert page.get_by_label('Regla de documentación',exact=True).input_value()=='QA regla relationships'
 report['checks'].append('three_policy_sections_and_conditional_control_saved_published_and_reopened');assert not errors,errors;report['browser_errors']=errors;Path('docs/evidence/server-model-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(report['states']),'responsive states and persisted server model',flush=True);b.close()
