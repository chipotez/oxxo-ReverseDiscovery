"""Private resource standards, immutable publications and document-bound snapshots."""
import json,uuid
from datetime import datetime,timezone
from pathlib import Path
from flask import Blueprint,jsonify,request
from psycopg.types.json import Jsonb
from diagrams import authorize,failure,connection,subject,require_member,key,text,InvalidDiagram

path=Path(__file__).with_name('operating-standards.json')
if not path.exists():path=Path(__file__).parent/'frontend/src/operating-standards.json'
model_path=path.with_name('server-standard-model.json')
if not model_path.exists():model_path=Path(__file__).parent/'frontend/src/server-standard-model.json'
SERVER_MODEL=json.loads(model_path.read_text())
CATALOG=json.loads(path.read_text());FUNCTIONS={f['id']:f for f in CATALOG['functions']}
bp=Blueprint('standards',__name__,url_prefix='/bienvenida/api/standards')
bp.before_request(authorize);bp.register_error_handler(Exception,failure)
from psycopg.errors import UniqueViolation
@bp.errorhandler(UniqueViolation)
def duplicate_name(exc):return jsonify(error='Ya existe una definición con ese nombre.'),409
@bp.errorhandler(InvalidDiagram)
def invalid_definition(exc):return jsonify(error='La definición no es válida. Revisa sus campos.'),400

def definition(value):
    if not isinstance(value,dict):raise InvalidDiagram()
    result={'name':text(value.get('name'),100,True),'responsible':text(value.get('responsible',''),120)}
    for field,options in [('family','families'),('platform','platforms'),('environment','environments'),('criticality','criticalities')]:
        if value.get(field) not in CATALOG[options]:raise InvalidDiagram()
        result[field]=value[field]
    controls=value.get('requirements')
    if not isinstance(controls,list) or len(controls)!=len(FUNCTIONS):raise InvalidDiagram()
    seen=set();result['requirements']=[]
    for control in controls:
        if not isinstance(control,dict) or control.get('id') not in FUNCTIONS or control['id'] in seen or control.get('level') not in CATALOG['levels']:raise InvalidDiagram()
        seen.add(control['id']);out={'id':control['id'],'label':FUNCTIONS[control['id']]['label'],'level':control['level']}
        for field,limit in [('condition',500),('tool',120),('responsible',120),('configuration',500),('evidence',500),('frequency',100)]:out[field]=text(control.get(field,''),limit)
        result['requirements'].append(out)
    if 'server_model' in value:
        model=value['server_model']
        if not isinstance(model,dict) or set(model)!={'identification','evidence','relationships'}:raise InvalidDiagram()
        result['server_model']={}
        for section in SERVER_MODEL['sections']:
            if section['id']=='controls':continue
            entries=model[section['id']];allowed={f['id'] for f in section['fields']}
            if not isinstance(entries,list) or len(entries)!=len(allowed):raise InvalidDiagram()
            seen=set();clean=[]
            for entry in entries:
                if not isinstance(entry,dict) or entry.get('id') not in allowed or entry['id'] in seen or entry.get('level') not in CATALOG['levels']:raise InvalidDiagram()
                seen.add(entry['id']);clean.append(dict(id=entry['id'],level=entry['level'],rule=text(entry.get('rule',''),500)))
            result['server_model'][section['id']]=clean
    return result

def initial(family,name):
    required={'monitoring','endpoint','backup','logs','cmdb','patching'}
    return definition(dict(name=name,family=family,platform='any',environment='all',criticality='unspecified',responsible='',requirements=[dict(id=i,level='required' if i in required else 'recommended') for i in FUNCTIONS]))

def serial(row):
    out=dict(row)
    for field in ['id','standard_id']:
        if field in out:out[field]=str(out[field])
    for field in ['updated_at','published_at']:
        if field in out:out[field]=out[field].isoformat()
    return out

@bp.get('')
def listing():
    with connection(subject()) as conn:
        require_member(conn)
        rows=conn.execute('SELECT id,name,revision,draft,published_version,updated_at FROM resource_standards WHERE owner_sub=%s ORDER BY lower(name) LIMIT 200',(subject(),)).fetchall()
    return jsonify(items=[serial(r) for r in rows])

@bp.get('/published')
def published():
    with connection(subject()) as conn:
        require_member(conn)
        rows=conn.execute('SELECT s.id,s.published_version AS version,v.definition FROM resource_standards s JOIN resource_standard_versions v ON v.standard_id=s.id AND v.version=s.published_version WHERE s.owner_sub=%s ORDER BY lower(s.name)',(subject(),)).fetchall()
    return jsonify(items=[serial(r) for r in rows])

@bp.post('')
def create():
    body=request.get_json() or {};value=initial(body.get('family','linux'),body.get('name','Servidor Linux'))
    with connection(subject()) as conn:
        require_member(conn);conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(subject(),))
        if conn.execute('SELECT count(*) AS count FROM resource_standards WHERE owner_sub=%s',(subject(),)).fetchone()['count']>=200:return jsonify(error='Puedes crear hasta 200 definiciones.'),400
        row=conn.execute('INSERT INTO resource_standards(owner_sub,name,draft) VALUES(%s,%s,%s) RETURNING id,name,draft,revision,published_version,updated_at',(subject(),value['name'],Jsonb(value))).fetchone()
    return jsonify(serial(row)),201

