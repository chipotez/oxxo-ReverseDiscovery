import {useEffect,useRef} from 'react';
// One dispatcher: a single Escape dismisses only the foremost interaction layer.
const layers=[];
export function useEscapeLayer(active,close,priority=0){const latest=useRef(close);latest.current=close;useEffect(()=>{if(!active)return;const entry={close:()=>latest.current(),priority,focus:document.activeElement};layers.push(entry);return()=>{const index=layers.indexOf(entry);if(index>=0)layers.splice(index,1);if(entry.focus?.isConnected)entry.focus.focus?.({preventScroll:true});};},[active,priority]);}
const selects=new WeakSet();
window.addEventListener('pointerdown',e=>{if(e.target.tagName==='SELECT')selects.add(e.target);},true);
window.addEventListener('change',e=>selects.delete(e.target),true);
window.addEventListener('keydown',e=>{
 if(e.target.tagName==='SELECT'&&['ArrowDown','ArrowUp',' ','Enter','F4'].includes(e.key))selects.add(e.target);
 if(e.key!=='Escape'||e.isComposing||e.repeat)return;
 if(e.target.tagName==='SELECT'&&selects.has(e.target)){selects.delete(e.target);return;}
 const details=e.target.closest?.('details[open]');if(details){e.preventDefault();e.stopImmediatePropagation();details.open=false;details.querySelector('summary')?.focus();return;}
 const modal=[...document.querySelectorAll('dialog[open]')].at(-1);
 if(modal){e.preventDefault();e.stopImmediatePropagation();const cancel=new Event('cancel',{cancelable:true});if(modal.dispatchEvent(cancel))modal.close();return;}
 const entry=[...layers].sort((a,b)=>a.priority-b.priority||layers.indexOf(a)-layers.indexOf(b)).at(-1);
 if(entry){e.preventDefault();e.stopImmediatePropagation();entry.close();}
},true);
