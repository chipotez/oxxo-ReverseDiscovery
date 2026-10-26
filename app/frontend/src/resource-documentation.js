import model from './server-standard-model.json';
import operating from './operating-standards.json';
import {resourcesByKind,componentSections} from './component-catalog.js';
export const serverKind=kind=>['servidor','virtual'].includes(kind);
export const instanceKey=data=>serverKind(data.kind)?'server_instance':'component_instance';
export const sectionsFor=data=>data.resource_schema?.sections|| (serverKind(data.kind)?model.sections.map(s=>s.id==='controls'?{...s,fields:operating.functions}:s):resourcesByKind[data.kind]?componentSections(resourcesByKind[data.kind]):[]);
export const documented=v=>(typeof v==='number'&&Number.isFinite(v))||typeof v==='boolean'||typeof v==='string'&&!!v.trim()&&!/^(no aplica|n\/a|na)\s*[:\-]?\s*$/i.test(v.trim())&&!['sin documentar','desconocido'].includes(v.trim().toLowerCase());
export const related=(id,field,edges)=>edges.filter(e=>field==='belongs'?(e.relation==='hosts'&&e.target===id)||(e.relation==='belongs'&&e.source===id):field==='used'?(e.relation==='used'&&e.source===id)||(e.relation==='depends'&&e.target===id):e.relation===field&&(e.source===id||(field==='connected'&&e.target===id)));
export function documentation(data,section,id,edges=[]){
 let fields=sectionsFor(data).find(s=>s.id===section)?.fields||[];
 if(section==='controls'&&serverKind(data.kind))fields=[...(data.standard?.definition.requirements||operating.functions),...fields.filter(f=>f.custom)];
 const rules=section==='controls'?data.standard?.definition.requirements:data.standard?.definition.server_model?.[section];
 if(rules)fields=fields.filter(f=>f.custom?f.required:['required','conditional'].includes((rules.find(r=>r.id===f.id)||(['environment','criticality'].includes(f.id)?rules.find(r=>r.id==='context'):null))?.level));
 fields=fields.filter(f=>!f.custom||f.required);
 const values=data[instanceKey(data)]?.[section]||{};
 const coverage=data.standard?.coverage||[];
 const filled=fields.filter(f=>{if(section==='controls'){const c=coverage.find(v=>v.id===f.id)||values[f.id];return c&&c.status!=='unknown'&&documented(c.evidence);}return documented(values[f.id])||(section==='relationships'&&related(id,f.id,edges).length>0);}).length;
 const total=fields.length,percent=total?Math.round(100*filled/total):0;
 return {filled,total,percent,state:total&&filled===total?'complete':percent<50?'missing':'progress',mark:total&&filled===total?'✓':percent<50?'!':'◐'};
}

export function nodeSummary(data){const fields=data[instanceKey(data)]?.identification||{};const values=[fields.hostname||fields.name,fields.environment,fields.criticality,fields.technology||data.technology,fields.location||data.location,(fields.address||data.address)&&((fields.address||data.address)+((fields.port||data.port)?' · '+(fields.port||data.port):''))].filter(Boolean).filter((v,i,all)=>v!==data.label&&all.indexOf(v)===i).slice(0,3);const label=resourcesByKind[data.kind]?.label;return values.length?values:label&&label!==data.label?[label]:[];}
