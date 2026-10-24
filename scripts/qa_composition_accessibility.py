import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');audits=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').first.click();page.locator('.server-instance-node').first.wait_for();page.route('**/__qa/axe.js',lambda r:r.fulfill(path='.artifacts/axe.min.js',content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js')
 def audit(view,selector):
  for theme in ['light','dark']:
   page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme);v=page.evaluate('async selector=>{let r=await axe.run(selector,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>v.id)}',selector);assert not v,(view,theme,v);audits.append(dict(view=view,theme=theme,violations=v))
 for count,state in [(0,'empty'),(1,'missing'),(4,'progress'),(8,'complete')]:
  page.get_by_role('button',name='Editar Identificación de entidad de QA VM',exact=True).click();panel=page.get_by_role('dialog',name='Identificación de entidad',exact=True)
  for i,el in enumerate(panel.locator('input').all()):el.fill('QA' if i<count else '')
  panel.get_by_role('button',name='Cerrar panel del servidor',exact=True).click();audit(state,'.server-instance-node')
 page.get_by_role('button',name='Editar Relaciones de arquitectura de QA VM',exact=True).click();audit('architecture','.architecture-panel');page.get_by_role('button',name='Cerrar relaciones',exact=True).click();page.get_by_role('button',name='Editar Capacidades y controles de QA FTP',exact=True).click();audit('generic-controls','.compact-server-inspector');r=json.loads(Path('docs/evidence/composition-report.json').read_text());r['accessibility']=audits;Path('docs/evidence/composition-report.json').write_text(json.dumps(r,indent=2)+'\n');b.close();print('PASS 12 focused WCAG AA audits')
