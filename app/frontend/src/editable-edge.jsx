import React,{useMemo,useRef} from 'react';
import {BaseEdge,getBezierPath,getSmoothStepPath,getStraightPath,useReactFlow} from '@xyflow/react';
// Relative offsets preserve the shape when either endpoint moves.
export default function EditableEdge(p){
 const flow=useReactFlow(),drag=useRef(null),route=p.data.route||'smoothstep';
 const [base,lx,ly]=(route==='straight'?getStraightPath:route==='default'?getBezierPath:getSmoothStepPath)({...p,borderRadius:route==='step'?0:10});
 const anchors=useMemo(()=>{const path=document.createElementNS('http://www.w3.org/2000/svg','path');path.setAttribute('d',base);return [.25,.5,.75].map(f=>{const q=path.getPointAtLength(path.getTotalLength()*f);return {x:q.x,y:q.y};});},[base]);
 const offsets=p.data.bends||[{x:0,y:0},{x:0,y:0},{x:0,y:0}],points=[{x:p.sourceX,y:p.sourceY},...anchors.map((v,i)=>({x:v.x+offsets[i].x,y:v.y+offsets[i].y})),{x:p.targetX,y:p.targetY}];
 let path=base;
 if(offsets.some(v=>v.x||v.y)){
  path=`M ${points[0].x},${points[0].y}`;
  for(let i=0;i<points.length-1;i++){const a=points[Math.max(0,i-1)],b=points[i],c=points[i+1],d=points[Math.min(points.length-1,i+2)];
   if(route==='straight')path+=` L ${c.x},${c.y}`;
   else if(route==='step'||route==='smoothstep'){const [segment]=getSmoothStepPath({sourceX:b.x,sourceY:b.y,targetX:c.x,targetY:c.y,sourcePosition:Math.abs(c.x-b.x)>Math.abs(c.y-b.y)?(c.x>b.x?'right':'left'):(c.y>b.y?'bottom':'top'),targetPosition:Math.abs(c.x-b.x)>Math.abs(c.y-b.y)?(c.x>b.x?'left':'right'):(c.y>b.y?'top':'bottom'),borderRadius:route==='step'?0:10,offset:0});path+=segment.replace(/^M[^LQCHV]+/,'');}
   else path+=` C ${b.x+(c.x-a.x)/6},${b.y+(c.y-a.y)/6} ${c.x-(d.x-b.x)/6},${c.y-(d.y-b.y)/6} ${c.x},${c.y}`;
  }
 }
 const labelWidth=useMemo(()=>{const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font='12px '+getComputedStyle(document.documentElement).fontFamily;return ctx.measureText(String(p.label||'')).width;},[p.label]);
 const labelPoint=offsets.some(v=>v.x||v.y)?points[2]:{x:lx,y:ly};
 const move=(event,index)=>{if(drag.current!==index)return;const q=flow.screenToFlowPosition({x:event.clientX,y:event.clientY});const next=offsets.map((v,i)=>i===index?{x:Math.max(-10000,Math.min(10000,q.x-anchors[i].x)),y:Math.max(-10000,Math.min(10000,q.y-anchors[i].y))}:v);p.data.onBend(p.id,next);};
 const finish=()=>{drag.current=null;p.data.onBendDrag(false);};
 return <><BaseEdge id={p.id} path={path} markerStart={p.markerStart} markerEnd={p.markerEnd} style={p.style} interactionWidth={18}/>{p.label&&<g className="editable-edge-label" pointerEvents="none" transform={`translate(${labelPoint.x},${labelPoint.y})`}><rect x={-labelWidth/2-5} y={-10} width={labelWidth+10} height={20} rx={3} style={{fill:p.data.labelBackground}}/><text textAnchor="middle" y={4} style={{fill:p.data.labelInk,fontSize:12}}>{p.label}</text></g>}{p.selected&&points.slice(1,4).map((q,i)=><circle key={i} className="edge-bend nodrag nopan" data-bend={i} cx={q.x} cy={q.y} r={5} tabIndex={0} role="button" aria-label={'Ajustar recorrido '+['25%','50%','75%'][i]} onPointerDown={e=>{e.preventDefault();e.stopPropagation();e.currentTarget.setPointerCapture(e.pointerId);drag.current=i;p.data.onBendDrag(true);}} onPointerMove={e=>move(e,i)} onPointerUp={finish} onPointerCancel={finish} onLostPointerCapture={finish} onKeyDown={e=>{const delta={ArrowLeft:[-10,0],ArrowRight:[10,0],ArrowUp:[0,-10],ArrowDown:[0,10]}[e.key];if(delta){e.preventDefault();e.stopPropagation();p.data.onBend(p.id,offsets.map((v,j)=>i===j?{x:Math.max(-10000,Math.min(10000,v.x+delta[0])),y:Math.max(-10000,Math.min(10000,v.y+delta[1]))}:v));}}}><title>Arrastra para ajustar el recorrido. Flechas: mover 10 unidades.</title></circle>)}</>;
}
