/** Record nested workspace views without remounting their live editor. */
export function recordView(path,values,replace=false){const params=new URLSearchParams();for(const [key,value] of Object.entries(values))if(value!==undefined&&value!==null&&value!=='')params.set(key,value);const hash='#'+path+(params.size?'?'+params:'');if(location.hash===hash)return;history[replace?'replaceState':'pushState']({koodariaView:true},'',hash);window.dispatchEvent(new Event('koodaria:route-state'));}
export function viewParams(){return new URLSearchParams(location.hash.split('?')[1]||'');}
