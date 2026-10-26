"""Synthetic identities only: direct editing, persistence and Escape layering."""
import time
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 p=b.new_page(viewport={'width':1440,'height':900});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.goto('http://localhost:18179/__qa/session')
 def api(method,path='',body=None):
  return p.evaluate('''async([method,path,body])=>{let r=await fetch('/bienvenida/api/diagrams'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body?{body:JSON.stringify(body)}:{})});return await r.json()}''',[method,path,body])
 name='QA Identity '+str(time.time_ns());r=api('POST',body={'name':name,'template_id':'blank'});did=r['id']
 doc={'name':name,'nodes':[{'id':'synthetic','type':'resource','position':{'x':0,'y':0},'data':{'kind':'virtual','label':'Synthetic VM','address':'192.0.2.10 / 192.0.2.11','port':'443','server_instance':{}}}],'edges':[]}
 api('PUT','/'+did,{'revision':r['revision'],'document':doc})
 p.goto('http://localhost:18179/bienvenida/#/herramientas/diagramas');p.locator('button.diagram-open').filter(has=p.get_by_role('heading',name=name,exact=True)).click()
 expect(p.locator('.resource-status').get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000);p.wait_for_timeout(600)
 p.get_by_role('button',name='Editar en Identidad: 192.0.2.10 / 192.0.2.11 · 443',exact=True).click()
 d=p.get_by_role('dialog',name='Editar IP y datos de identidad');expect(d).to_be_visible()
 for theme in ['light','dark']:
  p.emulate_media(color_scheme=theme)
  for w,h in [(1440,900),(1024,768),(390,844),(844,390)]:
   p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(80);box=d.bounding_box();assert box['x']>=0 and box['y']>=0 and box['y']+box['height']<=h+1;assert d.get_by_role('button',name='Preparar edición').is_visible()
 p.set_viewport_size({'width':1440,'height':900});p.keyboard.press('Escape');expect(d).to_have_count(0)
 p.get_by_role('button',name='Editar en Identidad: 192.0.2.10 / 192.0.2.11 · 443',exact=True).click();d.get_by_role('button',name='Preparar edición').click()
 panel=p.locator('.inspector-identification');expect(panel).to_be_visible(timeout=20000)
 for _ in range(6):
  if panel.get_by_label('Dirección IP / DNS',exact=True).count():break
  panel.get_by_role('button',name='Campos siguientes',exact=True).click()
 field=panel.get_by_label('Dirección IP / DNS',exact=True);expect(field).to_be_visible();assert field.input_value()=='192.0.2.10 / 192.0.2.11'
 field.fill('192.0.2.10\n192.0.2.11\n192.0.2.12');p.wait_for_timeout(1800)
 assert api('GET','/'+did)['document']['nodes'][0]['data']['server_instance']['identification']['address'].endswith('192.0.2.12')
 p.keyboard.press('Escape');expect(panel).to_have_count(0);expect(p.get_by_role('dialog',name='Resumen del recurso')).to_be_visible();p.keyboard.press('Escape');expect(p.get_by_role('dialog',name='Resumen del recurso')).to_have_count(0)
 p.get_by_role('button',name='Añadir recurso',exact=True).click();expect(p.locator('.resource-palette')).to_be_visible();p.keyboard.press('Escape');expect(p.locator('.resource-palette')).to_have_count(0)
 p.get_by_role('button',name='Insertar',exact=True).click();expect(p.get_by_role('dialog',name='Insertar diagrama')).to_be_visible();p.keyboard.press('Escape');expect(p.get_by_role('dialog',name='Insertar diagrama')).not_to_be_visible()
 assert not errors,errors
 print('PASS direct IP editing, multiline persistence, branded confirmation cancellation, inspector/summary/palette/import Escape layering')
 b.close()
