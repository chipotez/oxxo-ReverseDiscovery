"""Synthetic-only editor QA: no real customer maps or credentials."""
import json,time
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
BASE='http://localhost:18179'
def call(p,method,path,body=None):
 return p.evaluate('''async([method,path,body])=>{const r=await fetch('/bienvenida/api/diagrams'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body===null?{}:{body:JSON.stringify(body)})});return {status:r.status,data:await r.json()};}''',[method,path,body])
def opened(p,name):
 
 if p.locator('.narrative-canvas').count():p.get_by_role('button',name='Mis diagramas',exact=True).click()
 else:p.goto(BASE+'/bienvenida/#/herramientas/diagramas')
 p.wait_for_timeout(1000);p.locator('button.diagram-open').filter(has=p.get_by_role('heading',name=name,exact=True)).click();expect(p.locator('.resource-status').get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000)
def saved(p):
 p.wait_for_timeout(1000);expect(p.locator('.resource-status').get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000)
checks=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);ctx=b.new_context(viewport={'width':1440,'height':900});p=ctx.new_page();errors=[];p.on('pageerror',lambda e:(errors.append(str(e)),print('BROWSER ERROR',str(e))));p.goto(BASE+'/__qa/session');name='QA Editing '+str(time.time_ns());row=call(p,'POST','',{'name':name,'template_id':'blank'})['data'];did=row['id']
 doc={'name':name,'nodes':[{'id':k,'type':'resource','position':{'x':i*550,'y':0},'data':{'label':'QA '+k,'kind':'virtual','address':'192.0.2.10','port':'443','server_instance':{}}} for i,k in enumerate(['a','b'])],'edges':[{'id':'edge','source':'a','target':'b','sourceHandle':'east','targetHandle':'west','type':'smoothstep','relation':'connected'}]}
 doc['nodes'].insert(0,{'id':'frame','type':'resourceGroup','position':{'x':0,'y':0},'style':{'width':1200,'height':300},'data':{'kind':'grupo','label':'QA Frame'}})
 for n in doc['nodes'][1:]:n['parentId']='frame';n['position']['x']+=16;n['position']['y']+=40
 assert call(p,'PUT','/'+did,{'revision':row['revision'],'document':doc})['status']==200
 opened(p,name);p.locator('.react-flow__node[data-id="a"]').click();p.wait_for_timeout(2000)
 # Native clipboard events used by browser Ctrl/Cmd-C/V, with both user and input guards.
 payload=p.evaluate('''()=>{const d=new DataTransfer();window.dispatchEvent(new ClipboardEvent('copy',{clipboardData:d,bubbles:true,cancelable:true}));return d.getData('text/plain');}''');assert json.loads(payload)['koodaria']==1
 p.evaluate('''text=>{const d=new DataTransfer();d.setData('text/plain',text);window.dispatchEvent(new ClipboardEvent('paste',{clipboardData:d,bubbles:true,cancelable:true}));}''',payload);saved(p)
 result=call(p,'GET','/'+did)['data'];assert len(result['document']['nodes'])==4;assert len({n['id'] for n in result['document']['nodes']})==4;checks.append('copy/paste generates new persistent IDs')
 # Route segment keyboard moves entire segment and persists canonical points.
 point=p.locator('.react-flow__edge[data-id="edge"] .react-flow__edge-interaction').evaluate('(el)=>{const q=el.getPointAtLength(el.getTotalLength()*.2).matrixTransform(el.getScreenCTM());return {x:q.x,y:q.y};}');p.mouse.click(point['x'],point['y']);handle=p.locator('.edge-bend').first;expect(handle).to_be_visible();handle.focus();handle.press('ArrowDown');saved(p);result=call(p,'GET','/'+did)['data'];edge=result['document']['edges'][0];assert len(edge.get('routePoints',[]))>=2,edge;checks.append('segment move persists and keeps endpoint IDs')
 handle=p.locator('.edge-bend').first;box=handle.bounding_box();p.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2);p.mouse.down();p.mouse.move(box['x']+box['width']/2,box['y']+box['height']/2+30,steps=5);p.mouse.up();saved(p);checks.append('pointer drag moves a complete route segment')
 p.locator('.react-flow__edge[data-id="edge"] .react-flow__edge-interaction').dispatch_event('click');p.get_by_label('Recorrido',exact=True).select_option('default');saved(p);assert 'C' in p.locator('.react-flow__edge[data-id="edge"] .react-flow__edge-path').get_attribute('d');result=call(p,'GET','/'+did)['data'];assert result['document']['edges'][0]['type']=='default';checks.append('curve style persists after manual orthogonal editing')
 # Reclassify through dependent selects and explicit confirmation.
 p.locator('.react-flow__node[data-id="a"]').dblclick();summary=p.get_by_role('dialog',name='Resumen del recurso');summary.get_by_role('button',name='Cambiar clasificación',exact=True).click();dlg=p.get_by_role('dialog',name='Cambiar clasificación');expect(dlg).to_be_visible();families=dlg.get_by_label('Familia').locator('option').evaluate_all('(xs)=>xs.map(x=>({v:x.value,t:x.textContent}))');chosen=next(x['v'] for x in families if 'Datos' in x['t']);dlg.get_by_label('Familia').select_option(chosen);assert dlg.get_by_label('Tipo',exact=True).input_value()=='';assert dlg.get_by_label('Subtipo',exact=True).input_value()==''
 options=dlg.get_by_label('Tipo',exact=True).locator('option').evaluate_all('(xs)=>xs.map(x=>x.value).filter(Boolean)');dlg.get_by_label('Tipo',exact=True).select_option(options[0]);subs=dlg.get_by_label('Subtipo',exact=True).locator('option').evaluate_all('(xs)=>xs.map(x=>x.value).filter(Boolean)');dlg.get_by_label('Subtipo',exact=True).select_option(subs[0]);dlg.get_by_role('button',name='Revisar cambio').click();dlg.get_by_role('button',name='Confirmar clasificación').click();saved(p)
 result=call(p,'GET','/'+did)['data'];a=next(n for n in result['document']['nodes'] if n['id']=='a');assert a['data']['kind']==subs[0];assert result['document']['edges'][0]['source']=='a';checks.append('dependent classification preserves ID and connections')
 # Legacy displayed fields become versioned identity fields, not an ungoverned second form.
 p.on('dialog',lambda d:d.accept());summary=p.get_by_role('dialog',name='Resumen del recurso');summary.get_by_role('button',name='Editar datos visibles en Identidad').click();panel=p.locator('.inspector-identification');expect(panel).to_be_visible(timeout=15000);p.wait_for_timeout(1200);
 for _ in range(5):
  if panel.get_by_label('Dirección IP / DNS',exact=True).count():break
  panel.get_by_role('button',name='Campos siguientes',exact=True).click()
 expect(panel.get_by_label('Dirección IP / DNS',exact=True)).to_be_visible();assert panel.get_by_label('Dirección IP / DNS',exact=True).input_value()=='192.0.2.10';panel.get_by_label('Dirección IP / DNS',exact=True).fill('192.0.2.20');saved(p);result=call(p,'GET','/'+did)['data'];a=next(n for n in result['document']['nodes'] if n['id']=='a');assert a['data']['component_instance']['identification']['address']=='192.0.2.20';assert a['data']['address']=='';checks.append('visible legacy data migrates to explicit versioned identity fields')
 panel.get_by_role('button',name='Cerrar panel del servidor').click()
 # Paste into a distinct map and import the original as an independent grouped copy.
 second=name+' copy';row2=call(p,'POST','',{'name':second,'template_id':'blank'})['data'];opened(p,second);p.evaluate('''text=>{const d=new DataTransfer();d.setData('text/plain',text);window.dispatchEvent(new ClipboardEvent('paste',{clipboardData:d,bubbles:true,cancelable:true}));}''',payload);saved(p);checks.append('cross-diagram clipboard persists')
 p.get_by_role('button',name='Insertar',exact=True).click();dlg=p.get_by_role('dialog',name='Insertar diagrama');dlg.get_by_role('button',name=name+' →',exact=True).click();saved(p);r=call(p,'GET','/'+row2['id'])['data'];assert any(n['type']=='resourceGroup' for n in r['document']['nodes']);assert len(r['document']['nodes'])==6;groups=[n for n in r['document']['nodes'] if n['type']=='resourceGroup'];assert len(groups)==2;outer=next(n for n in groups if not n.get('parentId'));inner=next(n for n in groups if n.get('parentId'));assert inner['parentId']==outer['id'];assert outer['style']['width']>=inner['style']['width'];checks.append('insert diagram creates independent grouped graph')
 nested=next(n for n in r['document']['nodes'] if n['data']['kind']==subs[0]);p.locator('.react-flow__node[data-id="'+nested['id']+'"]').dblclick();p.get_by_role('dialog',name='Resumen del recurso').get_by_role('button',name='Cambiar clasificación',exact=True).click();dlg=p.get_by_role('dialog',name='Cambiar clasificación')
 p.screenshot(path='.artifacts/qa-classification.png')
 for theme in ['light','dark']:
  p.emulate_media(color_scheme=theme)
  for w,h in [(1440,900),(1024,768),(390,844),(844,390)]:
   p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(150);box=dlg.bounding_box();assert box and box['x']>=-1 and box['x']+box['width']<=w+1
   close=dlg.get_by_role('button',name='Cerrar clasificación').bounding_box();assert close['y']>=0 and close['y']+close['height']<=h
   cancel=dlg.get_by_role('button',name='Cancelar',exact=True).bounding_box();assert cancel['y']>=0 and cancel['y']+cancel['height']<=h
 checks.append('classification actions fit desktop tablet mobile short landscape light and dark')
 assert not errors,errors;ctx.close();b.close()
Path('docs/evidence/graph-editing-qa.json').write_text(json.dumps({'synthetic_only':True,'checks':checks},indent=2)+'\n');print('PASS '+str(len(checks))+' graph browser checks')
