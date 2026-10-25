import assert from 'node:assert/strict';
import {copyGraph,connectionAppearance} from '../app/frontend/src/connection-style.js';
const doc={name:'QA',nodes:[{id:'a',data:{kind:'virtual'}},{id:'b',parentId:'a',data:{kind:'datos'}}],edges:[{id:'ab',source:'a',target:'b',relation:'hosts',color:'blue',pattern:'dashdot'}]};
const copy=copyGraph(doc);
assert.notEqual(copy.nodes[0].id,'a');assert.equal(copy.nodes[1].parentId,copy.nodes[0].id);assert.equal(copy.edges[0].source,copy.nodes[0].id);assert.equal(copy.edges[0].target,copy.nodes[1].id);assert.equal(copy.edges[0].relation,'hosts');assert.equal(new Set([...copy.nodes,...copy.edges].map(x=>x.id)).size,3);assert.equal(doc.nodes[1].parentId,'a');
const line=connectionAppearance({...doc.edges[0],arrows:'both'});assert.equal(line.style.strokeDasharray,'8 4 1 4');assert.equal(line.markerStart.color,line.style.stroke);assert.equal(line.markerEnd.color,line.style.stroke);
console.log('PASS independent copy identities, remapped nesting/relations, rendered semantic styles');
