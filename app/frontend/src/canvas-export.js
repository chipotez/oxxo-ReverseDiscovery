import {toPng} from 'html-to-image';
export async function captureDiagram(stage,flow){
 const viewport=stage.querySelector('.react-flow__viewport');
 const nodes=flow.getNodes(),bounds=nodes.length?flow.getNodesBounds(nodes):{x:0,y:0,width:500,height:240};
 let x=bounds.x,y=bounds.y,right=x+bounds.width,bottom=y+bounds.height;
 for(const edge of viewport.querySelectorAll('.react-flow__edge')){const b=edge.getBBox();x=Math.min(x,b.x);y=Math.min(y,b.y);right=Math.max(right,b.x+b.width);bottom=Math.max(bottom,b.y+b.height);}
 const width=Math.ceil(right-x+48),height=Math.ceil(bottom-y+48),ratio=Math.min(2,Math.sqrt(7900000/(width*height)),8000/width,8000/height);
 const image=await toPng(viewport,{width,height,pixelRatio:ratio,skipFonts:true,backgroundColor:getComputedStyle(document.documentElement).getPropertyValue('--surface').trim()||'#f8faf7',style:{transform:`translate(${24-x}px,${24-y}px) scale(1)`,width:width+'px',height:height+'px'},filter:node=>!node.classList?.contains('resource-port')&&!node.classList?.contains('edge-bend')&&!node.classList?.contains('react-flow__edgeupdater')&&!node.classList?.contains('standard-ribbon')&&!node.classList?.contains('hosted-resources')&&!node.classList?.contains('react-flow__resize-control')});
 return {image};
}