@bp.put('/<standard_id>')
def save(standard_id):
    body=request.get_json() or {};value=definition(body.get('definition'))
    if type(body.get('revision'))!=int:raise InvalidDiagram()
    with connection(subject()) as conn:
        require_member(conn)
        previous=conn.execute('SELECT draft FROM resource_standards WHERE id=%s AND owner_sub=%s',(key(standard_id),subject())).fetchone()
        if previous:
            if 'server_model' not in value and 'server_model' in previous['draft']:value['server_model']=previous['draft']['server_model']
            old={c['id']:c for c in previous['draft']['requirements']}
            submitted={c['id']:c for c in body['definition']['requirements']}
            for control in value['requirements']:
                if 'condition' not in submitted[control['id']]:control['condition']=old[control['id']].get('condition','')
        row=conn.execute('UPDATE resource_standards SET name=%s,draft=%s,revision=revision+1,updated_at=now() WHERE id=%s AND owner_sub=%s AND revision=%s RETURNING id,name,draft,revision,published_version,updated_at',(value['name'],Jsonb(value),key(standard_id),subject(),body['revision'])).fetchone()
        if not row:return jsonify(error='La definición cambió o ya no está disponible. Vuelve a abrirla antes de guardar.'),409
    return jsonify(serial(row))

@bp.post('/<standard_id>/publish')
def publish(standard_id):
    body=request.get_json() or {}
    if type(body.get('revision'))!=int:raise InvalidDiagram()
    with connection(subject()) as conn:
        require_member(conn)
        row=conn.execute('SELECT * FROM resource_standards WHERE id=%s AND owner_sub=%s FOR UPDATE',(key(standard_id),subject())).fetchone()
        if not row:return jsonify(error='Definición no encontrada.'),404
        if row['revision']!=body['revision']:return jsonify(error='La definición cambió. Vuelve a abrirla antes de publicar.'),409
        if row['published_version']>=100:return jsonify(error='Esta definición admite hasta 100 versiones.'),400
        value=definition(row['draft']);version=row['published_version']+1
        conn.execute('INSERT INTO resource_standard_versions(standard_id,version,owner_sub,definition) VALUES(%s,%s,%s,%s)',(row['id'],version,subject(),Jsonb(value)))
        row=conn.execute('UPDATE resource_standards SET published_version=%s,revision=revision+1,updated_at=now() WHERE id=%s RETURNING id,name,draft,revision,published_version,updated_at',(version,row['id'])).fetchone()
    return jsonify(serial(row)),201

@bp.get('/<standard_id>/versions')
def versions(standard_id):
    with connection(subject()) as conn:
        require_member(conn)
        rows=conn.execute('SELECT standard_id,version,definition,published_at FROM resource_standard_versions WHERE standard_id=%s ORDER BY version DESC LIMIT 100',(key(standard_id),)).fetchall()
    return jsonify(items=[serial(r) for r in rows])

def reference(value):
    if not isinstance(value,dict):raise InvalidDiagram()
    sid=str(key(value.get('id')));version=value.get('version')
    if type(version)!=int or not 1<=version<=100:raise InvalidDiagram()
    coverage=value.get('coverage',[])
    if not isinstance(coverage,list) or len(coverage)>len(FUNCTIONS):raise InvalidDiagram()
    clean=[];seen=set()
    for item in coverage:
        if not isinstance(item,dict) or item.get('id') not in FUNCTIONS or item['id'] in seen or item.get('status') not in CATALOG['states']:raise InvalidDiagram()
        seen.add(item['id']);clean.append(dict(id=item['id'],status=item['status'],evidence=text(item.get('evidence',''),500)))
    return dict(id=sid,version=version,coverage=clean)

def bind(conn,doc,original=None):
    """Only owner-visible publications or snapshots already in this authorized map."""
    previous={n['id']:n for n in (original or {}).get('nodes',[])}
    snapshots={(n['data']['standard']['id'],n['data']['standard']['version']):n['data']['standard'] for n in previous.values() if n['data'].get('standard')}
    for node in doc['nodes']:
        data=node['data'];value=data.get('standard')
        if not value and data['kind'] in ['servidor','virtual']:
            existing=previous.get(node['id'],{}).get('data',{}).get('standard')
            if existing:
                data['standard']=json.loads(json.dumps(existing));continue
        if not value:continue
        if data['kind'] not in ['servidor','virtual']:raise InvalidDiagram()
        pair=(value['id'],value['version']);known=snapshots.get(pair)
        if known:definition_value=known['definition']
        else:
            row=conn.execute('SELECT definition FROM resource_standard_versions WHERE standard_id=%s AND version=%s',(key(value['id']),value['version'])).fetchone()
            if not row:raise InvalidDiagram()
            definition_value=row['definition']
        if definition_value['platform']=='physical' and data['kind']=='virtual':raise InvalidDiagram()
        by_id={c['id']:c for c in value['coverage']};prior=previous.get(node['id'],{}).get('data',{}).get('standard',{})
        old={c['id']:c for c in prior.get('coverage',[])} if (prior.get('id'),prior.get('version'))==pair else {}
        coverage=[]
        for req in definition_value['requirements']:
            c=by_id.get(req['id'],dict(id=req['id'],status='unknown',evidence=''))
            unchanged=old.get(c['id'],{}).get('status')==c['status'] and old.get(c['id'],{}).get('evidence','')==c['evidence']
            c.update(source='declared',reviewed_at=old[c['id']].get('reviewed_at') if unchanged else datetime.now(timezone.utc).isoformat() if c['status']!='unknown' or c['evidence'] else None)
            coverage.append(c)
        data['standard']=dict(id=value['id'],version=value['version'],name=definition_value['name'],definition=definition_value,coverage=coverage)
    return doc
