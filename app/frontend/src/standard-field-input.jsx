import React from 'react';
export default function StandardFieldInput({field,value,onChange}){
 const common={'aria-label':field.label,value:value??'',onChange:e=>onChange(e.target.value)};
 if(field.format==='select')return <select {...common}><option value="">Sin documentar</option>{field.options.map(v=><option key={v} value={v}>{v}</option>)}</select>;
 if(field.format==='boolean')return <select {...common} value={value===true?'true':value===false?'false':''} onChange={e=>onChange(e.target.value===''?'':e.target.value==='true')}><option value="">Sin documentar</option><option value="true">Sí</option><option value="false">No</option></select>;
 return <input {...common} type={field.format==='number'?'number':field.format==='date'?'date':'text'} maxLength={field.id==='name'?100:500} step={field.format==='number'?'any':undefined} placeholder="Sin documentar" onChange={e=>onChange(field.format==='number'&&e.target.value!==''?Number(e.target.value):e.target.value)}/>;
}
