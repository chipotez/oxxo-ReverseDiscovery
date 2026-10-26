import {graphDelta,applyDelta,inverseDelta} from './graph-delta.js';
// Remote edits update the baseline, never enter this user's undo stack.
export function createHistory(initial){
 let current=structuredClone(initial),past=[],future=[],lastGroup=null,lastTime=0;
 return {record(value,{group=null,now=Date.now()}={}){const delta=graphDelta(current,value);if(!delta.length)return;if(group&&group===lastGroup&&now-lastTime<=600&&past.length){const first=applyDelta(current,inverseDelta(past.at(-1)));past[past.length-1]=graphDelta(first,value);}else{past.push(delta);if(past.length>50)past.shift();}current=structuredClone(value);future=[];lastGroup=group;lastTime=now;},sync(value){current=structuredClone(value);lastGroup=null;},undo(){if(!past.length)return null;const delta=past.at(-1),next=applyDelta(current,inverseDelta(delta));past.pop();future.push(delta);current=next;lastGroup=null;return next;},redo(){if(!future.length)return null;const delta=future.at(-1),next=applyDelta(current,delta);future.pop();past.push(delta);current=next;lastGroup=null;return next;},counts:()=>({undo:past.length,redo:future.length})};
}
