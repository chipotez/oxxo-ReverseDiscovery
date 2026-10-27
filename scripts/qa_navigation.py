"""Recursive navigation audit against disposable QA data; never uses customer credentials."""
import json,time,os
from pathlib import Path
from urllib.parse import urlencode,urlsplit,parse_qs
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:18179'
ROOT='/estandares'
HOME='/catalogo/observabilidad'
catalog=json.loads(Path('app/frontend/src/component-catalog.json').read_text())
resources={r['kind']:r for r in catalog['resources'] if not r.get('legacy')}
checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 p=b.new_page(viewport={'width':1440,'height':900});p.add_init_script('window.qaPending=0;const nativeFetch=window.fetch;window.fetch=(...args)=>{window.qaPending++;return nativeFetch(...args).finally(()=>window.qaPending--)}');errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 cache={}
 def stable_get(route):
  key=route.request.url
  if key not in cache:
   response=route.fetch();assert response.ok,('QA read fixture',response.status,key);cache[key]={'status':response.status,'headers':response.headers,'body':response.body()}
  route.fulfill(**cache[key])
 # Reuse real disposable read fixtures: this audit exercises routing, not repeated DB reads.
 p.route('**/bienvenida/api/standards',stable_get)
 p.route('**/bienvenida/api/catalog/models/*',stable_get)
 p.goto(BASE+'/__qa/session');p.goto(BASE+'/bienvenida/')
 expect(p.locator('h1')).to_have_text('Observabilidad')
 assert p.locator('[data-section][aria-current=page]').evaluate_all('(xs)=>xs.map(x=>x.dataset.section)')==['inicio']
 checks.append('login-home-single-active-icon')
 def route(path):
  p.evaluate('(path)=>location.hash=path',arg=path)
  p.wait_for_function('(path)=>location.hash==="#"+path',arg=path)
  p.wait_for_timeout(40);p.wait_for_function('()=>window.qaPending===0')
 def query():return {k:v[0] for k,v in parse_qs(urlsplit(p.url).fragment.partition('?')[2]).items()}
 def waitq(expected):
  p.wait_for_function('(expected)=>{const q=new URLSearchParams(location.hash.split("?")[1]||"");return Object.entries(expected).every(([k,v])=>(q.get(k)||"")===v)}',arg=expected)
 def api(method,path='',body=None):
  return p.evaluate('''async([method,path,body])=>{const r=await fetch('/bienvenida/api/diagrams'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body?{body:JSON.stringify(body)}:{})});if(!r.ok)throw Error('QA fixture '+r.status);return r.json()}''',[method,path,body])
 p.get_by_role('link').filter(has=p.get_by_role('heading',name='Topología y dependencias',exact=True)).click();expect(p.locator('h1')).to_have_text('Diagramas')
 p.get_by_role('button',name='Volver a Inicio',exact=True).click();expect(p.locator('h1')).to_have_text('Observabilidad')
 p.go_back();expect(p.locator('h1')).to_have_text('Diagramas');p.go_forward();expect(p.locator('h1')).to_have_text('Observabilidad');checks.append('library-home-browser-reverse-forward')
 # New disposable group and document: refresh and history preserve their context.
 folder=api('POST','/folders',{'name':'QA Navigation '+str(time.time_ns())})
 fid=folder['id'];doc=api('POST',body={'name':'QA Navigation Diagram','template_id':'blank','folder_id':fid});did=doc['id']
 route('/herramientas/diagramas?folder='+fid);expect(p.get_by_role('heading',name='QA Navigation Diagram',exact=True)).to_be_visible()
 p.locator('button.diagram-open').filter(has=p.get_by_role('heading',name='QA Navigation Diagram',exact=True)).click();waitq({'diagram':did});expect(p.locator('.react-flow')).to_be_visible()
 p.go_back();expect(p.get_by_role('heading',name='QA Navigation Diagram',exact=True)).to_be_visible();waitq({'folder':fid,'diagram':''})
 p.go_forward();expect(p.locator('.react-flow')).to_be_visible();waitq({'folder':fid,'diagram':did});p.reload();expect(p.locator('.react-flow')).to_be_visible()
 p.get_by_role('button',name='Volver a mis diagramas',exact=True).click();expect(p.get_by_role('heading',name='QA Navigation Diagram',exact=True)).to_be_visible();waitq({'folder':fid,'diagram':''})
 p.get_by_role('button',name='Volver a mis diagramas',exact=True).click();waitq({'folder':''});p.get_by_role('button',name='Volver a Inicio',exact=True).click();expect(p.locator('h1')).to_have_text('Observabilidad');checks.append('group-editor-refresh-back-forward')
 route('/catalogo/observabilidad/gobierno');expect(p.locator('h1')).to_have_text('Gobierno');p.get_by_role('link',name='Inicio',exact=True).click();expect(p.locator('h1')).to_have_text('Observabilidad');checks.append('government-home-breadcrumb')
 # Every family, subfamily, component and all four standard sections.
 for family in catalog['categories']:
  f=family['id'];
  if os.environ.get('QA_FAMILY') and f!=os.environ['QA_FAMILY']:continue
  familyq={'level':'subcategories','category':f}
  cases=[(familyq,{'level':'','category':''})]
  for sub in family['children']:
   t=sub['id'];base={'category':f,'subcategory':t};level='serverModel' if t=='servers' else 'types'
   cases.append(({'level':level,**base},{'level':'subcategories','category':f,'subcategory':''}))
   if t=='servers':
    for section in ['identification','controls','evidence','relationships']:
     cases.append(({'level':'serverReference',**base,'section':section},{'level':'serverModel','category':f,'subcategory':t}))
   for kind in sub['kinds']:
    if kind not in resources or t=='servers':continue
    leaf={'level':'componentModel',**base,'kind':kind}
    cases.append((leaf,{'level':'types',**base,'kind':''}))
    for section in ['identification','controls','evidence','relationships']:
     cases.append(({'level':'componentReference',**base,'kind':kind,'section':section},leaf))
  for target,parent in cases:
   path=ROOT+'?'+urlencode(target);route(path)
   expect(p.get_by_role('button',name='Volver en estándares',exact=True)).to_be_visible()
   # Decoder must restore exactly this level before clicking Back.
   waitq(target);expect(p.locator('.standards-tool')).to_have_attribute('data-navigation-level',target['level'])

   if p.locator('.fault-dialog[open]').count():raise AssertionError(path+' '+p.locator('.fault-dialog[open]').inner_text())
   p.get_by_role('button',name='Volver en estándares',exact=True).dispatch_event('click');waitq(parent);expect(p.locator('.standards-tool')).to_have_attribute('data-navigation-level',parent['level'] or 'categories')
   p.go_back();waitq(target);expect(p.locator('.standards-tool')).to_have_attribute('data-navigation-level',target['level']);expect(p.get_by_role('button',name='Volver en estándares',exact=True)).to_be_visible()
   p.go_forward();waitq(parent);expect(p.locator('.standards-tool')).to_have_attribute('data-navigation-level',parent['level'] or 'categories');p.wait_for_timeout(40);p.wait_for_function('()=>window.qaPending===0')
   checks.append(path)
  print('PASS family',f,len(cases),'total',len(checks),flush=True)
 assert not errors,errors
 Path('docs/evidence/navigation-qa.json').write_text(json.dumps({'date':'2026-10-27','environment':'disposable QA; stable GET fixtures replayed after first actual read','checks':len(checks),'families':len(catalog['categories']),'javascriptErrors':errors,'routes':checks},ensure_ascii=False,indent=2)+'\n')
 print('PASS recursive navigation',len(checks),flush=True)
 b.close()
