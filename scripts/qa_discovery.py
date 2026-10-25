"""UI journey against disposable DB and test-only provider; no live Datadog keys."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'synthetic_identity_only':True,'layouts':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo');page.get_by_role('heading',name='Tu espacio de trabajo',exact=True).wait_for();assert page.locator('.breadcrumbs').count()==0
 page.get_by_role('link',name='Observabilidad',exact=False).click();page.get_by_role('button',name='Operación',exact=True).wait_for();assert page.get_by_role('button',name='Operación',exact=True).get_attribute('aria-pressed')=='true';assert page.get_by_role('heading',name='Fundamentos de observabilidad').count()==0
 page.get_by_role('link',name='Descubrimiento y conciliación',exact=False).click();page.get_by_role('heading',name='Descubrimiento y conciliación',exact=True).wait_for()
 page.screenshot(path='.artifacts/nesting/discovery-connectors.png')
 if page.get_by_role('button',name='Configurar',exact=True).count()==0:page.get_by_role('button',name='Nueva conexión',exact=True).click()
 page.get_by_role('button',name='Configurar',exact=True).first.click();name='QA browser '+str(int(time.time()));page.get_by_label('Nombre de conexión',exact=True).fill(name);page.get_by_label('API Key',exact=True).fill('qa-valid-placeholder');page.get_by_label('Application Key',exact=True).fill('qa-app-placeholder')
 page.get_by_role('button',name='Probar conexión',exact=True).click();page.get_by_role('button',name='Ver recursos',exact=True).wait_for(timeout=60000);assert page.locator('.connection-timeline [data-status=complete]').count()==4;page.screenshot(path='.artifacts/nesting/discovery-verified.png')
 page.get_by_role('button',name='Ver recursos',exact=True).click();page.get_by_text('32 hosts encontrados',exact=True).wait_for();page.get_by_role('button',name='Guardar conexión',exact=True).click();page.get_by_role('heading',name=name,exact=True).wait_for()
 page.reload();page.get_by_role('heading',name=name,exact=True).wait_for();page.get_by_role('button',name='Configurar',exact=True).first.click();assert page.get_by_label('API Key',exact=True).input_value()=='';assert page.get_by_label('Application Key',exact=True).input_value()==''
 for theme in ['light','dark']:
  page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
  for w,h in [(1440,900),(390,844),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(200)
   if w<700 or h<600:
    action=page.get_by_role('button',name='Continuar',exact=True)
    if action.count():action.click()
   action=page.get_by_role('button',name='Probar conexión',exact=True);r=action.bounding_box();assert r and r['y']+r['height']<=h+1,(w,h,r)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(w,h)
   report['layouts'].append(dict(theme=theme,width=w,height=h,primary_visible=True))
   if w<700 or h<600:page.get_by_role('button',name='Anterior',exact=True).click()
 page.set_viewport_size({'width':1440,'height':900});page.evaluate("document.documentElement.dataset.theme='light'");page.get_by_label('API Key',exact=True).fill('qa-invalid-placeholder');page.get_by_role('button',name='Probar conexión',exact=True).click();page.get_by_role('dialog').filter(has=page.get_by_text('KOD-CON-002',exact=True)).wait_for(timeout=60000);page.get_by_role('button',name='Entendido',exact=True).click();assert page.locator('.connection-timeline [data-status=failed]').count()==1
 page.get_by_role('button',name='Revisar configuración',exact=True).click();page.get_by_role('button',name='Cancelar',exact=True).click();page.get_by_role('button',name='Eliminar conexión '+name,exact=True).click();page.get_by_role('dialog').get_by_role('button',name='Eliminar',exact=True).click();page.get_by_role('heading',name=name,exact=True).wait_for(state='detached');assert not errors,errors
 report.update(persisted=True,masked_keys=True,four_stages=True,failure_code=True,browser_errors=errors);Path('docs/evidence/discovery-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS discovery journey, persistence, masked credentials, error codes and six responsive layouts');b.close()
