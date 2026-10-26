import {copyGraph} from './connection-style.js';
export function extractGraph(document,selected){
 const ids=new Set(selected);let count=-1;while(count!==ids.size){count=ids.size;document.nodes.filter(n=>ids.has(n.parentId)).forEach(n=>ids.add(n.id));document.edges.filter(e=>e.relation==='hosts'&&ids.has(e.source)).forEach(e=>ids.add(e.target));}
 return {name:document.name,nodes:document.nodes.filter(n=>ids.has(n.id)).map(n=>({...n,...(!ids.has(n.parentId)?{parentId:undefined,extent:undefined}:{})})),edges:document.edges.filter(e=>ids.has(e.source)&&ids.has(e.target))};
}
export function pasteGraph(document,position){
 if(!document||!Array.isArray(document.nodes)||!Array.isArray(document.edges)||!document.nodes.length||document.nodes.length>200||document.edges.length>500)throw Error('Contenido no válido.');
 const value=copyGraph(structuredClone(document)),roots=value.nodes.filter(n=>!n.parentId),x=Math.min(...roots.map(n=>n.position.x)),y=Math.min(...roots.map(n=>n.position.y)),dx=position.x-x,dy=position.y-y;
 value.nodes=value.nodes.map(n=>({...n,selected:true,position:n.parentId?n.position:{x:n.position.x+dx,y:n.position.y+dy}}));value.edges=value.edges.map(e=>({...e,...(e.routePoints?{routePoints:e.routePoints.map(p=>({x:p.x+dx,y:p.y+dy}))}:{})}));return value;
}
