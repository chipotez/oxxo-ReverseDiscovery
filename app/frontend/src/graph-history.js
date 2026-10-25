// Diagram history excludes selection/UI state and keeps each compound edit atomic.
export function createHistory(initial){
 let current=JSON.stringify(initial),past=[],future=[],lastGroup=null,lastTime=0;
 return {record(value,{group=null,now=Date.now()}={}){const next=JSON.stringify(value);if(next===current)return;if(!group||group!==lastGroup||now-lastTime>600){past.push(current);if(past.length>50)past.shift();}current=next;future=[];lastGroup=group;lastTime=now;},undo(){if(!past.length)return null;future.push(current);current=past.pop();lastGroup=null;return JSON.parse(current);},redo(){if(!future.length)return null;past.push(current);current=future.pop();lastGroup=null;return JSON.parse(current);},counts:()=>({undo:past.length,redo:future.length})};
}
