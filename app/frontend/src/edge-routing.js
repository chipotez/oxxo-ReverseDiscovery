// Canonical orthogonal routes: no duplicate or collinear vertices.
export function simplify(points,tolerance=1){
 const out=[];for(const point of points){const p={x:Math.round(point.x*10)/10,y:Math.round(point.y*10)/10};if(out.length&&Math.hypot(p.x-out.at(-1).x,p.y-out.at(-1).y)<=tolerance)continue;out.push(p);while(out.length>2){const [a,b,c]=out.slice(-3);if(((Math.abs(a.x-b.x)<=tolerance&&Math.abs(b.x-c.x)<=tolerance)||(Math.abs(a.y-b.y)<=tolerance&&Math.abs(b.y-c.y)<=tolerance))&&(b.x-a.x)*(c.x-b.x)+(b.y-a.y)*(c.y-b.y)>=0)out.splice(out.length-2,1);else break;}}return out;
}
const vector=p=>({left:{x:-1,y:0},right:{x:1,y:0},top:{x:0,y:-1},bottom:{x:0,y:1}}[p]||{x:1,y:0});
export function routeOrthogonal(source,target,sourcePosition,targetPosition,obstacles=[]){
 const sv=vector(sourcePosition),tv=vector(targetPosition),a={x:source.x+sv.x*20,y:source.y+sv.y*20},b={x:target.x+tv.x*20,y:target.y+tv.y*20};
 const rects=obstacles.filter(r=>![source,target].some(p=>p.x>=r.x-1&&p.x<=r.x+r.width+1&&p.y>=r.y-1&&p.y<=r.y+r.height+1)).sort((r,q)=>Math.hypot(r.x-(a.x+b.x)/2,r.y-(a.y+b.y)/2)-Math.hypot(q.x-(a.x+b.x)/2,q.y-(a.y+b.y)/2)).slice(0,32);
 const xs=[(a.x+b.x)/2,...rects.flatMap(r=>[r.x-16,r.x+r.width+16])],ys=[(a.y+b.y)/2,...rects.flatMap(r=>[r.y-16,r.y+r.height+16])];
 const candidates=[[a,{x:b.x,y:a.y},b],[a,{x:a.x,y:b.y},b],...xs.map(x=>[a,{x,y:a.y},{x,y:b.y},b]),...ys.map(y=>[a,{x:a.x,y},{x:b.x,y},b])];
 const score=points=>{const first=points[1],last=points.at(-2);let n=((first.x-source.x)*sv.x+(first.y-source.y)*sv.y<1?1000000:0)+((last.x-target.x)*tv.x+(last.y-target.y)*tv.y<1?1000000:0);for(let i=1;i<points.length;i++){const p=points[i-1],q=points[i];n+=Math.abs(p.x-q.x)+Math.abs(p.y-q.y);for(const r of rects){if(p.x===q.x?p.x>r.x-8&&p.x<r.x+r.width+8&&Math.max(p.y,q.y)>r.y-8&&Math.min(p.y,q.y)<r.y+r.height+8:p.y>r.y-8&&p.y<r.y+r.height+8&&Math.max(p.x,q.x)>r.x-8&&Math.min(p.x,q.x)<r.x+r.width+8)n+=100000;}}return n+points.length*12;};
 return candidates.map(p=>simplify([source,...p,target])).sort((p,q)=>score(p)-score(q))[0];
}
export function moveSegment(points,index,point){
 const next=structuredClone(points),a=next[index],b=next[index+1],horizontal=Math.abs(a.y-b.y)<1;
 // Keep endpoints attached: insert short end legs instead of moving a port.
 if(index===0){next.splice(1,0,{...a});index++;}if(index+1===next.length-1)next.splice(next.length-1,0,{...b});
 if(horizontal){next[index].y=point.y;next[index+1].y=point.y;}else{next[index].x=point.x;next[index+1].x=point.x;}return next;
}
export function roundedPath(points,radius=8){if(!points.length)return '';let d=`M ${points[0].x},${points[0].y}`;for(let i=1;i<points.length-1;i++){const a=points[i-1],b=points[i],c=points[i+1],l=Math.hypot(b.x-a.x,b.y-a.y),r=Math.hypot(c.x-b.x,c.y-b.y),k=Math.min(radius,l/2,r/2);if(!l||!r)continue;d+=` L ${b.x+(a.x-b.x)*k/l},${b.y+(a.y-b.y)*k/l} Q ${b.x},${b.y} ${b.x+(c.x-b.x)*k/r},${b.y+(c.y-b.y)*k/r}`;}return d+` L ${points.at(-1).x},${points.at(-1).y}`;}
