import {reportFault} from './error-center.jsx';
const root='/bienvenida/api/discovery';
export async function discoveryApi(path='',method='GET',body,signal){
 const r=await fetch(root+path,{method,credentials:'same-origin',signal,headers:{'Content-Type':'application/json','X-CSRF-Token':document.querySelector('meta[name=csrf-token]').content},...(body?{body:JSON.stringify(body)}:{})});
 if(r.status===204)return null;const data=await r.json();if(!r.ok){const e=Object.assign(new Error(data.error||'No se pudo completar la operación.'),{data});reportFault({code:data.error_code||'KOD-SYS-001',message:e.message,reference:data.reference,action:data.action});throw e;}return data;
}
