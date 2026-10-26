"""Synthetic pointer-placement QA with actual canvas pan/zoom transforms."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:18179'
def api(p,method,path,body=None):return p.evaluate('''async([method,path,body])=>{const r=await fetch('/bienvenida/api/diagrams'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body===null?{}:{body:JSON.stringify(body)})});return {status:r.status,data:await r.json()};}''',[method,path,body])
checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);c=b.new_context(viewport={'width':1440,'height':900});p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(BASE+'/__qa/session');name='QA Pointer '+str(time.time_ns());row=api(p,'POST','',{'name':name,'template_id':'blank'})['data'];did=row['id'];doc={'name':name,'nodes':[{'id':'original','type':'resource','position':{'x':0,'y':0},'data':{'kind':'virtual','label':'QA pointer VM'}}],'edges':[]};assert api(p,'PUT','/'+did,{'revision':row['revision'],'document':doc})['status']==200
 p.goto(BASE+'/bienvenida/#/herramientas/diagramas');p.locator('button.diagram-open').filter(has=p.get_by_role('heading',name=name,exact=True)).click();expect(p.locator('.resource-status').get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000)
 payload=json.dumps({'koodaria':1,'document':doc})
 for i in range(2):
  if i:p.get_by_role('button',name='Acercar',exact=True).click();p.wait_for_timeout(400)
  box=p.locator('.react-flow').bounding_box();x=box['x']+box['width']*.72;y=box['y']+box['height']*.68
  p.mouse.move(x,y)
  expected=p.locator('.react-flow__viewport').evaluate('''(el,point)=>{const m=new DOMMatrix(getComputedStyle(el).transform),r=el.closest('.react-flow').getBoundingClientRect();return {x:(point.x-r.left-m.e)/m.a,y:(point.y-r.top-m.f)/m.d};}''',{'x':x,'y':y})
  # Moving over toolbar must not replace the last canvas point.
  title=p.locator('.diagram-title').bounding_box();p.mouse.move(title['x']+10,title['y']+10)
  before=api(p,'GET','/'+did)['data'];ids={n['id'] for n in before['document']['nodes']}
  p.evaluate('''text=>{const d=new DataTransfer();d.setData('text/plain',text);window.dispatchEvent(new ClipboardEvent('paste',{clipboardData:d,bubbles:true,cancelable:true}));}''',payload)
  p.wait_for_timeout(1100);expect(p.locator('.resource-status').get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000)
  after=api(p,'GET','/'+did)['data'];added=[n for n in after['document']['nodes'] if n['id'] not in ids];assert len(added)==1
  actual=added[0]['position'];assert abs(actual['x']-expected['x'])<2 and abs(actual['y']-expected['y'])<2,(actual,expected)
  checks.append('last canvas pointer persisted at '+('changed zoom' if i else 'initial zoom')+' after moving over toolbar')
 assert not errors,errors;c.close();b.close()
Path('docs/evidence/paste-pointer-qa.json').write_text(json.dumps({'synthetic_only':True,'checks':checks},indent=2)+'\n');print('PASS pointer placement at two zoom levels')
