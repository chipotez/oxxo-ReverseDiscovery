import React from 'react';
import {createRoot} from 'react-dom/client';
import SelectionDialog from './selection-dialog.jsx';
let queue=Promise.resolve();
export function confirmDialog({title='Confirmar cambio',message,confirmLabel='Continuar',cancelLabel='Cancelar'}){
 const result=queue.then(()=>new Promise(resolve=>{const host=document.createElement('div');document.body.append(host);const root=createRoot(host);const finish=value=>{root.unmount();host.remove();resolve(value);};root.render(<SelectionDialog title={title} wide={false} closeLabel="Cancelar y cerrar" onClose={()=>finish(false)} footer={<><button onClick={()=>finish(false)}>{cancelLabel}</button><button className="resource-primary" onClick={()=>finish(true)}>{confirmLabel}</button></>}><p className="confirmation-message">{message}</p></SelectionDialog>);}));queue=result.then(()=>{},()=>{});return result;
}
