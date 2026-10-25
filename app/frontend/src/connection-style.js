// Persist semantic options only; never arbitrary SVG/CSS from a document.
export function connectionAppearance(edge){
 const pattern=edge.pattern||'solid',arrows=edge.arrows||'end';
 const marker={type:'arrowclosed'};
 return {...edge,style:{strokeDasharray:pattern==='dashed'?'7 5':pattern==='dotted'?'1 5':undefined,strokeLinecap:'round'},markerStart:['start','both'].includes(arrows)?marker:null,markerEnd:['end','both'].includes(arrows)?marker:null};
}
