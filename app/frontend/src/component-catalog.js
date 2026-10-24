import componentCatalog from './component-catalog.json';
import diagrams from './diagram-catalog.json';
export const resourcesByKind=Object.fromEntries(componentCatalog.resources.map(r=>[r.kind,r]));
export const taxonomy=componentCatalog.categories.map(c=>({...c,children:c.children.map(s=>({...s,types:s.kinds.map(k=>resourcesByKind[k].label)}))}));
export const diagramCatalog={...diagrams,categories:[...componentCatalog.categories.map(({id,label,icon})=>({id,label,icon})),{id:'visual',label:'Organización visual',icon:'collection'}],resources:[...componentCatalog.resources,...diagrams.visualResources]};
export const normalized=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export function matchesResource(resource,query='',provider=''){
 return (!provider||resource.providers.includes(provider))&&(!query||normalized([resource.label,...resource.technologies,...resource.providers].join(' ')).includes(normalized(query)));
}
export function componentSections(resource){
 const category=componentCatalog.categories.find(c=>c.id===resource.category);
 return [
 {id:'identification',label:'Identificación de entidad',icon:'identity',description:'Datos para identificar y ubicar el componente.',fields:[{id:'ci',label:'ID único / CI',description:'Identificador en el inventario o catálogo.'},{id:'name',label:'Nombre',description:'Nombre que identifica este componente.'},{id:'type',label:'Tipo de componente',description:resource.label+'.'},{id:'technology',label:'Tecnología y versión',description:'Producto y versión utilizados'+(resource.technologies.length?'; por ejemplo, '+resource.technologies.slice(0,4).join(', '):'')+'.'},{id:'provider',label:'Proveedor',description:'Fabricante, proveedor o responsable de la plataforma.'},{id:'location',label:'Entorno y ubicación',description:'Ambiente, sede, datacenter o región.'},{id:'owner',label:'Responsable',description:'Persona o equipo responsable del componente.'}]},
 {id:'controls',label:'Capacidades y controles',icon:'shield',description:'Funciones y requisitos aplicables a este tipo de componente.',fields:category.capabilities},
 {id:'evidence',label:'Evidencia operativa',icon:'note',description:'Datos que permiten documentar la implementación y su estado.',fields:[{id:'product',label:'Producto / tecnología',description:'Solución y versión que cubren la capacidad.'},{id:'implementation',label:'Implementación',description:'Mecanismo nativo, API, agente o procedimiento aplicable.'},{id:'state',label:'Estado operativo',description:'Estado observado, con fecha de la última revisión.'},{id:'evidence',label:'Evidencia',description:'Fuente, fecha y resultado de la validación.'},{id:'compliance',label:'Cumplimiento',description:'Cumple, no cumple, excepción o no aplica, con justificación.'}]},
 {id:'relationships',label:'Relaciones de arquitectura',icon:'topology',description:'Relaciones del componente con el resto del servicio.',fields:[{id:'belongs',label:'Pertenece a',description:'Servicio, organización o grupo que contiene el componente.'},{id:'depends',label:'Depende de',description:'Componentes y servicios necesarios para su operación.'},{id:'connected',label:'Conectado a',description:'Destinos y canales con los que se comunica.'},{id:'used',label:'Utilizado por',description:'Aplicaciones, personas o servicios que lo consumen.'},{id:'managed',label:'Administrado / protegido por',description:'Plataformas y equipos que lo gestionan. Registrar fuente y grado de confianza.'}]}];
}
export default componentCatalog;
