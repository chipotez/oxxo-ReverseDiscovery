/* Koodaria catalog and local diagram workspace. No identity tokens or remote credentials. */
(() => {
'use strict';
const main=document.querySelector('#contenido');
const guest=document.querySelector('meta[name=portal-tier]')?.content==='guest';
if(!main)return;
const accountMenu=document.querySelector('.user-menu');
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const paths={cloud:'<path d="M6 17a4 4 0 1 1 1-8 5.5 5.5 0 0 1 10.5-1A4.5 4.5 0 0 1 18 17Z"/>',automation:'<rect x="2" y="3" width="6" height="5" rx="1"/><rect x="16" y="16" width="6" height="5" rx="1"/><path d="M5 8v9h11M8 5h11v11"/><path d="m16 12 3 4 3-4"/>',observe:'<rect x="2" y="3" width="20" height="16" rx="2"/><path d="m5 13 4-4 4 5 6-7M8 22h8M12 19v3"/>',devops:'<path d="M8 7C0 1 0 23 8 17l8-10c8-6 8 16 0 10Z"/>',shield:'<path d="m12 2 9 4v6c0 5-9 10-9 10S3 17 3 12V6Z"/><path d="m8 12 3 3 5-6"/>',code:'<rect x="2" y="3" width="20" height="18" rx="2"/><path d="m8 9-3 3 3 3m8-6 3 3-3 3m-3-7-2 8"/>',sre:'<circle cx="12" cy="12" r="4"/><circle cx="12" cy="2" r="1"/><circle cx="22" cy="12" r="1"/><circle cx="12" cy="22" r="1"/><circle cx="2" cy="12" r="1"/><path d="M12 3v5m4 4h5m-9 4v5M3 12h5"/>',map:'<rect x="9" y="2" width="6" height="5" rx="1"/><rect x="1" y="17" width="6" height="5" rx="1"/><rect x="17" y="17" width="6" height="5" rx="1"/><path d="M12 7v5H4v5m8-5h8v5"/>',resource:'<path d="M5 8V5h14v3M5 16v3h14v-3"/><rect x="2" y="9" width="7" height="6" rx="1"/><rect x="15" y="9" width="7" height="6" rx="1"/>',dependency:'<circle cx="5" cy="5" r="3"/><circle cx="19" cy="8" r="3"/><circle cx="9" cy="20" r="3"/><path d="m8 6 8 1M6 8l2 9m4 1 5-7"/>',book:'<path d="M12 5C8 2 4 3 2 4v16c4-2 7-1 10 1 3-2 6-3 10-1V4c-4-2-7-1-10 1Zm0 0v16"/>',integration:'<rect x="1" y="5" width="7" height="14" rx="2"/><rect x="16" y="5" width="7" height="14" rx="2"/><path d="M8 12h8m-3-3 3 3-3 3"/>',arrow:'<path d="M4 12h16m-6-6 6 6-6 6"/>',search:'<circle cx="10" cy="10" r="7"/><path d="m15 15 6 6"/>'};
const icon=(name,cls='')=>`<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name]||paths.map}</svg>`;
const illustration=(type)=>`<svg class="catalog-art" viewBox="0 0 280 120" fill="none" aria-hidden="true"><rect x="1" y="1" width="278" height="118" rx="14" fill="var(--art-bg)"/><g stroke="var(--art-line)" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"><path d="M59 83h43m76 0h43M140 57v25m-38 1h76" stroke-dasharray="3 5"/><rect x="36" y="75" width="25" height="18" rx="4"/><rect x="219" y="75" width="25" height="18" rx="4"/><path d="M42 81h13m170 0h13M42 87h7m176 0h7"/><g transform="translate(112 16) scale(2.3)">${paths[type]||paths.map}</g><circle cx="93" cy="30" r="5" fill="var(--art-dot)" stroke="none"/><circle cx="194" cy="48" r="9" fill="var(--art-dot)" stroke="none"/></g></svg>`;
const productIllustration=type=>`<svg class="catalog-art" viewBox="0 0 96 104" fill="none" aria-hidden="true"><g stroke="var(--art-line)" stroke-width="1.25" stroke-linecap="round" stroke-linejoin="round"><path d="M48 58v12H17v14m31-14h31v14" stroke-dasharray="2.5 4"/><g transform="translate(26 9) scale(1.8)">${paths[type]||paths.map}</g><rect x="8" y="84" width="18" height="13" rx="3" fill="var(--art-bg)"/><rect x="70" y="84" width="18" height="13" rx="3" fill="var(--art-bg)"/><path d="M12 89h10m52 0h10M12 93h6m56 0h6"/><circle cx="13" cy="30" r="4" fill="var(--art-dot)" stroke="none"/><circle cx="83" cy="57" r="6" fill="var(--art-dot)" stroke="none"/></g></svg>`;
const disciplines=[
{id:'cloud',title:'Cloud',description:'Arquitectura y servicios en la nube.',icon:'cloud'},
{id:'automatizacion',title:'Automatización',description:'Tareas y procesos que puedes automatizar.',icon:'automation'},
{id:'observabilidad',title:'Observabilidad',description:'Recursos, servicios y sus dependencias.',icon:'observe'},
{id:'devops',title:'DevOps',description:'Entrega y operación de aplicaciones.',icon:'devops'},
{id:'secops',title:'SecOps',description:'Seguridad integrada en la operación.',icon:'shield'},
{id:'infraestructura-como-codigo',title:'Infraestructura como código',description:'Infraestructura definida y versionada.',icon:'code'},
{id:'sre',title:'SRE',description:'Confiabilidad y continuidad de los servicios.',icon:'sre'}];
const products=[
{id:'diagramas',ready:true,title:'Diagramas',description:'Documenta recursos, servicios y dependencias en un solo lugar.',type:'herramienta',icon:'map',outcome:'Diagramas guardados en línea, con plantillas y acceso compartido.'},
{id:'fundamentos',title:'Fundamentos de observabilidad',description:'Métricas, registros y trazas.',type:'curso',level:1,icon:'book',outcome:'Reconocer las señales que permiten investigar un servicio.',topics:['Métricas y señales de salud','Registros y contexto de un evento','Trazas y recorrido de una solicitud']},
{id:'investiga-servicios',title:'Investiga tus servicios',description:'De una señal a una causa probable.',type:'curso',level:2,icon:'observe',outcome:'Relacionar señales para construir un diagnóstico con evidencia.',topics:['Preguntas para empezar una investigación','Correlación de métricas, registros y trazas','Hipótesis y comprobación de causas']},
{id:'observabilidad-avanzada',title:'Observabilidad avanzada',description:'Diseño, correlación y operación.',type:'curso',level:3,icon:'sre',outcome:'Diseñar una estrategia de observabilidad acorde con el servicio.',topics:['Indicadores y objetivos de servicio','Diseño de alertas y señales útiles','Contexto, costo y operación']},
{id:'datadog-servicenow',title:'Datadog + ServiceNow',description:'De una alerta a un incidente.',type:'caso',icon:'integration',outcome:'Relacionar un evento de monitoreo con su incidente operativo.',topics:['Señal y contexto del evento en Datadog','Campos y ciclo de vida del incidente','Correlación, deduplicación y seguimiento']},
{id:'datadog-ansible',title:'Datadog + Ansible',description:'De la detección a una acción automatizada.',type:'caso',icon:'automation',outcome:'Definir una respuesta controlada a un evento de monitoreo.',topics:['Condiciones para iniciar una acción','Ejecución autorizada del playbook','Verificación del resultado y registro de evidencia']},
{id:'escenarios-operacion',title:'Escenarios de operación',description:'Aplica lo aprendido a situaciones reales.',type:'caso',icon:'code',outcome:'Investigar un servicio y documentar el razonamiento utilizado.',topics:['Un servicio dejó de responder','Una dependencia presenta latencia','Un cambio afecta el comportamiento del servicio']}];
const typeLabel=p=>p.type==='curso'?`Curso · Nivel ${p.level}`:p.type==='caso'?'Caso de uso':'Herramienta';
let page=1,query='',filter='todo',currentItems=[],currentMode='catalog';
const crumbs=parts=>`<nav class="breadcrumbs" aria-label="Ruta de navegación"><a href="#/catalogo">Catálogo</a>${parts.map(p=>`<span aria-hidden="true">/</span>${p.href?`<a href="${p.href}">${esc(p.label)}</a>`:`<span aria-current="page">${esc(p.label)}</span>`}`).join('')}</nav>`;
const pagination=()=>`<nav class="catalog-pagination" aria-label="Páginas del catálogo"><span id="result-count" role="status"></span><div><button type="button" id="page-prev" aria-label="Página anterior">←</button><span id="page-count"></span><button type="button" id="page-next" aria-label="Página siguiente">→</button></div></nav>`;
function listView(title,description,items,mode,parts=[],initialFilter='todo'){
 currentItems=items;currentMode=mode;page=1;query='';filter=['todo','herramienta','curso','caso'].includes(initialFilter)?initialFilter:'todo';
 main.className='workspace-main catalog-page';
 main.innerHTML=`<div class="catalog-heading">${crumbs(parts)}<div class="heading-row"><div><h1 id="workspace-heading">${esc(title)}</h1><p>${esc(description)}</p></div><label class="catalog-search">${icon('search')}<input id="catalog-search" type="search" maxlength="120" placeholder="${mode==='catalog'?'Buscar una tecnología o una necesidad':'Buscar en este catálogo'}" aria-label="Buscar en el catálogo" autocomplete="off"></label></div></div>${mode==='products'?`<label class="filter-select">Mostrar<select id="filter-select" aria-label="Tipo de contenido">${[['todo','Todo'],['herramienta','Herramientas'],['curso','Cursos'],['caso','Casos de uso']].map(([id,label])=>`<option value="${id}" ${filter===id?'selected':''}>${label}</option>`).join('')}</select></label><div class="catalog-filters" role="group" aria-label="Tipo de contenido">${[['todo','Todo'],['herramienta','Herramientas'],['curso','Cursos'],['caso','Casos de uso']].map(([id,label])=>`<button type="button" data-filter="${id}" aria-pressed="${id===filter}">${label}</button>`).join('')}</div>`:''}<div class="catalog-grid" id="catalog-grid"></div>${pagination()}`;
 main.querySelector('#catalog-search').addEventListener('input',e=>{query=e.target.value;page=1;paginate();});
 main.querySelector('#filter-select')?.addEventListener('change',e=>{filter=e.target.value;page=1;main.querySelectorAll('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x.dataset.filter===filter)));paginate();});
 main.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.filter;page=1;main.querySelector('#filter-select').value=filter;main.querySelectorAll('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));paginate();}));
 main.querySelector('#page-prev').onclick=()=>{page--;paginate();};main.querySelector('#page-next').onclick=()=>{page++;paginate();};
 paginate();
}
function fitShell(){
 const h=window.visualViewport?.height||innerHeight;
 main.dataset.density=h<740?'compact':'comfortable';
 main.style.setProperty('--content-height',`${Math.max(160,h-document.querySelector('.workspace-header').getBoundingClientRect().bottom-24)}px`);
}
function paginate(){
 const grid=main.querySelector('#catalog-grid');if(!grid)return;
 fitShell();
 const width=grid.getBoundingClientRect().width;
 const cols=currentMode==='catalog'?(width>=1050?4:width>=780?3:width>=490?2:1):(width>=950?3:width>=580?2:1);
 const available=(window.visualViewport?.height||innerHeight)-grid.getBoundingClientRect().top-62;
 const minHeight=main.dataset.density==='compact'?140:(currentMode==='catalog'?245:170);
 const rows=Math.max(1,Math.min(3,Math.floor((available+14)/(minHeight+14))));
 const size=cols*rows;
 const items=currentItems.filter(x=>(filter==='todo'||x.type===filter)&&norm(x.title+' '+x.description).includes(norm(query)));
 const pages=Math.max(1,Math.ceil(items.length/size));page=Math.max(1,Math.min(page,pages));
 grid.style.setProperty('--columns',cols);
 grid.innerHTML=items.slice((page-1)*size,page*size).map(p=>{
  const href=currentMode==='catalog'?`#/catalogo/${p.id}`:p.id==='diagramas'?'#/herramientas/diagramas':`#/catalogo/observabilidad/${p.id}`;
  const locked=guest&&(currentMode==='catalog'?p.id!=='observabilidad':p.id!=='diagramas');
  return `<${locked?'div':'a'} class="catalog-card ${currentMode==='catalog'?'discipline-card':'product-card'} ${p.id==='mapeo-servicios'?'card-featured':''} ${locked?'is-locked':''}" ${locked?'aria-label="'+esc(p.title)+', sin acceso"':'href="'+href+'"'}>${currentMode==='catalog'?illustration(p.icon):`<div class="product-art">${productIllustration(p.icon)}</div>`}<div class="card-copy">${currentMode==='products'?`<div class="card-tags"><span>${typeLabel(p)}</span>${p.ready?'<span class="available-tag">Disponible</span>':''}</div>`:''}<h2>${esc(p.title)}</h2><p>${esc(p.description)}</p><span class="card-action">${locked?'Sin acceso':currentMode==='catalog'?'Explorar':p.id==='diagramas'?'Mis diagramas':'Ver detalle'} ${locked?'':icon('arrow')}</span></div></${locked?'div':'a'}>`;
 }).join('')||(currentItems.length?'<p class="catalog-empty">No encontramos coincidencias. Prueba con otro término.</p>':'<p class="catalog-empty">Este catálogo estará disponible próximamente.</p>');
 main.querySelector('#result-count').textContent=`${items.length} ${currentMode==='catalog'?'disciplinas':'opciones'}`;
 main.querySelector('#page-count').textContent=`${page} / ${pages}`;
 main.querySelector('#page-prev').disabled=page===1;main.querySelector('#page-next').disabled=page===pages;
}
const example={name:'Servicio de pagos',nodes:[{id:'web',label:'Canal web',type:'canal',parent:''},{id:'pagos',label:'Servicio de pagos',type:'servicio',parent:'web'},{id:'identidad',label:'Identidad',type:'servicio',parent:'pagos'},{id:'db',label:'Base de datos',type:'datos',parent:'pagos'},{id:'proveedor',label:'Proveedor de pagos',type:'externo',parent:'pagos'}]};
function diagramSvg(project){
 const levels=new Map();
 const depth=n=>{let d=0,p=n,seen=new Set([n.id]);while(p.parent){p=project.nodes.find(x=>x.id===p.parent);if(!p||seen.has(p.id))break;seen.add(p.id);d++;}levels.set(n.id,d);return d;};
 project.nodes.forEach(depth);const max=Math.max(0,...levels.values());const positions=new Map();const groups=[];
 for(let d=0;d<=max;d++){const nodes=project.nodes.filter(x=>levels.get(x.id)===d);for(let i=0;i<nodes.length;i+=3)groups.push(nodes.slice(i,i+3));}
 const canvasHeight=Math.max(500,groups.length*110+30);
 groups.forEach((nodes,row)=>nodes.forEach((n,i)=>positions.set(n.id,{x:(i+1)*720/(nodes.length+1),y:70+row*(canvasHeight-140)/Math.max(1,groups.length-1)})));
 const lines=project.nodes.filter(n=>positions.has(n.parent)).map(n=>{const a=positions.get(n.parent),b=positions.get(n.id);return `<path d="M${a.x} ${a.y+32}V${(a.y+b.y)/2}H${b.x}V${b.y-34}" fill="none" stroke="#527c68" stroke-width="1.5" marker-end="url(#diagram-arrow)"/>`;}).join('');
 const nodes=project.nodes.map(n=>{const p=positions.get(n.id);return `<g><rect x="${p.x-67}" y="${p.y-32}" width="134" height="64" rx="11" fill="#edf4ee" stroke="#6e9780"/><text x="${p.x}" y="${p.y-7}" font-size="10" text-anchor="middle" fill="#576560">${esc({canal:'Canal',servicio:'Servicio',datos:'Datos',externo:'Externo'}[n.type]||'Componente')}</text><text x="${p.x}" y="${p.y+13}" font-size="12" text-anchor="middle" fill="#243c39">${esc(n.label.slice(0,22))}</text></g>`;}).join('');
 return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 ${canvasHeight}" role="img" aria-label="Diagrama de ${esc(project.name)}"><title>${esc(project.name)}</title><defs><marker id="diagram-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="m0 0 10 5-10 5Z" fill="#527c68"/></marker></defs>${lines}${nodes}</svg>`;
}
function detail(p){
 main.className='workspace-main detail-page';main.dataset.detailPanel='resumen';fitShell();
 main.innerHTML=`${crumbs([{label:'Observabilidad',href:'#/catalogo/observabilidad'},{label:p.title}])}<nav class="detail-mobile-tabs" aria-label="Vista del producto">${[['resumen','Resumen'],['incluye','Qué incluye'],['ejemplo','Vista previa']].map(([id,label])=>`<button type="button" data-detail-panel="${id}" aria-pressed="${id==='resumen'}">${label}</button>`).join('')}</nav><div class="detail-layout"><section class="detail-copy"><span class="type-pill">${typeLabel(p)}</span><h1 id="workspace-heading">${esc(p.title)}</h1><p class="detail-intro">${p.ready?'Documenta cómo funciona un servicio y qué componentes necesita.':esc(p.description)}</p>${p.ready?`<ul class="outcome-list"><li>${icon('resource')}<div><h2>Servicios y componentes</h2><p>Identifica los elementos que forman parte del servicio.</p></div></li><li>${icon('dependency')}<div><h2>Relaciones y dependencias</h2><p>Visualiza cómo se conectan sus componentes.</p></div></li><li>${icon('map')}<div><h2>Diagramas para compartir</h2><p>Exporta tu diagrama y conserva el proyecto.</p></div></li></ul><div class="detail-actions"><a class="primary-action" href="#/herramientas/mapeo-servicios">Abrir herramienta ${icon('arrow')}</a><a class="text-action" href="#/herramientas/mapeo-servicios/ejemplo">Ver ejemplo</a></div><details class="how-to" open><summary>Cómo empezar</summary><ul><li>Define el servicio</li><li>Añade sus componentes</li><li>Conecta las dependencias</li></ul></details>`:`<p class="pending-status">En preparación</p><div class="preparing"><span class="type-pill">En preparación</span><h2>${p.type==='curso'?'Lo que aprenderás':'Qué podrás desarrollar'}</h2><p>${esc(p.outcome)}</p><ul>${(p.topics||['Identificar los elementos relevantes','Documentar su contexto y relaciones','Compartir los resultados con tu equipo']).map(t=>`<li>${esc(t)}</li>`).join('')}</ul><p class="availability-note">${p.type==='curso'?'El curso todavía no está habilitado.':'Esta opción todavía no está habilitada.'}</p></div>`}<a class="back-link" href="#/catalogo/observabilidad">← Volver a Observabilidad</a></section><section class="diagram-preview" aria-label="Vista de ejemplo"><div class="preview-title"><div><h2>${p.ready?'Vista de ejemplo':esc(p.title)}</h2><p>${p.ready?'Servicio de pagos':'Contenido del catálogo'}</p></div>${icon(p.icon)}</div>${p.ready?`<div class="diagram-image">${diagramSvg(example)}</div><p class="preview-caption">Un punto de partida para documentar tu servicio.</p>`:`<div class="large-product-art">${illustration(p.icon)}</div>`}</section></div>`;
 main.querySelectorAll('[data-detail-panel]').forEach(b=>b.onclick=()=>{main.dataset.detailPanel=b.dataset.detailPanel;main.querySelectorAll('[data-detail-panel]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));});
 const how=main.querySelector('.how-to');if(how&&(innerWidth<=700||innerHeight<=730))how.open=false;

}
let lastRenderedHash=location.hash,restoringHash=false;
function render(){
 if(restoringHash){restoringHash=false;return;}
 if(window.KoodariaResourceFlow?.hasUnsavedChanges()&&!confirm('Todavía hay cambios sin guardar. Espera al guardado o vuelve al editor para reintentar. ¿Salir de todos modos?')){restoringHash=true;location.hash=lastRenderedHash;return;}
 lastRenderedHash=location.hash;
 accountMenu?.removeAttribute('open');
 window.KoodariaResourceFlow?.unmount();document.body.classList.remove('resource-tool-open');
 const route=location.hash.slice(1)||'/catalogo';
 document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String((route.startsWith('/cursos')?'modulos':'servicios')===b.dataset.view)));
 document.querySelectorAll('[data-section]').forEach(b=>{if(b.dataset.section===(route.startsWith('/cursos')?'aprendizaje':route.startsWith('/herramientas')?'crear':'aplicaciones'))b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
 const [path,params='']=route.split('?');const bits=path.split('/').filter(Boolean);
 const diagramAliases=['diagramas','mapeo-recursos','mapeo-servicios','mapeo-dependencias'];
 if((bits[0]==='herramientas'&&diagramAliases.includes(bits[1]))||(bits[0]==='catalogo'&&bits[1]==='observabilidad'&&diagramAliases.includes(bits[2]))){if(path!=='/herramientas/diagramas'){location.replace('#/herramientas/diagramas');return;}document.body.classList.add('resource-tool-open');main.className='workspace-main resource-flow-page';main.removeAttribute('style');main.innerHTML='';window.KoodariaResourceFlow.mount(main);return;}
 if(guest&&!(bits[0]==='catalogo'&&(!bits[1]||(bits[1]==='observabilidad'&&!bits[2])))){location.hash='/catalogo';return;}
 if(bits[0]==='cursos'){listView('Cursos','Aprende observabilidad, desde sus fundamentos hasta su aplicación en operación.',products.filter(p=>p.type==='curso'),'products',[{label:'Cursos'}]);return;}
 if(bits[0]==='catalogo'&&bits[1]){
  const discipline=disciplines.find(d=>d.id===bits[1]);if(!discipline){location.hash='/catalogo';return;}
  if(bits[2]){const p=products.find(p=>p.id===bits[2]);if(discipline.id==='observabilidad'&&p){detail(p);return;}location.hash='/catalogo/'+discipline.id;return;}
  listView(discipline.title,discipline.id==='observabilidad'?'Conoce tus servicios, relaciona sus dependencias y aprende a investigarlos.':'Estamos preparando las herramientas y contenidos de esta disciplina.',discipline.id==='observabilidad'?products:[],'products',[{label:discipline.title}],new URLSearchParams(params).get('tipo')||'todo');
  if(discipline.id!=='observabilidad')main.querySelector('#catalog-grid').innerHTML='<div class="catalog-empty">Este catálogo estará disponible próximamente.<br><a href="#/catalogo">Volver al catálogo</a></div>';
  return;
 }
 listView('¿Qué quieres desarrollar?','Aprende, documenta y lleva tus conocimientos a la práctica.',disciplines,'catalog');
}
window.addEventListener('hashchange',render);
let resizeFrame;const resize=()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(main.querySelector('#catalog-grid'))paginate();else fitShell();});};
window.addEventListener('resize',resize);window.visualViewport?.addEventListener('resize',resize);
document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{location.hash=b.dataset.view==='modulos'?'/cursos':'/catalogo';}));
document.querySelectorAll('[data-section]').forEach(b=>b.addEventListener('click',()=>{const route={inicio:'/catalogo',aplicaciones:'/catalogo',biblioteca:'/cursos',aprendizaje:'/cursos',crear:'/herramientas/diagramas'}[b.dataset.section];if(route)location.hash=route;}));
for(const section of (guest?['asistente','favoritos','consola','crear','biblioteca','aprendizaje']:['asistente','favoritos','consola'])){const button=document.querySelector(`[data-section="${section}"]`);if(button){button.disabled=true;button.title=button.getAttribute('aria-label')+' · Próximamente';}}
if(guest)document.querySelector('[data-view=modulos]')?.setAttribute('disabled','');
render();
})();
