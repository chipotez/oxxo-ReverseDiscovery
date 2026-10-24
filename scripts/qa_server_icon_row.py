"""Disposable browser QA for server nodes and saved per-instance fields."""
import os,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');report={'states':[],'synthetic_identity_only':True}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 created=page.evaluate('''async()=>{const r=await fetch('/bienvenida/api/diagrams',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},body:JSON.stringify({name:'QA server '+Date.now(),template_id:'blank'})});return r.json()}''')
 page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=created['name'],exact=True)).click();page.get_by_role('button',name='Añadir recurso',exact=True).click();page.get_by_label('Buscar recursos',exact=True).fill('Máquina virtual');page.get_by_role('button',name='Máquina virtual',exact=True).click();page.locator('.server-instance-node').wait_for();assert page.locator('.server-standard-icon').count()==4
 labels=['Identificación de entidad','Capacidades y controles','Evidencia operativa','Relaciones de arquitectura']
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(1024,600),(390,844),(320,568),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150)
   boxes=page.locator('.server-standard-icon button').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().top)');assert max(boxes)-min(boxes)<2
   for label in labels:
    button=page.get_by_role('button',name='Editar '+label+' de Máquina virtual',exact=True);button.hover();tip=page.get_by_role('tooltip',name=label,exact=True);tip.wait_for(state='visible');button.focus();assert tip.is_visible();button.click();dialog=page.get_by_role('dialog',name='Máquina virtual',exact=True);assert dialog.get_by_label('Bloque del servidor',exact=True).input_value()==['identification','controls','evidence','relationships'][labels.index(label)];dialog.get_by_role('button',name='Listo',exact=True).click()
   report['states'].append(dict(theme=theme,width=w,height=h,icons_in_one_row=True,hover_focus_and_click=True))
 page.set_viewport_size({'width':1440,'height':900});page.mouse.move(500,100);page.screenshot(path='.artifacts/component-catalog/server-icon-row.png');assert not errors,errors;report['browser_errors']=errors;Path('docs/evidence/server-icon-row-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS icon row, tooltips, keyboard and four block dialogs');b.close()
