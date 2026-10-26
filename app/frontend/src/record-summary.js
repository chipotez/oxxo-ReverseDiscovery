// A concise view of provider-reported values. The original record stays untouched.
export function summarizeRecord(record){
 if(record===null||typeof record!=='object')return [['Valor',String(record)]];
 const meta=record.meta||{},attrs=record.attributes||{},tags=Object.values(record.tags_by_source||{}).flat().filter(t=>typeof t==='string');
 const tag=key=>tags.find(t=>t.startsWith(key+':'))?.slice(key.length+1);
 const cluster=tag('kube_cluster_name')??tag('kubernetes_cluster')??tag('cluster_name'),node=tag('kube_node')??tag('kubernetes_node'),apps=Array.isArray(record.apps)?record.apps:[];
 const rows=[['Proveedor',record.aws_id?'AWS · EC2':tag('cloud_provider')],['Instancia cloud',record.aws_id],['Clúster',cluster],['Nodo Kubernetes',node],['Software detectado',apps.some(a=>a==='kubernetes'||a==='kubernetes_state')?'Kubernetes (según apps)':undefined],['Runtime',apps.includes('containerd')?'containerd':apps.includes('docker')?'Docker':undefined],['Nombre',record.name??record.host_name??attrs.name??record.title],['ID',record.id],['Sistema operativo',meta.platform],['Procesadores',meta.cpuCores],['Agente',meta.agent_version],['Ambiente',tag('env')],['Servicio',tag('service')??attrs.service],['Equipo',tag('team')],['Región',tag('region')??tag('aws_region')],['Aplicaciones',Array.isArray(record.apps)?record.apps.join(', '):undefined],['Reportando',typeof record.up==='boolean'?(record.up?'Sí':'No'):undefined],['Estado',attrs.status??record.overall_state??record.status],['Tipo',record.type]];
 const clean=rows.filter(([,v])=>v!==undefined&&v!==null&&v!=='').map(([k,v])=>[k,String(v)]);
 if(!clean.length)for(const [k,v] of Object.entries(record)){if(v!==null&&typeof v!=='object'&&String(v).length<=240)clean.push([k,String(v)]);if(clean.length>=10)break;}
 return clean;
}
