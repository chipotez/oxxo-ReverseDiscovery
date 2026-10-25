import {documentation,documented} from '../app/frontend/src/resource-documentation.js';
import model from '../app/frontend/src/server-standard-model.json';
const check=(ok,msg)=>{if(!ok)throw Error(msg)};const data={kind:'virtual',server_instance:{identification:{}}};const fields=model.sections[0].fields;check(documentation(data,'identification','vm').state==='missing','empty');data.server_instance.identification[fields[0].id]='QA';check(documentation(data,'identification','vm').state==='missing','under half');fields.slice(0,4).forEach(f=>data.server_instance.identification[f.id]='QA');check(documentation(data,'identification','vm').state==='progress','half');fields.forEach(f=>data.server_instance.identification[f.id]='QA');check(documentation(data,'identification','vm').state==='complete','complete');check(!documented('No aplica')&&documented('No aplica: VM sin número físico'),'NA justification');check(documentation(data,'relationships','vm',[{source:'vm',target:'db',relation:'hosts'}]).filled===1,'typed relation counts');data.standard={definition:{requirements:[{id:'backup',level:'required'}]},coverage:[{id:'backup',status:'pending',evidence:'QA backup absent'}]};check(documentation(data,'controls','vm').state==='complete','documented pending is not a healthy signal');console.log('PASS documentation thresholds, no-apply justification, relationship and pending-control semantics');

data.standard={definition:{server_model:{identification:[{id:'context',level:'required'}]}}};check(documentation(data,'identification','vm').total===2,'legacy required context applies to both split fields');console.log('PASS required legacy policy mapping');

import {resourceLayout} from '../app/frontend/src/resource-layout.js';
const nodes=['a','b','c'].map((id,i)=>({id,type:'resource',position:{x:i*500,y:0},data:{kind:'virtual',label:id}}));
const result=resourceLayout(nodes,[{source:'a',target:'b',relation:'hosts'},{source:'b',target:'c',relation:'hosts'}]);
check(result.nodes.map(n=>n.id).join('')==='abc','parent-first');
check(result.nodes[1].parentId==='a'&&result.nodes[2].parentId==='b','recursive containment');
check(result.sizes.get('a').width>result.sizes.get('b').width&&result.sizes.get('a').height>result.sizes.get('b').height,'recursive bounds');
check(result.absolute.get('c').x===20&&result.absolute.get('c').y===168,'absolute coordinates');
console.log('PASS recursive matryoshka layout and absolute positions');
const shortNode={id:'short',type:'resource',position:{x:0,y:0},data:{kind:'virtual',label:'QA'}};
const detailed={...shortNode,data:{...shortNode.data,server_instance:{identification:{hostname:'qa.example',environment:'QA',criticality:'Alta'}}}};
check(resourceLayout([shortNode],[]).sizes.get('short').height===76,'one-line compact footprint');
check(resourceLayout([detailed],[]).sizes.get('short').height===90,'summary grows only with visible distinct values');
console.log('PASS content-aware compact node height');

import {overall} from '../app/frontend/src/documentation-views.jsx';
check(overall({kind:'custom_service'},'custom',[]).label==='Pendiente','empty overall');
check(documentation({kind:'custom_service'},'identification','custom').total===4,'custom own identity schema');
check(documentation({kind:'virtual'},'identification','vm').total===8,'server own identity schema');
console.log('PASS summary uses each resource standard');
const defaultName={...shortNode,data:{kind:'virtual',label:'Máquina virtual'}};
check(resourceLayout([defaultName],[]).sizes.get('short').height===62,'no duplicate type caption or empty metadata reservation');
check(resourceLayout([defaultName],[]).sizes.get('short').width===320,'narrower node width');
console.log('PASS duplicate caption removal and narrow geometry');
const typed={kind:'custom_service',resource_schema:{version:2,sections:[{id:'identification',fields:[{id:'zero',custom:true,required:true},{id:'no',custom:true,required:true},{id:'optional',custom:true,required:false}]}]},component_instance:{identification:{zero:0,no:false}}};
check(documentation(typed,'identification','typed').filled===2&&documentation(typed,'identification','typed').total===2,'typed zero/false count and optional fields excluded');
console.log('PASS versioned schema coverage for zero, false and optional fields');
