import assert from 'node:assert/strict';
import {graphDelta,applyDelta,equal} from '../app/frontend/src/graph-delta.js';
import {createHistory} from '../app/frontend/src/graph-history.js';
const base={name:'QA',nodes:[{id:'a',data:{label:'A',address:''}}],edges:[]};
const mine=structuredClone(base);mine.nodes[0].data.label='Mine';
const theirs=structuredClone(base);theirs.nodes[0].data.address='192.0.2.1';
const merged=applyDelta(theirs,graphDelta(base,mine));assert.equal(merged.nodes[0].data.label,'Mine');assert.equal(merged.nodes[0].data.address,'192.0.2.1');
const h=createHistory(base);h.record(mine);h.sync(merged);const undo=h.undo();assert.equal(undo.nodes[0].data.label,'A');assert.equal(undo.nodes[0].data.address,'192.0.2.1');assert.equal(h.redo().nodes[0].data.label,'Mine');
const other=structuredClone(merged);other.nodes[0].data.label='Another editor';h.sync(other);assert.throws(()=>h.undo());assert.equal(h.counts().undo,1);
console.log('PASS independent fields, local undo/redo preserving remote work, conflicting undo refused');

assert(equal({a:1,b:[{c:2,d:3}]},{b:[{d:3,c:2}],a:1}));
