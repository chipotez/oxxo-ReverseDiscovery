"""Visual/interaction QA using synthetic markup; no test login is deployed."""
import json,ast
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];csp=ast.literal_eval(next(line.split('=',1)[1] for line in (root/'app/server.py').read_text().splitlines() if "response.headers['Content-Security-Policy']" in line));html=(root/'app/templates/welcome.html').read_text()
for k,v in {'name':'QA Catálogo','initials':'QC','csrf':'visual-fixture','account_url':'https://login.koodaria.com/realms/koodaria/account/'}.items():html=html.replace('{{ '+k+' }}',v)
report={'states':[],'violations':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/__qa/catalog',lambda r:r.fulfill(body=html,content_type='text/html',headers={'Content-Security-Policy':csp}))
 page.route('**/workspace-assets/*',lambda r:r.fulfill(path=str(root/'app/static'/r.request.url.split('/')[-1])))
 page.route('**/__qa/axe.js',lambda r:r.fulfill(path=str(root/'.artifacts/axe.min.js'),content_type='application/javascript'))
 page.goto('https://koodaria.com/__qa/catalog');page.wait_for_timeout(200);assert not errors,errors
 page.add_script_tag(url='https://koodaria.com/__qa/axe.js')
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for w,h in [(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]:
   page.set_viewport_size({'width':w,'height':h})
   for route in ['/catalogo','/catalogo/observabilidad','/catalogo/observabilidad/mapeo-servicios','/herramientas/mapeo-servicios']:
    page.evaluate('(v)=>location.hash=v',route);page.wait_for_timeout(100)
    r=page.evaluate('()=>({w:innerWidth,h:innerHeight,doc:[document.documentElement.scrollWidth,document.documentElement.scrollHeight],main:document.querySelector("main").getBoundingClientRect().toJSON()})')
    r.update({'route':route,'theme':theme});report['states'].append(r)
    if r['doc'][0]>w or r['doc'][1]>h:raise AssertionError(('Unexpected overflow',theme,w,h,route,r['doc']))
    if (w,h) in [(1440,900),(320,568)] and theme=='light':page.screenshot(path=f'.artifacts/catalog-{route.split("/")[-1]}-{w}.png')
    if (w,h)==(1440,900):
     v=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}')
     if v:report['violations'].append({'route':route,'theme':theme,'items':v})
 report['browser_errors']=errors
 (root/'docs/evidence/catalog-layout-report.json').write_text(json.dumps(report,indent=2));print('LAYOUT DONE',len(report['states']),report['violations'],errors,flush=True);b.close()
