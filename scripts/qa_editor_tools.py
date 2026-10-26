"""Disposable browser fixture only; no customer diagrams or credentials."""
import time,json
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:18179'
def call(p,method,path,body=None):
 return p.evaluate('''async([method,path,body])=>{const r=await fetch('/bienvenida/api/diagrams'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body===null?{}:{body:JSON.stringify(body)})});return {status:r.status,data:await r.json()};}''',[method,path,body])
def saved(p):
 expect(p.locator('.resource-status').get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000)
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);p=b.new_page(viewport={'width':1440,'height':900});errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.goto(BASE+'/__qa/session');name='QA Tools '+str(time.time_ns());r=call(p,'POST','',{'name':name,'template_id':'blank'})['data'];did=r['id']
 doc={'name':name,'nodes':[{'id':k,'type':'resource','position':{'x':i*450,'y':i*40},'data':{'kind':'virtual','label':'QA '+k,'server_instance':{}}} for i,k in enumerate(['a','b','child'])],'edges':[{'id':'hosts','source':'a','target':'child','relation':'hosts','type':'smoothstep'}]}
 assert call(p,'PUT','/'+did,{'revision':r['revision'],'document':doc})['status']==200
 p.goto(BASE+'/bienvenida/#/herramientas/diagramas');p.locator('button.diagram-open').filter(has=p.get_by_role('heading',name=name,exact=True)).click();saved(p)
 a=p.locator('.react-flow__node[data-id="a"]');a.locator('strong').click();p.get_by_role('button',name='Plegar componentes',exact=True).click();p.wait_for_timeout(1200);saved(p);assert not p.locator('.react-flow__node[data-id="child"]').is_visible();assert next(n for n in call(p,'GET','/'+did)['data']['document']['nodes'] if n['id']=='a')['data']['collapsed']
 a.get_by_role('button',name='Desplegar componentes').click();p.wait_for_timeout(1200);saved(p);expect(p.locator('.react-flow__node[data-id="child"]')).to_be_visible()
 a.locator('strong').click();p.get_by_role('button',name='Bloquear posición',exact=True).click();p.wait_for_timeout(1200);saved(p);assert next(n for n in call(p,'GET','/'+did)['data']['document']['nodes'] if n['id']=='a')['data']['positionLocked'];p.get_by_role('button',name='Desbloquear posición',exact=True).click();p.wait_for_timeout(1200);saved(p)
 # Multi-select using the Shift modifier; Ctrl is reserved for rectangular selection.
 p.keyboard.down('Shift');p.locator('.react-flow__node[data-id="b"] strong').click();p.keyboard.up('Shift');expect(p.get_by_role('button',name='Arriba',exact=True)).to_be_visible();p.get_by_role('button',name='Arriba',exact=True).click();p.wait_for_timeout(1200);saved(p);value=call(p,'GET','/'+did)['data']['document'];assert len({n['position']['y'] for n in value['nodes'] if n['id'] in ['a','b']})==1
 a.locator('strong').click();p.locator('.arrange-toolbar').get_by_role('button',name='Comentarios',exact=True).click();panel=p.get_by_role('complementary',name='Comentarios anclados');panel.get_by_label('Comentario',exact=True).fill('Verificar respaldo sintético');panel.get_by_role('button',name='Publicar comentario').click();expect(panel.get_by_text('Verificar respaldo sintético',exact=True)).to_be_visible(timeout=15000);panel.get_by_role('button',name='Resolver',exact=True).click();expect(panel.get_by_role('button',name='Resuelto · Reabrir',exact=True)).to_be_visible(timeout=15000)
 # Rectangle selection must appear during Ctrl+drag on the canvas.
 panel.get_by_role('button',name='Cerrar comentarios').click();rect=p.locator('.resource-stage').bounding_box();p.keyboard.down('Control');p.mouse.move(rect['x']+20,rect['y']+100);p.mouse.down();p.mouse.move(rect['x']+rect['width']-25,rect['y']+rect['height']-25,steps=6);expect(p.locator('.canvas-area-selection')).to_be_visible();p.mouse.up();p.keyboard.up('Control')
 # A source spanning more than 3000 units remains importable without scaling data.
 big=call(p,'POST','',{'name':'QA Wide '+name,'template_id':'blank'})['data'];wide={'name':'QA Wide '+name,'nodes':[{'id':'wide'+str(i),'type':'resource','position':{'x':i*4000,'y':0},'data':{'kind':'virtual','label':'Wide '+str(i)}} for i in range(2)],'edges':[]};assert call(p,'PUT','/'+big['id'],{'revision':big['revision'],'document':wide})['status']==200
 p.get_by_role('button',name='Insertar',exact=True).click();d=p.get_by_role('dialog',name='Insertar diagrama');d.get_by_role('button',name='QA Wide '+name+' →',exact=True).click();p.wait_for_timeout(1500);saved(p);data=call(p,'GET','/'+did)['data']['document'];assert any(n['type']=='resourceGroup' and n['style']['width']>3000 for n in data['nodes'])
 p.get_by_role('button',name='Comentarios',exact=True).first.click();panel=p.get_by_role('complementary',name='Comentarios anclados')
 for w,h in [(1440,900),(1024,768),(390,844),(844,390)]:
  p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(200);assert panel.bounding_box()['x']>=0;assert panel.get_by_role('button',name='Cerrar comentarios').is_visible()
 assert not errors,errors
 print('PASS: persisted collapse, lock/unlock, Shift multi-selection, alignment, anchored comment, resolve, responsive panel; no JS errors')
 p.close();b.close()
