"""Synthetic waypoints, direct fields, scoped comparison and identical PDF image."""
import base64,json,time
from pathlib import Path
from playwright.sync_api import sync_playwright
from PIL import Image,ImageChops
import fitz
base='http://localhost:18179';report={'synthetic_identity_only':True}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(base+'/__qa/session');page.goto(base+'/bienvenida/#/catalogo')
 row=page.evaluate('''async()=>{const h={'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content};const c=await(await fetch('/bienvenida/api/diagrams',{method:'POST',headers:h,body:JSON.stringify({name:'QA Canvas '+Date.now(),template_id:'blank'})})).json();const doc={name:c.name,nodes:['vm','db','inst','outside'].map((id,i)=>({id:'11111111-2222-3333-4444-'+id,type:'resource',position:{x:i===3?900:0,y:i===3?140:0},data:{kind:i===3?'servidor':i?'datos':'virtual',label:['QA VM','QA Oracle','QA Instancia','QA Independiente'][i],...(i===0?{server_instance:{identification:{hostname:'qa.vm.example',environment:'Producción',criticality:'Alta'},evidence:{product:'QA technology'},controls:{monitoring:{status:'configured',evidence:'QA evidence'}}}}:{})}})),edges:[{id:'host-one',source:'11111111-2222-3333-4444-vm',target:'11111111-2222-3333-4444-db',relation:'hosts'},{id:'host-two',source:'11111111-2222-3333-4444-db',target:'11111111-2222-3333-4444-inst',relation:'hosts'},{id:'aaaaaaaa-bbbb-cccc-dddd-lastsegment',source:'11111111-2222-3333-4444-inst',target:'11111111-2222-3333-4444-outside',sourceHandle:'east',targetHandle:'north',type:'default',color:'purple',pattern:'dashdot',arrows:'both',relation:'connected',label:'SSH · TCP 22'}]};const r=await fetch('/bienvenida/api/diagrams/'+c.id,{method:'PUT',headers:h,body:JSON.stringify({revision:1,document:doc})});if(!r.ok)throw Error(await r.text());return c}''')
 def open_map():
  page.goto(base+'/bienvenida/#/herramientas/diagramas');page.locator('button.diagram-open').filter(has=page.get_by_role('heading',name=row['name'],exact=True)).click();page.locator('.react-flow__node').first.wait_for();page.wait_for_timeout(300)
 def saved():return page.request.get(base+'/bienvenida/api/diagrams/'+row['id']).json()
 def select_line():
  xy=page.locator('.react-flow__edge-path').evaluate('''p=>{for(let f=.15;f<.9;f+=.05){const q=p.getPointAtLength(p.getTotalLength()*f),r=new DOMPoint(q.x,q.y).matrixTransform(p.getScreenCTM());if(document.elementFromPoint(r.x,r.y)?.closest('.react-flow__edge')&&!document.elementFromPoint(r.x,r.y)?.classList.contains('react-flow__edgeupdater'))return [r.x,r.y]}throw Error('No visible line')}''');page.mouse.click(*xy);page.get_by_role('group',name='Estilo de conexión').wait_for()
 open_map();select_line();assert page.locator('.edge-bend').count()==3
 for index,delta in [(0,(0,-80)),(1,(30,80)),(2,(0,-40))]:
  handle=page.locator('[data-bend="'+str(index)+'"]');r=handle.bounding_box();page.mouse.move(r['x']+r['width']/2,r['y']+r['height']/2);page.mouse.down();page.mouse.move(r['x']+r['width']/2+delta[0],r['y']+r['height']/2+delta[1],steps=10);page.mouse.up();page.wait_for_timeout(120)
 page.wait_for_timeout(1300);page.keyboard.press('Control+z');page.wait_for_timeout(1200);assert next(e for e in saved()['document']['edges'] if e['relation']=='connected')['bends'][2]=={'x':0,'y':0};page.keyboard.press('Control+Shift+z');page.wait_for_timeout(1200);doc=saved();line=next(e for e in doc['document']['edges'] if e['relation']=='connected');assert all(p['x'] or p['y'] for p in line['bends']),line
 page.reload();open_map();assert next(e for e in saved()['document']['edges'] if e['relation']=='connected')['bends']==line['bends']
 select_line();
 for route in ['step','smoothstep','straight','default']:
  page.get_by_label('Recorrido',exact=True).select_option(route);assert 'NaN' not in page.locator('.react-flow__edge-path').get_attribute('d')
 page.get_by_role('button',name='Más propiedades de la conexión',exact=True).click();panel=page.get_by_role('complementary',name='Propiedades de la conexión');assert panel.get_by_text('lastsegment',exact=True).count()==1;panel.get_by_role('button',name='Cerrar propiedades',exact=True).click()
 # Icons open the corresponding values, with no summary click in between.
 vm=page.locator('.react-flow__node[data-id="11111111-2222-3333-4444-vm"]');vm.locator('header').click()
 for section,label in [('Identificación de entidad','Hostname / FQDN'),('Capacidades y controles',None),('Evidencia operativa','Producto / tecnología'),('Relaciones de arquitectura',None)]:
  vm.get_by_role('button',name='Abrir '+section+' de QA VM',exact=True).click();panel=page.get_by_role('dialog',name=section,exact=True);panel.wait_for()
  if label:assert panel.get_by_label(label,exact=True).input_value()==('qa.vm.example' if section=='Identificación de entidad' else 'QA technology')
  if section=='Capacidades y controles':assert panel.locator('select').first.input_value()=='configured'
  if section=='Relaciones de arquitectura':assert panel.locator('.architecture-links').get_by_text('QA Oracle',exact=True).count()==1
  close=panel.get_by_role('button',name='Cerrar relaciones' if section=='Relaciones de arquitectura' else 'Cerrar panel del servidor',exact=True);close.click();page.wait_for_timeout(250)
 vm.locator('header').dblclick();summary=page.get_by_role('dialog',name='Resumen del recurso');summary.get_by_text('Identificador del componente',exact=True).click();assert summary.locator('code').inner_text()=='vm';summary.get_by_role('button',name='Comparar recursos',exact=True).click();matrix=page.get_by_role('region',name='Cobertura del diagrama');matrix.wait_for();names=matrix.locator('tbody th').all_inner_texts();assert names==['QA VM','QA Oracle','QA Instancia'],names;matrix.get_by_role('button',name='Volver al mapa',exact=True).click()
 page.get_by_role('button',name='Cobertura',exact=True).click();matrix.wait_for();assert matrix.locator('tbody th').count()==4;matrix.get_by_role('button',name='Volver al mapa',exact=True).click()
 page.get_by_role('button',name='Diagrama',exact=True).click();panel=page.get_by_role('complementary',name='Propiedades del diagrama');assert panel.get_by_text(row['id'].split('-')[-1],exact=True).count()==1;panel.get_by_role('button',name='Cerrar propiedades',exact=True).click()
 captures=[]
 def capture(request):
  if request.method=='POST' and request.url.endswith('/pdf'):captures.append(request.post_data_json['image'])
 page.on('request',capture)
 with page.expect_download(timeout=60000) as download:page.get_by_role('button',name='PDF',exact=True).click()
 path='.artifacts/nesting/canvas-detail.pdf';download.value.save_as(path);assert captures;raw=base64.b64decode(captures[-1].split(',',1)[1]);Path('.artifacts/nesting/canvas-capture.png').write_bytes(raw)
 pdf=fitz.open(path);assert len(pdf)==1;images=pdf[0].get_images();assert len(images)==1;image=pdf.extract_image(images[0][0]);Path('.artifacts/nesting/canvas-embedded.png').write_bytes(image['image']);a=Image.open('.artifacts/nesting/canvas-capture.png').convert('RGB');z=Image.open('.artifacts/nesting/canvas-embedded.png').convert('RGB');assert a.size==z.size;assert ImageChops.difference(a,z).getbbox() is None
 pdf[0].get_pixmap(matrix=fitz.Matrix(1,1)).save('.artifacts/nesting/canvas-pdf-render.png');assert not errors,errors
 report.update(three_waypoints_saved=True,direct_icons=True,last_id_segment=True,scoped_descendants=True,pdf_page_count=len(pdf),pdf_image_pixel_identical=True,browser_errors=errors);Path('docs/evidence/canvas-detail-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS three draggable points, canonical values, scoped comparison, last IDs and pixel-identical PDF image');b.close()
