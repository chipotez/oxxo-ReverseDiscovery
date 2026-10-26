// Stable resource IDs and leaf-level preconditions; arrays (e.g. bends) are atomic.
const clone=v=>JSON.parse(JSON.stringify(v));
export const equal=(a,b)=>{if(a===b)return true;if(!a||!b||typeof a!=='object'||typeof b!=='object'||Array.isArray(a)!==Array.isArray(b))return false;const keys=Object.keys(a);return keys.length===Object.keys(b).length&&keys.every(k=>Object.hasOwn(b,k)&&equal(a[k],b[k]));};
const slot=(o,k)=>Object.hasOwn(o,k)?{exists:true,value:o[k]}:{exists:false};
export function graphDelta(before,after){
 const changes=[];
 const walk=(a,b,collection,id,path=[])=>{for(const k of new Set([...Object.keys(a),...Object.keys(b)])){const x=slot(a,k),y=slot(b,k);if(equal(x,y))continue;if(x.exists&&y.exists&&x.value&&y.value&&typeof x.value==='object'&&typeof y.value==='object'&&!Array.isArray(x.value)&&!Array.isArray(y.value))walk(x.value,y.value,collection,id,[...path,k]);else changes.push({collection,id,path:[...path,k],before:clone(x),after:clone(y)});}};
 if(before.name!==after.name)changes.push({collection:'document',id:null,path:['name'],before:{exists:true,value:before.name},after:{exists:true,value:after.name}});
 for(const collection of ['nodes','edges']){const old=new Map(before[collection].map(v=>[v.id,v])),next=new Map(after[collection].map(v=>[v.id,v]));for(const id of new Set([...old.keys(),...next.keys()])){if(!old.has(id)||!next.has(id))changes.push({collection,id,path:[],before:old.has(id)?{exists:true,value:clone(old.get(id))}:{exists:false},after:next.has(id)?{exists:true,value:clone(next.get(id))}:{exists:false}});else if(collection==='nodes'&&old.get(id).data.kind!==next.get(id).data.kind)changes.push({collection,id,path:['data'],before:{exists:true,value:clone(old.get(id).data)},after:{exists:true,value:clone(next.get(id).data)}});else walk(old.get(id),next.get(id),collection,id);}}
 return changes;
}
export function applyDelta(document,changes){
 const value=clone(document);
 for(const c of changes){let target=c.collection==='document'?value:value[c.collection].find(v=>v.id===c.id);if(!c.path.length){const actual=target?{exists:true,value:target}:{exists:false};if(!equal(actual,c.before))throw Error('El recurso cambió.');if(c.after.exists){if(target)value[c.collection][value[c.collection].indexOf(target)]=clone(c.after.value);else value[c.collection].push(clone(c.after.value));}else value[c.collection]=value[c.collection].filter(v=>v.id!==c.id);continue;}if(!target)throw Error('El recurso ya no existe.');for(const p of c.path.slice(0,-1)){target[p]??={};target=target[p];if(!target||typeof target!=='object')throw Error('El campo cambió.');}const key=c.path.at(-1);if(!equal(slot(target,key),c.before))throw Error('El campo cambió.');if(c.after.exists)target[key]=clone(c.after.value);else delete target[key];}
 return value;
}
export const inverseDelta=changes=>[...changes].reverse().map(c=>({...c,before:c.after,after:c.before}));
