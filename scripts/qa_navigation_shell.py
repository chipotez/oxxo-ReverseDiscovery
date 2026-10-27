"""Navigation entry points, discovery parents, aliases, reloads, and responsive rail."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:18179';HOME='/catalogo/observabilidad';checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 p=b.new_page(viewport={'width':1440,'height':900});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.goto(BASE+'/__qa/session');p.goto(BASE+'/bienvenida/')
 def go(path):
  p.evaluate('(path)=>location.hash=path',path);p.wait_for_timeout(150)
 def heading(name):expect(p.locator('h1')).to_have_text(name)
 # Every public catalog entry, including its breadcrumb return.
 go('/catalogo');heading('Tu espacio de trabajo');links=p.locator('a.catalog-card').evaluate_all('(xs)=>xs.map(x=>({href:x.getAttribute("href"),title:x.querySelector("h2").textContent}))')
 for link in links:
  go(link['href'][1:]);heading('Observabilidad' if link['title']=='Observabilidad' else link['title'])
  if link['title']!='Observabilidad':p.get_by_role('link',name='Inicio',exact=True).click();heading('Observabilidad')
  p.locator('[data-section=inicio]').click();heading('Observabilidad');checks.append('area:'+link['title'])
 go('/cursos');heading('Cursos');course=p.locator('a.catalog-card').first;title=course.locator('h2').inner_text();course.click();heading(title)
 p.get_by_role('link',name='← Volver a Capacitación',exact=True).click();heading('Cursos');p.go_back();heading(title);p.go_forward();heading('Cursos');checks.append('course-parent-back-forward')
 for alias in ['/catalogo/observabilidad/diagramas','/herramientas/mapeo-recursos','/herramientas/mapeo-servicios','/herramientas/mapeo-dependencias']:
  go(alias);heading('Diagramas');assert '#/herramientas/diagramas' in p.url;p.get_by_role('button',name='Volver a Inicio',exact=True).click();heading('Observabilidad');checks.append('alias:'+alias)
 for bad in ['/does-not-exist','/catalogo/unknown']:
  go(bad);heading('Observabilidad');checks.append('invalid-route:'+bad)
 go('/descubrimiento');heading('Descubrimiento y conciliación')
 p.get_by_role('button',name='Configurar',exact=True).first.click();heading('Conectar Datadog');p.wait_for_url('**/*view=form*')
 p.go_back();heading('Descubrimiento y conciliación');p.go_forward();heading('Conectar Datadog');p.reload();heading('Conectar Datadog')
 p.get_by_role('button',name='← Conexiones',exact=True).click();heading('Descubrimiento y conciliación')
 for tab in ['Recursos descubiertos','Conciliación','Conexiones']:
  p.get_by_role('button',name=tab,exact=True).click();p.wait_for_timeout(100)
 p.get_by_role('button',name='← Inicio',exact=True).click();heading('Observabilidad');checks.append('discovery-form-tabs-refresh-back-forward')
 # Diagram integrations is a view in history, not a dead-end overlay.
 p.evaluate('''async()=>{const r=await fetch('/bienvenida/api/diagrams',{method:'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},body:JSON.stringify({name:'QA Shell Navigation',template_id:'blank'})});window.qaDoc=await r.json()}''')
 did=p.evaluate('qaDoc.id');go('/herramientas/diagramas?diagram='+did);expect(p.locator('.react-flow')).to_be_visible()
 p.get_by_role('button',name='Integraciones',exact=True).click();expect(p.locator('.integration-explorer')).to_be_visible();assert 'panel=integrations' in p.url
 p.go_back();expect(p.locator('.integration-explorer')).to_have_count(0);expect(p.locator('.react-flow')).to_be_visible()
 p.go_forward();expect(p.locator('.integration-explorer')).to_be_visible();p.reload();expect(p.locator('.integration-explorer')).to_be_visible();checks.append('editor-integrations-back-forward-refresh')
 p.go_back();expect(p.locator('.integration-explorer')).to_have_count(0)
 p.locator('.diagram-title-edit').dblclick();p.get_by_label('Nombre del diagrama',exact=True).fill('QA Navigation Saved Before Leaving')
 p.locator('[data-section=inicio]').click();heading('Observabilidad');p.go_back();expect(p.locator('.diagram-title-edit')).to_have_text('QA Navigation Saved Before Leaving');checks.append('navigation-flushes-pending-online-edit')
 for width,height in [(1440,900),(1024,768),(390,844),(844,390)]:
  p.set_viewport_size({'width':width,'height':height});go(HOME);heading('Observabilidad')
  for theme in ['light','dark']:
   p.evaluate('(theme)=>document.documentElement.dataset.theme=theme',theme)
   assert p.locator('[data-section][aria-current=page]').evaluate_all('(xs)=>xs.map(x=>x.dataset.section)')==['inicio']
   assert p.evaluate('document.documentElement.scrollWidth<=innerWidth+1');
   if theme=='light' and width in [1440,390]:p.screenshot(path=f'.artifacts/navigation-home-{width}.png')
   checks.append(f'home-rail:{width}x{height}:{theme}')
 p.goto(BASE+'/__qa/session?as=guest');p.goto(BASE+'/bienvenida/');heading('Observabilidad')
 assert p.locator('[data-section][aria-current=page]').evaluate_all('(xs)=>xs.map(x=>x.dataset.section)')==['inicio'];checks.append('guest-home')
 assert not errors,errors
 Path('docs/evidence/navigation-shell-qa.json').write_text(json.dumps({'date':'2026-10-27','environment':'disposable QA','checks':checks,'javascriptErrors':errors},ensure_ascii=False,indent=2)+'\n')
 print('PASS shell navigation',len(checks),flush=True);b.close()
