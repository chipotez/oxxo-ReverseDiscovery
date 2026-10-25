export const shortId=value=>String(value||'').split('-').at(-1);
export function descendants(root,nodes,edges){if(!root)return nodes;const ids=new Set([root]),pending=[root];while(pending.length){const parent=pending.pop();for(const e of edges)if(e.relation==='hosts'&&e.source===parent&&!ids.has(e.target)){ids.add(e.target);pending.push(e.target);}}return nodes.filter(n=>ids.has(n.id));}
