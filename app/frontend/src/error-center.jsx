import React,{useEffect,useRef,useState} from 'react';
import catalog from './error-catalog.json';
export function reportFault(value){window.dispatchEvent(new CustomEvent('koodaria:fault',{detail:value}));}
export default function ErrorCenter(){
 const [fault,setFault]=useState(null),[copied,setCopied]=useState(false);const ref=useRef(null),prior=useRef(null),last=useRef(null);
 useEffect(()=>{const receive=e=>{if(last.current===e.detail.reference)return;last.current=e.detail.reference;setCopied(false);setFault(e.detail);};window.addEventListener('koodaria:fault',receive);return()=>window.removeEventListener('koodaria:fault',receive);},[]);
 useEffect(()=>{if(fault&&!ref.current.open){prior.current=document.activeElement;ref.current.showModal();}},[fault]);
 const close=()=>{ref.current.close();setFault(null);prior.current?.focus?.({preventScroll:true});};
 const info=catalog[fault?.code]||catalog['KOD-SYS-001'];
 return <dialog ref={ref} className="resource-dialog fault-dialog" aria-labelledby="fault-title" aria-describedby="fault-message" onCancel={e=>{e.preventDefault();close();}}><header><h2 id="fault-title">No se pudo completar la operación</h2><button aria-label="Cerrar aviso de error" onClick={close}>×</button></header><p id="fault-message">{fault?.message||info.message}</p><p className="fault-action">{fault?.action||info.action}</p><dl><dt>Código</dt><dd>{fault?.code}</dd><dt>Referencia</dt><dd>{fault?.reference}</dd></dl><footer><button onClick={async()=>{try{await navigator.clipboard.writeText((fault?.code||'')+' · '+(fault?.reference||''));setCopied(true);}catch{setCopied(false);}}}>{copied?'Copiado':'Copiar referencia'}</button><button autoFocus className="resource-primary" onClick={close}>Entendido</button></footer></dialog>;
}
