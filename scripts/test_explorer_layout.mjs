import assert from 'node:assert/strict';
import {rowsThatFit} from '../app/frontend/src/explorer-layout.js';
assert.equal(rowsThatFit(380,76),5);
assert.equal(rowsThatFit(454,40,6),10);
assert.equal(rowsThatFit(453,40,6),9);
assert.equal(rowsThatFit(10,76),1);
assert.equal(rowsThatFit(3000,40,6,25),25);
console.log('PASS measured list capacity: exact fit, gaps, boundary, minimum and API cap');
