import React from 'react';
export default function HostedResources({id,context}){
 const count=context.edges.filter(e=>e.source===id&&e.relation==='hosts').length;
 return <div className="hosted-resources nodrag nopan" onClick={e=>e.stopPropagation()}><span className="hosted-count">{count?`${count} componente${count===1?'':'s'} dentro`:''}</span><button className="hosted-add" aria-label={'Añadir componente alojado en '+context.nodes.find(n=>n.id===id)?.data.label} title="Añadir componente alojado" onClick={()=>context.onAdd(id)}>+</button></div>;
}
