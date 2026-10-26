import {useLayoutEffect,useRef,useState} from 'react';

// Count real, fixed-height rows in the space left by the panel's own controls.
export function rowsThatFit(height,rowHeight,gap=0,max=25){
 return Math.max(1,Math.min(max,Math.floor((height+gap)/(rowHeight+gap))));
}
export function useExplorerLayout(dependencies){
 const windowRef=useRef(null),catalogList=useRef(null),resultList=useRef(null);
 const [height,setHeight]=useState(440),[catalogCount,setCatalogCount]=useState(4),[resultCount,setResultCount]=useState(6),[compact,setCompact]=useState(false);
 useLayoutEffect(()=>{
  let frame;
  const fit=()=>{
   const viewport=window.visualViewport?.height||innerHeight,root=windowRef.current;
   setCompact(viewport<600);
   if(!root)return;
   const boundary=root.closest('.diagram-integrations')?.getBoundingClientRect().bottom||viewport;
   setHeight(Math.max(180,Math.floor(Math.min(viewport,boundary)-root.getBoundingClientRect().top-16)));
   for(const [ref,setCount,rowClass,max] of [[catalogList,setCatalogCount,'--api-row-height',25],[resultList,setResultCount,'--result-row-height',25]]){
    const list=ref.current;if(!list||!list.getClientRects().length)continue;
    const style=getComputedStyle(list),rowHeight=parseFloat(style.getPropertyValue(rowClass)),gap=parseFloat(style.rowGap)||0;
    if(rowHeight>0)setCount(rowsThatFit(list.clientHeight,rowHeight,gap,max));
   }
  };
  const schedule=()=>{cancelAnimationFrame(frame);frame=requestAnimationFrame(fit);};
  const observer=new ResizeObserver(schedule);
  [windowRef.current,catalogList.current,resultList.current].filter(Boolean).forEach(el=>observer.observe(el));
  schedule();window.addEventListener('resize',schedule);window.visualViewport?.addEventListener('resize',schedule);
  return()=>{cancelAnimationFrame(frame);observer.disconnect();window.removeEventListener('resize',schedule);window.visualViewport?.removeEventListener('resize',schedule);};
 },dependencies);
 return {windowRef,catalogList,resultList,height,catalogCount,resultCount,compact};
}
