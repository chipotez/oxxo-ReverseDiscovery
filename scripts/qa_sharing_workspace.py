"""Real PostgreSQL/UI test with isolated owner and guest identities, never real email."""
import json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');api=base+'/bienvenida/api/diagrams'
report={'synthetic_identity_only':True,'real_postgresql_disposable_database':True,'checks':[],'states':[],'accessibility':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True)
 guest_context=b.new_context(viewport={'width':1440,'height':900});guest=guest_context.new_page();guest.goto(base+'/__qa/session?as=guest')
 context=b.new_context(viewport={'width':1440,'height':900});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));guest.on('pageerror',lambda e:errors.append(str(e)))
 page.goto(base+'/__qa/session');csrf=page.locator('meta[name=csrf-token]').get_attribute('content');headers={'X-CSRF-Token':csrf}
 while True:
  rows=context.request.get(api).json()['items']
  if not rows:break
  for row in rows:assert context.request.delete(api+'/'+row['id'],data={'revision':row['revision']},headers=headers).status==204
 for f in context.request.get(api+'/folders').json()['items']:context.request.delete(api+'/folders/'+f['id'],data={'revision':f['revision']},headers=headers)
 for name in ['Oracle QA 1','Oracle QA 2','Oracle QA 3']:
  assert context.request.post(api,data={'name':name},headers=headers).status==201
 page.goto(base+'/bienvenida/#/herramientas/mapeo-recursos');page.get_by_role('button',name='Nuevo grupo',exact=True).wait_for();page.get_by_role('button',name='Nuevo grupo',exact=True).click();d=page.locator('dialog[open]');d.get_by_label('Nombre del grupo').fill('Oracle · Producción QA');d.get_by_role('button',name='Crear grupo',exact=True).click();page.locator('dialog[open]').wait_for(state='hidden')
 page.get_by_role('button',name='Seleccionar diagramas de esta página',exact=True).click();page.get_by_role('button',name='Mover (3)',exact=True).click();d=page.locator('dialog[open]');d.get_by_label('Grupo de destino').select_option(label='Oracle · Producción QA');d.get_by_role('button',name='Mover',exact=True).click();page.locator('dialog[open]').wait_for(state='hidden');page.get_by_role('button',name='Abrir grupo',exact=False).filter(has_text='Oracle · Producción QA').click();page.wait_for_function('()=>document.querySelectorAll(".diagram-open").length===3')
 report['checks'].append('semantic_icons_groups_and_compact_bulk_selection')
 page.get_by_role('button',name='Compartir Oracle QA 1',exact=True).click();d=page.locator('dialog[open]');d.get_by_label('Correo electrónico').fill('qa-guest-browser@example.invalid');d.get_by_role('button',name='Compartir',exact=True).click();d.get_by_text('Puede editar',exact=True).wait_for();d.get_by_role('button',name='Cerrar compartir').click();report['checks'].append('owner_grants_edit_access_by_verified_email')
 guest.goto(base+'/bienvenida/#/herramientas/mapeo-recursos');guest.get_by_role('button',name='Compartidos conmigo',exact=True).wait_for();guest.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='Oracle QA 1').wait_for();assert guest.locator('.diagram-open').count()==1;assert not guest.get_by_role('button',name='+ Nuevo diagrama').count();assert not guest.get_by_role('button',name='Nuevo grupo',exact=True).count();assert not guest.get_by_role('button',name='Compartir Oracle QA 1',exact=True).count()
 guest.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='Oracle QA 1').click();guest.locator('.react-flow').wait_for();assert not guest.get_by_role('button',name='Compartir',exact=True).count()
 guest.get_by_role('button',name='+ Añadir',exact=True).click();gd=guest.locator('dialog[open]');gd.get_by_label('Nombre',exact=True).fill('Servidor compartido QA');gd.locator('select[name=kind]').select_option('servidor');gd.get_by_role('button',name='Añadir',exact=True).click();guest.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")')
 rows=context.request.get(api).json()['items'];shared=next(v for v in rows if v['name']=='Oracle QA 1');hidden=next(v for v in rows if v['name']=='Oracle QA 2');assert len(context.request.get(api+'/'+shared['id']).json()['document']['nodes'])==1
 guest_csrf=guest.locator('meta[name=csrf-token]').get_attribute('content');assert guest_context.request.post(api,data={'name':'No autorizado'},headers={'X-CSRF-Token':guest_csrf}).status==403;assert guest_context.request.get(api+'/'+hidden['id']).status==404
 report['checks'].append('guest_edits_only_granted_map_and_cannot_create_or_read_other_maps')
 guest.goto(base+'/bienvenida/#/catalogo');guest.locator('.catalog-card').first.wait_for();assert guest.locator('a.catalog-card').count()==1;guest.locator('a.catalog-card[href="#/catalogo/observabilidad"]').click();guest.locator('a[href="#/herramientas/mapeo-recursos"]').wait_for();assert guest.locator('a.catalog-card').count()==1;assert guest.locator('a[href="#/herramientas/mapeo-recursos"]').count()==1
 guest.goto(base+'/bienvenida/#/herramientas/mapeo-servicios');guest.wait_for_function('()=>location.hash==="#/catalogo"');report['checks'].append('guest_catalog_visible_but_only_observability_resource_mapping_enabled')
 page.get_by_role('button',name='Compartir Oracle QA 1',exact=True).click();d=page.locator('dialog[open]');d.get_by_role('button',name='Personas con acceso',exact=True).click();page.once('dialog',lambda dlg:dlg.accept());d.get_by_role('button',name='Revocar acceso a qa-guest-browser@example.invalid').click();d.get_by_text('Acceso revocado',exact=True).wait_for();d.get_by_role('button',name='Cerrar compartir').click()
 guest.goto(base+'/bienvenida/#/herramientas/mapeo-recursos');guest.get_by_text('Aún no hay diagramas compartidos contigo',exact=True).wait_for();report['checks'].append('owner_revokes_access_immediately')
 page.get_by_role('button',name='Compartir Oracle QA 1',exact=True).click();d=page.locator('dialog[open]');d.get_by_label('Correo electrónico').fill('not-provisioned@example.invalid');d.get_by_role('button',name='Compartir',exact=True).click();d.get_by_role('alert').wait_for();assert 'Falta configurar' in d.get_by_role('alert').inner_text();d.get_by_role('button',name='Cerrar compartir').click();report['checks'].append('unconfigured_mail_does_not_claim_invitation_sent')
 # Return to root and populate pagination to exercise normal and short screens.
 page.locator('.library-breadcrumb').get_by_role('button',name='Mis diagramas',exact=True).click()
 for i in range(8):context.request.post(api+'/folders',data={'name':f'Grupo QA {i+1}'},headers=headers)
 page.reload();page.get_by_role('button',name='Nuevo grupo',exact=True).wait_for();page.wait_for_timeout(250)
 page.route('**/__qa/axe.js',lambda r:r.fulfill(path=str(root/'.artifacts/axe.min.js'),content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js')
 sizes=[(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for w,h in sizes:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(400)
   dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],('library',theme,w,h,dims)
   inner=page.locator('.diagram-library-body').evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inner[1]<=inner[0]+1,('library',theme,w,h,inner)
   report['states'].append(dict(view='library',theme=theme,width=w,height=h,no_document_or_panel_overflow=True))
   if w in [1440,320]:
    issues=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}');assert not issues,issues;report['accessibility'].append(dict(view='library',theme=theme,width=w,violations=issues))
   page.screenshot(path=str(root/f'.artifacts/sharing-library-{theme}-{w}-{h}.png'))
 # Sharing dialog in mobile/short viewports; use a diagram directly from root's diagram filter.
 page.set_viewport_size({'width':1440,'height':900});page.locator('summary[aria-label="Filtrar diagramas"]').click();page.get_by_role('button',name='Solo diagramas',exact=True).click();page.get_by_role('button',name='Compartir Oracle QA 1',exact=True).wait_for();page.get_by_role('button',name='Compartir Oracle QA 1',exact=True).click()
 for w,h in [(1440,900),(320,568),(844,390)]:
  page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150);d=page.locator('dialog[open]');dim=d.evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert dim[1]<=dim[0]+1,('share-dialog',w,h,dim)
  issues=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}');assert not issues,issues;report['accessibility'].append(dict(view='share_dialog',width=w,violations=issues));page.screenshot(path=str(root/f'.artifacts/sharing-dialog-{w}-{h}.png'))
 assert not errors,errors;report['browser_errors']=errors
 (root/'docs/evidence/sharing-workspace-report.json').write_text(json.dumps(report,indent=2)+'\n');b.close();print('Sharing UX, guest restrictions, revocation and responsive accessibility checks passed.')
