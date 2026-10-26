import React from 'react';
export default function HostedResources({id,context}){
 const count=context.edges.filter(e=>e.source===id&&e.relation==='hosts').length;
 return <div className="hosted-resources nodrag nopan" onClick={e=>e.stopPropagation()}>{count>0&&<button title={context.nodes.find(n=>n.id===id)?.data.collapsed?'Desplegar componentes':'Plegar componentes'} aria-label={context.nodes.find(n=>n.id===id)?.data.collapsed?'Desplegar componentes':'Plegar componentes'} onClick={()=>context.onToggle(id)}>{context.nodes.find(n=>n.id===id)?.data.collapsed?'▸':'▾'} {count}</button>}<button className="hosted-add" aria-label={'Añadir componente alojado en '+context.nodes.find(n=>n.id===id)?.data.label} title={'Añadir componente alojado'+(count?` · ${count} dentro`:'')} onClick={()=>context.onAdd(id)}>+</button></div>;
}
