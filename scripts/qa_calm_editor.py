"""Synthetic-only regression for compact editor controls and complete identity forms."""
import time
from playwright.sync_api import sync_playwright,expect
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 p=b.new_page(viewport={'width':1440,'height':900});errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.goto('http://localhost:18179/__qa/session')
 def api(method,path='',body=None):
  return p.evaluate('''async([method,path,body])=>{const r=await fetch('/bienvenida/api/diagrams'+path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body?{body:JSON.stringify(body)}:{})});return await r.json()}''',[method,path,body])
 name='QA Calm '+str(time.time_ns());r=api('POST',body={'name':name,'template_id':'blank'});did=r['id']
 api('PUT','/'+did,{'revision':r['revision'],'document':{'name':name,'nodes':[{'id':'synthetic','type':'resource','position':{'x':0,'y':0},'data':{'kind':'balanceador','label':'QA Balancer','address':'192.0.2.10','port':'443','component_instance':{}}}],'edges':[]}})
 p.goto('http://localhost:18179/bienvenida/#/herramientas/diagramas');p.locator('button.diagram-open').filter(has=p.get_by_role('heading',name=name,exact=True)).click();expect(p.locator('.resource-status').get_by_text('Sincronizado',exact=True)).to_be_visible(timeout=20000);p.wait_for_timeout(500)
 assert not p.get_by_role('button',name='Guardar',exact=True).count();assert p.get_by_role('button',name='Integraciones',exact=True).count()==1
 p.get_by_role('button',name='Editar en Identidad: 192.0.2.10 · 443',exact=True).click();p.get_by_role('dialog',name='Editar IP y datos de identidad').get_by_role('button',name='Preparar edición').click()
 panel=p.locator('.inspector-identification');expect(panel).to_be_visible(timeout=20000);field=panel.get_by_label('IPs',exact=True);expect(field).to_be_visible();assert not panel.get_by_role('navigation').count()
 p.screenshot(path='.artifacts/qa-calm-identity.png');field.fill('192.0.2.10');field.press('Control+End');field.press('Control+Enter');field.press('1');assert '\n' in field.input_value();field.fill('192.0.2.10\n192.0.2.11');p.wait_for_timeout(1800);assert api('GET','/'+did)['document']['nodes'][0]['data']['component_instance']['identification']['address']=='192.0.2.10\n192.0.2.11'
 for theme in ['light','dark']:
  p.emulate_media(color_scheme=theme)
  for w,h in [(1440,900),(1024,768),(390,844),(844,390)]:
   p.set_viewport_size({'width':w,'height':h});p.wait_for_timeout(180);box=panel.bounding_box();assert box['x']>=0 and box['y']>=0 and box['y']+box['height']<=h+1,(w,h,box)
   body=panel.locator('.identity-form-body');last=panel.locator('.identity-fields label').last;last.scroll_into_view_if_needed();assert last.is_visible();assert panel.get_by_role('button',name='Cerrar panel del servidor').is_visible()
 p.set_viewport_size({'width':1440,'height':900});p.keyboard.press('Escape');summary=p.get_by_role('dialog',name='Resumen del recurso');expect(summary).to_be_visible();assert not summary.get_by_text('Identificador del componente',exact=True).count();assert not summary.get_by_role('button',name='Comparar recursos',exact=True).count();assert not summary.get_by_text('Avance de documentación',exact=True).count()
 p.keyboard.press('Escape');p.get_by_role('button',name='Comentarios',exact=True).first.click();comments=p.get_by_role('complementary',name='Comentarios anclados');comments.get_by_label('Comentario',exact=True).fill('QA ubicación');comments.get_by_role('button',name='Publicar comentario').click();expect(comments.get_by_text('QA ubicación',exact=True)).to_be_visible(timeout=15000);comments.get_by_role('button',name='↗ QA Balancer',exact=True).click();assert p.locator('.react-flow__node[data-id=synthetic]').is_visible()
 assert not errors,errors
 print('PASS: one identity view, Ctrl+Enter, persisted multiple IPs, compact toolbar, quiet ID, eight responsive/theme checks')
 b.close()
