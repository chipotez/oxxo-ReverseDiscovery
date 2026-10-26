import {nodeSummary} from './resource-documentation.js';
// Hosting is the canonical relationship; containment is a derived canvas layout.
// Persist absolute coordinates so older clients and detached components remain usable.
export function resourceLayout(nodes,edges){
 const byId=new Map(nodes.map(n=>[n.id,n])),parents=new Map(),children=new Map(),sizes=new Map(),absolute=new Map(),result=[];
 for(const e of edges)if(e.relation==='hosts'&&byId.has(e.source)&&byId.has(e.target)&&!parents.has(e.target)){parents.set(e.target,e.source);children.set(e.source,[...(children.get(e.source)||[]),e.target]);}
 const base=id=>62+14*nodeSummary(byId.get(id).data).length;
 const measure=(id,trail=new Set())=>{if(sizes.has(id))return sizes.get(id);if(trail.has(id))return {width:320,height:76};const next=new Set([...trail,id]),kids=(children.get(id)||[]).map(k=>measure(k,next));const size={width:kids.length?Math.max(320,...kids.map(s=>s.width))+20:320,height:base(id)+(kids.length?8+kids.reduce((v,s)=>v+s.height+8,0):0)};sizes.set(id,size);return size;};
 const place=(n,parent,position,trail=new Set())=>{if(trail.has(n.id)||absolute.has(n.id))return;const size=measure(n.id),parentAbs=absolute.get(parent||n.parentId);absolute.set(n.id,{x:position.x+(parentAbs?.x||0),y:position.y+(parentAbs?.y||0)});result.push({...n,zIndex:n.type==='resourceGroup'?0:2,parentId:parent||n.parentId,extent:parent?'parent':n.extent,position,data:{...n.data,visualDepth:parent?(result.find(v=>v.id===parent)?.data.visualDepth||0)+1:0},draggable:!parent,style:n.type==='resource'?{...n.style,...size}:n.style});let y=base(n.id)+8;for(const child of children.get(n.id)||[]){place(byId.get(child),n.id,{x:10,y},new Set([...trail,n.id]));y+=measure(child).height+8;}};
 for(const n of nodes)if(!parents.has(n.id))place(n,null,n.position);
 for(const n of nodes)if(!absolute.has(n.id))place(n,null,n.position);
 return {nodes:result,absolute,sizes,parents};
}
