"""Visual/interaction QA using synthetic markup; no test login is deployed."""
import json,ast
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];csp=ast.literal_eval(next(line.split('=',1)[1] for line in (root/'app/server.py').read_text().splitlines() if "response.headers['Content-Security-Policy']" in line));html=(root/'app/templates/welcome.html').read_text()
for k,v in {'name':'QA Catálogo','initials':'QC','csrf':'visual-fixture','account_url':'https://login.koodaria.com/realms/koodaria/account/'}.items():html=html.replace('{{ '+k+' }}',v)
r={}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/__qa/catalog',lambda x:x.fulfill(body=html,content_type='text/html',headers={'Content-Security-Policy':csp}))
 page.route('**/workspace-assets/*',lambda x:x.fulfill(path=str(root/'app/static'/x.request.url.split('/')[-1])))
 page.goto('https://koodaria.com/__qa/catalog');page.wait_for_timeout(100)
 assert page.locator('.discipline-card').count()==7
 page.locator('#catalog-search').fill('automatizacion');assert page.locator('.discipline-card').count()==1
 page.locator('#catalog-search').fill('');page.locator('a[href="#/catalogo/observabilidad"]').first.click();page.wait_for_timeout(100)
 page.get_by_role('button',name='Cursos',exact=True).click();assert page.locator('.product-card').count()==3
 page.get_by_role('button',name='Todo',exact=True).click();page.locator('#catalog-search').fill('datadog');assert page.locator('.product-card').count()==2
 page.locator('#catalog-search').fill('no-existe');assert page.locator('.catalog-empty').is_visible();page.locator('#catalog-search').fill('')
 page.locator('a[href="#/catalogo/observabilidad/mapeo-servicios"]').click();page.get_by_role('link',name='Abrir herramienta').click();page.wait_for_timeout(100)
 page.locator('#service-name').fill('Servicio QA');assert 'Servicio QA' in page.locator('#project-diagram').inner_text()
 page.locator('#add-node').click();page.locator('#node-label').fill('Base QA');page.locator('#node-type').select_option('datos');page.locator('#node-parent').select_option('servicio');page.locator('#node-form').get_by_role('button',name='Añadir',exact=True).click();assert 'Base QA' in page.locator('#project-diagram').inner_text()
 with page.expect_download() as download:page.locator('#save-project').click()
 project=json.loads(Path(download.value.path()).read_text());assert project['name']=='Servicio QA' and len(project['nodes'])==2;r['project_json_download']=True
 with page.expect_download() as download:page.locator('#export-svg').click()
 svg=Path(download.value.path()).read_text();assert '<svg' in svg and 'Base QA' in svg;r['svg_download']=True
 page.locator('#project-file').set_input_files({'name':'malformed.json','mimeType':'application/json','buffer':b'{"version":1,"name":"x","nodes":[{"id":"a","label":"x","type":"datos","parent":"a"}]}'})
 page.wait_for_function('()=>document.querySelector("#editor-status").textContent.includes("No pudimos")');assert 'No pudimos' in page.locator('#editor-status').inner_text();r['cyclic_import_rejected']=True
 imported={'version':1,'name':'Proyecto importado','nodes':[{'id':'a','label':'<script>QA</script>','type':'servicio','parent':''},{'id':'b','label':'Datos','type':'datos','parent':'a'}]}
 page.locator('#project-file').set_input_files({'name':'safe.json','mimeType':'application/json','buffer':json.dumps(imported).encode()});page.wait_for_timeout(100)
 assert page.locator('#service-name').input_value()=='Proyecto importado';assert page.locator('#project-diagram script').count()==0;r['safe_import_roundtrip']=True
 page.set_viewport_size({'width':320,'height':568});page.wait_for_timeout(100)
 overflow=page.evaluate('()=>[...document.querySelectorAll("body *")].filter(e=>{const r=e.getBoundingClientRect();return r.right>innerWidth+1&&r.width>0}).map(e=>({tag:e.tagName,id:e.id,cls:e.className?.baseVal??e.className,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width})).slice(0,20)')
 assert not overflow,overflow
 for panel in ['servicio','componentes','diagrama']:
  page.locator('button[data-editor-panel="'+panel+'"]').click();size=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert size==[320,568],(panel,size)
 page.on('dialog',lambda d:d.dismiss())
 page.evaluate('()=>location.hash="/catalogo/observabilidad"');page.wait_for_timeout(100);page.locator('#filter-select').select_option('curso');assert page.locator('.product-card').count()>=1
 titles=[]
 while True:
  titles+=page.locator('.product-card h2').all_text_contents()
  if page.locator('#page-next').is_disabled():break
  page.locator('#page-next').click()
 assert len(titles)==3 and len(set(titles))==3;r['mobile_filter_and_pagination']=True
 for product in ['mapeo-servicios','fundamentos','datadog-ansible']:
  page.evaluate('(v)=>location.hash=v','/catalogo/observabilidad/'+product);page.wait_for_timeout(100)
  for panel in ['resumen','incluye','ejemplo']:
   page.locator('button[data-detail-panel="'+panel+'"]').click();size=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert size==[320,568],(product,panel,size)
 # Exercise a full project and verify that short screens paginate its components.
 page.evaluate('()=>location.hash="/herramientas/mapeo-servicios"');page.wait_for_timeout(100)
 full={'version':1,'name':'Servicio de prueba','nodes':[{'id':'node-'+str(i),'label':'Componente '+str(i+1),'type':'servicio','parent':'node-'+str(i-1) if i else ''} for i in range(12)]}
 page.locator('#project-file').set_input_files({'name':'full.json','mimeType':'application/json','buffer':json.dumps(full).encode()});page.wait_for_function('()=>document.querySelector("#service-name").value==="Servicio de prueba"')
 for w,h in [(1440,900),(1024,600),(320,568),(844,390)]:
  page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(100)
  panels=['servicio','componentes','diagrama'] if w<=600 or h<650 else []
  for panel in panels:
   page.locator('button[data-editor-panel="'+panel+'"]').click();assert page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]')==[w,h],(w,h,panel)
 page.set_viewport_size({'width':1440,'height':900});page.wait_for_timeout(100)
 box=page.locator('#project-diagram svg').get_attribute('viewBox');page.locator('#zoom-in').click();assert page.locator('#project-diagram svg').get_attribute('viewBox')!=box;page.locator('#zoom-fit').click();assert page.locator('#project-diagram svg').get_attribute('viewBox')==box
 page.locator('#project-diagram svg').focus();page.keyboard.press('ArrowRight');assert page.locator('#project-diagram svg').get_attribute('viewBox')!=box;r['diagram_zoom_and_keyboard_pan']=True
 page.locator('[data-edit="node-0"]').click();page.locator('#node-parent').select_option('node-1');page.locator('#node-form button[type=submit]').click();assert 'ciclo' in page.locator('#node-error').inner_text();r['editing_rejects_cycles']=True
 page.locator('#node-parent').select_option('');page.locator('#node-label').fill('Componente editado');page.locator('#node-form button[type=submit]').click();assert 'Componente editado' in page.locator('#project-diagram').inner_text();r['component_editing_works']=True
 r['full_project_responsive']=True
 assert not errors,errors;r['browser_errors']=errors
 (root/'docs/evidence/catalog-functional-report.json').write_text(json.dumps(r,indent=2));print('FUNCTIONAL DONE',r,flush=True);b.close()
