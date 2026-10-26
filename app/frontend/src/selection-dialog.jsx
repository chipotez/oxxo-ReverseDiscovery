import React,{useEffect,useId,useRef} from 'react';
/** Shared shell for catalog selectors. Keep header/footer outside the paginated body. */
export default function SelectionDialog({title,description,children,footer,onClose,wide=true,closeLabel="Cerrar clasificación"}){
 const ref=useRef(null),titleId=useId(),descriptionId=useId();
 useEffect(()=>{const previous=document.activeElement;ref.current.showModal();return()=>previous?.focus?.({preventScroll:true});},[]);
 return <dialog ref={ref} className={'selection-dialog '+(wide?'selection-dialog-wide':'selection-dialog-compact')} aria-labelledby={titleId} aria-describedby={description?descriptionId:undefined} onCancel={e=>{e.preventDefault();onClose();}}><header className="selection-dialog-header"><div><h2 id={titleId}>{title}</h2>{description&&<p id={descriptionId}>{description}</p>}</div><button className="icon-button" aria-label={closeLabel} onClick={onClose}>×</button></header><div className="selection-dialog-body">{children}</div><footer className="selection-dialog-footer">{footer}</footer></dialog>;
}
