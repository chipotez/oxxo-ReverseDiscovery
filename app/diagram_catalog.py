"""Shared, versioned resource palette and server-owned starter diagrams."""
import json,uuid
from pathlib import Path
path=Path(__file__).with_name('diagram-catalog.json')
if not path.exists():path=Path(__file__).parent/'frontend/src/diagram-catalog.json'
CATALOG=json.loads(path.read_text())
component_path=path.with_name('component-catalog.json')
COMPONENTS=json.loads(component_path.read_text())
CATALOG['categories']=[dict(id=c['id'],label=c['label'],icon=c['icon']) for c in COMPONENTS['categories']]+[dict(id='visual',label='Organización visual',icon='collection')]
CATALOG['resources']=COMPONENTS['resources']+CATALOG['visualResources']
LABELS={item['kind']:item['label'] for item in CATALOG['resources']}
TEMPLATES={item['id']:item for item in CATALOG['templates']}
def starter(template_id,name):
    if not isinstance(template_id,str) or template_id not in TEMPLATES:raise ValueError('Unknown diagram template')
    template=TEMPLATES[template_id]
    nodes=json.loads(json.dumps(template['nodes']));edges=json.loads(json.dumps(template['edges']))
    ids={n['id']:str(uuid.uuid4()) for n in nodes}
    for node in nodes:
        node['id']=ids[node['id']]
        if node.get('parentId'):node['parentId']=ids[node['parentId']]
    for edge in edges:edge.update(id=str(uuid.uuid4()),source=ids[edge['source']],target=ids[edge['target']])
    return dict(name=name,nodes=nodes,edges=edges)
