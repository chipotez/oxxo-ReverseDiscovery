"""React Flow UI QA with synthetic identity and the production CSP; no login bypass is deployed."""
import ast,json
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
html=(root/'app/templates/welcome.html').read_text()
for k,v in {'name':'QA Recursos','initials':'QR','csrf':'visual-fixture','account_url':'https://login.koodaria.com/realms/koodaria/account/'}.items():html=html.replace('{{ '+k+' }}',v)
csp=ast.literal_eval(next(line.split('=',1)[1] for line in (root/'app/server.py').read_text().splitlines() if "response.headers['Content-Security-Policy']" in line))
report={'states':[],'accessibility':[],'synthetic_identity_only':True}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/__qa/flow',lambda r:r.fulfill(body=html,content_type='text/html',headers={'Content-Security-Policy':csp}))
 page.route('**/workspace-assets/*',lambda r:r.fulfill(path=str(root/'app/static'/r.request.url.split('/')[-1])))
 page.route('**/__qa/axe.js',lambda r:r.fulfill(path=str(root/'.artifacts/axe.min.js'),content_type='application/javascript'))
 page.goto('https://koodaria.com/__qa/flow#/catalogo/observabilidad');page.wait_for_timeout(200)
 page.locator('a[href="#/herramientas/mapeo-recursos"]').click();page.locator('.react-flow').wait_for();assert not page.locator('.workspace-header').is_visible();assert not page.locator('.detail-layout').count()
 report['card_opens_react_flow_directly']=True
 def add(label,kind):
  page.get_by_role('button',name='+ Añadir',exact=True).click();dialog=page.locator('.resource-dialog');dialog.get_by_label('Nombre',exact=True).fill(label);dialog.locator('select[name=kind]').select_option(kind);dialog.get_by_role('button',name='Añadir',exact=True).click();page.wait_for_timeout(220)
 add('Origen QA','origen');add('F5 QA','balanceador')
 source=page.locator('.react-flow__node').filter(has_text='Origen QA');target=page.locator('.react-flow__node').filter(has_text='F5 QA')
 a=source.locator('.source').bounding_box();z=target.locator('.target').bounding_box();page.mouse.move(a['x']+a['width']/2,a['y']+a['height']/2);page.mouse.down();page.mouse.move(z['x']+z['width']/2,z['y']+z['height']/2,steps=15);page.mouse.up();page.locator('.react-flow__edge').wait_for(timeout=5000)
 report['connect_handles_works']=True
 target.dblclick();page.locator('.resource-properties').get_by_label('IP o nombre DNS').fill('192.0.2.10');page.locator('.resource-properties').get_by_label('Puerto / protocolo').fill('443 / HTTPS');assert '192.0.2.10' in target.inner_text()
 page.get_by_role('button',name='Cerrar propiedades').click();page.locator('.react-flow__edge-interaction').click(force=True);page.locator('.resource-properties').get_by_label('Conexión',exact=True).fill('443 / HTTPS');page.get_by_role('button',name='Cerrar propiedades').click()
 source.locator('strong').hover();box=source.bounding_box();page.mouse.move(box['x']+50,box['y']+35);page.mouse.down();page.mouse.move(box['x']+80,box['y']+110,steps=12);page.mouse.up();page.wait_for_timeout(100)
 with page.expect_download() as d:page.get_by_role('button',name='Descargar',exact=True).click()
 saved=json.loads(Path(d.value.path()).read_text());assert saved['format']=='koodaria-resource-flow';assert len(saved['nodes'])==2 and len(saved['edges'])==1;assert saved['edges'][0]['label']=='443 / HTTPS';assert any(n['data']['address']=='192.0.2.10' for n in saved['nodes']);report['editable_nodes_edges_and_json_export']=True
 add('Grupo QA','grupo');group=page.locator('.react-flow__node').filter(has_text='Grupo QA');assert group.count()==1
 target=page.locator('.react-flow__node').filter(has_text='F5 QA');target.dblclick();group_id=group.get_attribute('data-id');page.locator('.resource-properties').get_by_label('Grupo').select_option(group_id);page.get_by_role('button',name='Cerrar propiedades').click()
 with page.expect_download() as d:page.get_by_role('button',name='Descargar',exact=True).click()
 grouped=json.loads(Path(d.value.path()).read_text());assert any(n.get('parentId')==group_id for n in grouped['nodes']);report['grouping_works']=True
 page.locator('input[type=file]').set_input_files({'name':'map.json','mimeType':'application/json','buffer':json.dumps(grouped).encode()});page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Proyecto abierto")');report['json_reopens']=True
 bad={**grouped,'nodes':[{**grouped['nodes'][0],'data':{**grouped['nodes'][0]['data'],'label':'x'*101}}]}
 page.locator('input[type=file]').set_input_files({'name':'invalid.json','mimeType':'application/json','buffer':json.dumps(bad).encode()});page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("No pudimos")');report['malformed_import_rejected']=True
 page.locator('input[type=file]').set_input_files({'name':'map.json','mimeType':'application/json','buffer':json.dumps(grouped).encode()});page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Proyecto abierto")')
 page.wait_for_timeout(150);page.locator('.react-flow__node').filter(has_text='F5 QA').locator('strong').click()
 page.add_script_tag(url='https://koodaria.com/__qa/axe.js')
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme);page.wait_for_timeout(70)
  for w,h in [(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(80)
   for panel in [False,True]:
    if(page.get_by_role('button',name='Propiedades',exact=True).get_attribute('aria-pressed')=='true')!=panel:page.get_by_role('button',name='Propiedades',exact=True).click()
    dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],(theme,w,h,panel,dims)
    if panel:
     assert page.locator('.resource-properties').get_by_label('IP o nombre DNS').is_visible()
     inner=page.locator('.resource-properties').evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inner[1]<=inner[0]+1,(theme,w,h,'properties',inner)
    report['states'].append({'theme':theme,'width':w,'height':h,'properties_open':panel,'no_document_overflow':True})
   if w in [1440,320]:
    result=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}');assert not result,result;report['accessibility'].append({'theme':theme,'width':w,'violations':result})
   page.get_by_role('button',name='Cerrar propiedades').click();page.screenshot(path=str(root/f'.artifacts/resource-flow-{theme}-{w}-{h}.png'))
 assert not errors,errors;report['browser_errors']=errors
 (root/'docs/evidence/resource-flow-report.json').write_text(json.dumps(report,indent=2)+'\n');print('React Flow interactions, resource-card routing, import/export and responsive checks passed.',flush=True);b.close()
