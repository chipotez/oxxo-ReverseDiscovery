import assert from 'node:assert/strict';
import {summarizeRecord} from '../app/frontend/src/record-summary.js';
const record={id:0,name:'qa-host',up:false,meta:{platform:'Linux',cpuCores:0,gohai:'large opaque payload'},tags_by_source:{agent:['env:production','service:db']},apps:['postgres']};
const before=JSON.stringify(record),rows=Object.fromEntries(summarizeRecord(record));
assert.equal(rows.ID,'0');assert.equal(rows.Procesadores,'0');assert.equal(rows.Reportando,'No');assert.equal(rows.Ambiente,'production');assert.equal(rows.Servicio,'db');assert.equal(rows.Aplicaciones,'postgres');assert(!JSON.stringify(rows).includes('opaque'));assert.equal(JSON.stringify(record),before);
assert.deepEqual(summarizeRecord(false),[['Valor','false']]);assert.deepEqual(summarizeRecord(null),[['Valor','null']]);assert.deepEqual(summarizeRecord({nested:{data:1}}),[]);assert.deepEqual(summarizeRecord({custom:'value'}),[['custom','value']]);console.log('PASS summary: zero/false, tags, generic records, opaque metadata excluded, immutable source');

const k=Object.fromEntries(summarizeRecord({aws_id:'i-qa',apps:['kubernetes','containerd'],tags_by_source:{agent:['kube_cluster_name:qa-cluster','kube_node:qa-node']}}));assert.equal(k.Clúster,'qa-cluster');assert.equal(k['Nodo Kubernetes'],'qa-node');assert.equal(k.Runtime,'containerd');assert.equal(k.Proveedor,'AWS · EC2');assert(!('Tipo' in k));
