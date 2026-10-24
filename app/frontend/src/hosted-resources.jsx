import React from 'react';
export default function HostedResources({id,context}){
 const count=context.edges.filter(e=>e.source===id&&e.relation==='hosts').length;
 return <div className="hosted-resources nodrag nopan" onClick={e=>e.stopPropagation()}><button className="hosted-add" aria-label={'Añadir componente alojado en '+context.nodes.find(n=>n.id===id)?.data.label} title={'Añadir componente alojado'+(count?` · ${count} dentro`:'')} onClick={()=>context.onAdd(id)}>+</button></div>;
}
