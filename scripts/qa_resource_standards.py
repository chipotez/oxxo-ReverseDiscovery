"""Synthetic standards lifecycle and responsive QA against the disposable database."""
import json,os,time
from pathlib import Path
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1];base=os.environ.get('KOODARIA_QA_ORIGIN','http://localhost:18179');maps=base+'/bienvenida/api/diagrams';standards=base+'/bienvenida/api/standards'
sizes=[(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]
report={'synthetic_identity_only':True,'checks':[],'states':[],'accessibility':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);context=b.new_context(viewport={'width':1440,'height':900});page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');csrf=page.locator('meta[name=csrf-token]').get_attribute('content');headers={'X-CSRF-Token':csrf}
 page.get_by_role('button',name='Estándares',exact=True).click();page.get_by_role('button',name='Infraestructura',exact=False).click();page.get_by_role('button',name='Cómputo',exact=False).click();page.get_by_role('button',name='Servidores',exact=False).click();page.get_by_role('button',name='Definiciones',exact=True).click();page.get_by_role('button',name='+ Nueva definición',exact=True).click();d=page.locator('dialog[open]');title='Servidor Linux QA '+str(time.time_ns());d.get_by_label('Nombre',exact=True).fill(title);d.get_by_role('button',name='Crear borrador').click();page.get_by_role('button',name='Requisitos',exact=True).click();page.get_by_label('Herramienta aprobada',exact=True).fill('QA Monitor');page.get_by_role('button',name='Guardar borrador',exact=True).click();page.get_by_text('Borrador guardado.',exact=True).wait_for();page.once('dialog',lambda d:d.accept());page.get_by_role('button',name='Publicar versión',exact=True).click();page.get_by_text('Versión 1 publicada.',exact=True).wait_for()
 row=next(r for r in context.request.get(standards).json()['items'] if r['name']==title);assert row['published_version']==1
 report['checks'].append('sidebar_catalog_linux_draft_edited_saved_and_published')
 def check(view,w,h,selector):
  dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]');assert dims==[w,h],(view,w,h,dims)
  box=page.locator(selector);inside=box.evaluate('(e)=>[e.clientHeight,e.scrollHeight]');assert inside[1]<=inside[0]+1,(view,w,h,inside)
  report['states'].append(dict(view=view,theme=page.evaluate('document.documentElement.dataset.theme'),width=w,height=h,no_overflow=True))
 def axe(view):
  page.route('**/__qa/axe.js',lambda r:r.fulfill(path=str(root/'.artifacts/axe.min.js'),content_type='application/javascript'));page.add_script_tag(url=base+'/__qa/axe.js');issues=page.evaluate('async()=>{const r=await axe.run(document,{runOnly:{type:"tag",values:["wcag2a","wcag2aa","wcag21aa"]}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}');assert not issues,issues;report['accessibility'].append(dict(view=view,violations=issues))
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for tab,sub in [('Definición','Datos'),('Definición','Aplicación'),('Requisitos','Regla'),('Requisitos','Validación'),('Requisitos','Gestión'),('Versiones',None)]:
   page.get_by_role('button',name=tab,exact=True).click()
   if sub:page.get_by_role('button',name=sub,exact=True).click()
   for w,h in sizes:
    page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(100);check(tab+' '+str(sub),w,h,'.standard-detail-body')
    if tab=='Requisitos' and sub=='Regla' and w in [1440,320]:axe('standards '+theme+' '+str(w))
    if w in [1440,320]:page.screenshot(path=str(root/f'.artifacts/standards-{theme}-{tab}-{sub}-{w}.png'))
 page.set_viewport_size({'width':1440,'height':900});page.goto(base+'/bienvenida/#/herramientas/diagramas');page.get_by_role('button',name='+ Nuevo diagrama',exact=True).click();page.locator('dialog[open]').get_by_role('button',name='Continuar',exact=True).click();page.get_by_label('Nombre del diagrama').fill('QA standards diagram');page.get_by_role('button',name='Crear diagrama',exact=True).click();page.get_by_role('button',name='Añadir recurso').click();palette=page.get_by_role('complementary',name='Biblioteca de recursos');palette.get_by_label('Buscar recursos').fill('Servidor');palette.get_by_role('button',name='Servidor',exact=True).click();palette.get_by_role('button',name=title+' · v1',exact=True).click();page.get_by_role('button',name='Cerrar recursos',exact=True).click();page.get_by_role('button',name='Monitoreo · Sin verificar',exact=True).click();panel=page.get_by_role('complementary',name='Cobertura del servidor');panel.get_by_label('Estado',exact=True).select_option('configured');panel.get_by_role('button',name='Evidencia',exact=True).click();panel.get_by_label('Evidencia o comentario').fill('QA evidencia sintética');page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")')
 diagram=next(r for r in context.request.get(maps).json()['items'] if r['name']=='QA standards diagram');saved=context.request.get(maps+'/'+diagram['id']).json()['document'];bound=saved['nodes'][0]['data']['standard'];assert bound['version']==1;assert bound['coverage'][0]['status']=='configured' and bound['coverage'][0]['source']=='declared';assert bound['definition']['requirements'][0]['tool']=='QA Monitor'
 for theme in ['light','dark']:
  page.evaluate('(v)=>document.documentElement.dataset.theme=v',theme)
  for tab in ['Estado documentado','Evidencia','Requisito']:
   panel.get_by_role('button',name=tab,exact=True).click()
   for w,h in sizes:
    page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(100);check('coverage '+tab,w,h,'.coverage-panel')
    if tab=='Estado documentado' and w in [1440,320]:axe('coverage '+theme+' '+str(w))
    if w in [1440,320]:page.screenshot(path=str(root/f'.artifacts/coverage-{theme}-{tab}-{w}.png'))
 report['checks'].append('new_server_requires_publication_unknown_indicators_manual_coverage_persists')
 # Publishing does not change bound nodes; the editor offers an explicit review.
 value=context.request.get(standards).json()['items'];row=next(r for r in value if r['id']==row['id']);draft=row['draft'];draft['requirements'][0]['tool']='QA Monitor v2';updated=context.request.put(standards+'/'+row['id'],data={'revision':row['revision'],'definition':draft},headers=headers).json();assert context.request.post(standards+'/'+row['id']+'/publish',data={'revision':updated['revision']},headers=headers).status==201
 page.set_viewport_size({'width':1440,'height':900});page.reload();page.get_by_role('button',name='Abrir diagrama',exact=False).filter(has_text='QA standards diagram').first.click();page.get_by_role('button',name='Monitoreo · Configurado',exact=True).click();panel.get_by_role('button',name='Revisar actualización · v2').wait_for();assert context.request.get(maps+'/'+diagram['id']).json()['document']['nodes'][0]['data']['standard']['version']==1
 page.once('dialog',lambda d:d.accept());panel.get_by_role('button',name='Revisar actualización · v2').click();page.wait_for_function('()=>document.querySelector(".resource-status").textContent.includes("Guardado en línea")');new=context.request.get(maps+'/'+diagram['id']).json()['document']['nodes'][0]['data']['standard'];assert new['version']==2 and all(c['status']=='unknown' for c in new['coverage'])
 report['checks'].append('new_publication_pinned_until_review_and_update_resets_unverified')
 assert not errors,errors;report['browser_errors']=errors;(root/'docs/evidence/resource-standards-report.json').write_text(json.dumps(report,indent=2)+'\n');b.close();print('Standards lifecycle, snapshot binding, coverage, explicit version update and responsive UI PASS')
