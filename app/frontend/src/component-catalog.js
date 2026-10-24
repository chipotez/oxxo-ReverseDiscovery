import componentCatalog from './component-catalog.json';
import diagrams from './diagram-catalog.json';
import genericModel from './generic-standard-model.json';
export const resourcesByKind=Object.fromEntries(componentCatalog.resources.map(r=>[r.kind,r]));
export const taxonomy=componentCatalog.categories.map(c=>({...c,children:c.children.map(s=>({...s,kinds:s.kinds.filter(k=>!resourcesByKind[k].legacy),types:s.kinds.filter(k=>!resourcesByKind[k].legacy).map(k=>resourcesByKind[k].label)}))}));
export const diagramCatalog={...diagrams,categories:[...componentCatalog.categories.map(({id,label,icon})=>({id,label,icon})),{id:'visual',label:'Organización visual',icon:'collection'}],resources:[...componentCatalog.resources.filter(r=>!r.legacy),...diagrams.visualResources]};
export const normalized=value=>value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export function matchesResource(resource,query='',provider=''){
 return (!provider||resource.providers.includes(provider))&&(!query||normalized([resource.label,...resource.technologies,...resource.providers].join(' ')).includes(normalized(query)));
}
export function componentSections(resource){
 const sections=structuredClone(genericModel.sections);sections[0].fields=structuredClone(genericModel.identificationOverrides[resource.kind]||sections[0].fields);sections[1].fields=componentCatalog.categories.find(c=>c.id===resource.category).capabilities;return sections;
}
export default componentCatalog;
