// Semantic options are persisted; presentation is derived, never arbitrary CSS.
export const connectionColors={auto:'Original',forest:'Verde',graphite:'Grafito',blue:'Azul',purple:'Violeta',amber:'Ámbar',rose:'Rosa'};
const colors={forest:'#357665',graphite:'#627778',blue:'#407db0',purple:'#8666ac',amber:'#9a761c',rose:'#ad6670'};
export function connectionAppearance(edge){
 const pattern=edge.pattern||'solid',arrows=edge.arrows||'end',color=colors[edge.color];
 const marker={type:'arrowclosed',...(color?{color}:{})};
 return {...edge,style:{stroke:color,strokeDasharray:({dashed:'7 5',dotted:'1 5',dashdot:'8 4 1 4',longdash:'14 6'})[pattern],strokeLinecap:'round'},markerStart:['start','both'].includes(arrows)?marker:null,markerEnd:['end','both'].includes(arrows)?marker:null};
}
export function copyGraph(document){
 const ids=new Map(document.nodes.map(n=>[n.id,crypto.randomUUID()]));
 return {...document,nodes:document.nodes.map(n=>({...n,id:ids.get(n.id),...(n.parentId?{parentId:ids.get(n.parentId)}:{})})),edges:document.edges.map(e=>({...e,id:crypto.randomUUID(),source:ids.get(e.source),target:ids.get(e.target)}))};
}
