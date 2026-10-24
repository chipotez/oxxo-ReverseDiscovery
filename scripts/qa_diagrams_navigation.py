"""Synthetic browser QA for navigation with a failed pending save."""
import json,uuid,ast
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
html=(root/'app/templates/welcome.html').read_text()
for key,value in {'name':'QA','first_name':'QA','initials':'QA','csrf':'qa','account_url':'/qa-account'}.items():html=html.replace('{{ '+key+' }}',value)
rows={};fail=True
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.route('**/__qa/nav',lambda r:r.fulfill(body=html,content_type='text/html'))
 page.route('**/workspace-assets/*',lambda r:r.fulfill(path=str(root/'app/static'/r.request.url.split('/')[-1])))
 def api(route):
  key=route.request.url.split('/diagrams')[-1].split('?')[0].strip('/');method=route.request.method
  if method=='GET':route.fulfill(json=rows[key] if key else {'items':[dict(id=v['id'],name=v['name'],revision=v['revision'],updated_at=v['updated_at'],resources=len(v['document']['nodes'])) for v in rows.values()],'total':len(rows),'page_size':8,'page':1})
  elif method=='POST':
   name=route.request.post_data_json['name'];id=str(uuid.uuid4());rows[id]=dict(id=id,name=name,revision=1,updated_at='2026-10-23T20:00:00Z',document=dict(name=name,nodes=[],edges=[]));route.fulfill(status=201,json=rows[id])
  elif method=='PUT':route.fulfill(status=503,json={'error':'Fallo sintético de conexión.'})
 page.route('**/bienvenida/api/diagrams**',api)
 page.goto('https://koodaria.com/__qa/nav#/herramientas/mapeo-recursos');page.get_by_role('button',name='+ Nuevo diagrama').click();dlg=page.locator('.resource-dialog');dlg.get_by_label('Nombre del diagrama').fill('Navegación QA');dlg.get_by_role('button',name='Crear diagrama').click();page.get_by_role('button',name='+ Añadir').click();dlg.get_by_label('Nombre',exact=True).fill('Recurso QA');dlg.get_by_role('button',name='Añadir',exact=True).click();page.locator('.diagram-save-error').wait_for()
 page.once('dialog',lambda d:d.dismiss());page.locator('.workspace-rail [data-section=inicio]').click();page.wait_for_timeout(100);assert page.locator('.react-flow').count()==1
 page.once('dialog',lambda d:d.accept());page.locator('.workspace-rail [data-section=inicio]').click();page.wait_for_selector('.catalog-card');page.evaluate('location.hash="/herramientas/mapeo-recursos"');page.get_by_role('button',name='+ Nuevo diagrama').wait_for();page.wait_for_timeout(1000);assert not page.evaluate('KoodariaResourceFlow.hasUnsavedChanges()');assert not errors,errors
 b.close();print('Pending-change route guard and disposed-writer isolation passed.')
