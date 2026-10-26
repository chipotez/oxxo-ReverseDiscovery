"""Organization-scoped, append-only field models. Diagrams pin authoritative versions."""
import copy,datetime,math,re,uuid
from flask import Blueprint,jsonify,request
from psycopg.types.json import Jsonb
from diagrams import authorize,connection,subject,require_member,failure,InvalidDiagram,text
from faults import Fault
from diagram_catalog import resource_model,COMPONENTS
bp=Blueprint('component_models',__name__,url_prefix='/bienvenida/api/catalog')
bp.before_request(authorize);bp.register_error_handler(Exception,failure)
KEYS={r['kind'] for r in COMPONENTS['resources']} - {'servidor','virtual'} | {'servers'}
FORMATS={'text','identifier','number','date','select','reference','boolean'}
def model_key(kind):return 'servers' if kind in ['servidor','virtual','servers'] else kind
def base_model(kind):
    if model_key(kind)=='servers':
        from standards import SERVER_MODEL
        return dict(version=1,sections=copy.deepcopy(SERVER_MODEL['sections']))
    value=resource_model(kind)
    if not value:raise Fault('KOD-CAT-004',status=404)
    return copy.deepcopy(value)
def latest(conn,kind,ensure=False):
    key=model_key(kind)
    if key not in KEYS:raise Fault('KOD-CAT-004',status=404)
    row=conn.execute('SELECT m.id,m.revision,m.current_version AS version,v.schema FROM component_models m JOIN component_model_versions v ON v.model_id=m.id AND v.version=m.current_version WHERE m.resource_key=%s',(key,)).fetchone()
    if not row and ensure:
        scope=conn.execute('SELECT component_model_scope() AS scope').fetchone()['scope']
        if scope:
            conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(scope+'|'+key,))
            row=conn.execute('SELECT m.id,m.revision,m.current_version AS version,v.schema FROM component_models m JOIN component_model_versions v ON v.model_id=m.id AND v.version=m.current_version WHERE m.resource_key=%s',(key,)).fetchone()
            if not row:
                schema=base_model(key)
                mid=conn.execute('INSERT INTO component_models(scope_key,resource_key,created_by) VALUES(%s,%s,%s) RETURNING id',(scope,key,subject())).fetchone()['id']
                conn.execute('INSERT INTO component_model_versions(model_id,version,schema,created_by) VALUES(%s,1,%s,%s)',(mid,Jsonb(schema),subject()))
                return dict(id=str(mid),revision=1,version=1,schema=schema,resource_key=key)
    return dict(id=str(row['id']),revision=row['revision'],version=row['version'],schema=row['schema'],resource_key=key) if row else dict(id=None,revision=1,version=1,schema=base_model(key),resource_key=key)
@bp.get('/models')
def listing():
    with connection(subject()) as conn:
        require_member(conn)
        keys=conn.execute('SELECT resource_key FROM component_models').fetchall()
        return jsonify(items=[latest(conn,k['resource_key']) for k in keys])
@bp.get('/models/<kind>')
def get(kind):
    with connection(subject()) as conn:
        require_member(conn);return jsonify(latest(conn,kind,ensure=True))
@bp.get('/errors')
def errors():
    from faults import CATALOG
    return jsonify(version=1,items=CATALOG)
def field_value(raw,controls=False):
    if not isinstance(raw,dict):raise Fault('KOD-CAT-001')
    try:label=text(raw.get('label'),100,True);description=text(raw.get('description'),300,True)
    except InvalidDiagram:raise Fault('KOD-CAT-001')
    fmt=raw.get('format','text')
    if fmt not in FORMATS or type(raw.get('required',False)) is not bool:raise Fault('KOD-CAT-001')
    options=raw.get('options',[])
    if fmt=='select':
        if not isinstance(options,list) or not 2<=len(options)<=30 or not all(isinstance(x,str) and 0<len(x.strip())<=80 for x in options):raise Fault('KOD-CAT-001','Una selección necesita entre 2 y 30 opciones distintas.')
        options=[x.strip() for x in options]
        if len({x.casefold() for x in options})!=len(options):raise Fault('KOD-CAT-001','Las opciones no deben repetirse.')
    elif options:raise Fault('KOD-CAT-001')
    return dict(id='custom_'+uuid.uuid4().hex,label=label,description=description,format='control' if controls else fmt,required=raw.get('required',False),options=options,custom=True)
@bp.post('/models/<kind>/fields')
def add(kind):
    body=request.get_json() or {};section_id=body.get('section')
    if type(body.get('revision')) is not int or section_id not in ['identification','controls','evidence','relationships']:raise Fault('KOD-CAT-001')
    field=field_value(body.get('field'),section_id=='controls')
    if section_id=='relationships' and field['format']!='reference':raise Fault('KOD-CAT-001','Las relaciones utilizan el formato Referencia.')
    key=model_key(kind)
    if key not in KEYS:raise Fault('KOD-CAT-004',status=404)
    with connection(subject()) as conn:
        require_member(conn)
        scope=conn.execute('SELECT component_model_scope() AS scope').fetchone()['scope']
        # Serialize first creation as well as concurrent additions; no client scope accepted.
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(scope+'|'+key,))
        current=latest(conn,key,ensure=True)
        if current['revision']!=body['revision']:raise Fault('KOD-CAT-003',status=409)
        schema=copy.deepcopy(current['schema']);section=next(s for s in schema['sections'] if s['id']==section_id)
        if len(section['fields'])>=64:raise Fault('KOD-CAT-001','El bloque admite hasta 64 campos.')
        if any(f['label'].strip().casefold()==field['label'].casefold() for f in section['fields']):raise Fault('KOD-CAT-002',status=409)
        if not current['id']:
            mid=conn.execute('INSERT INTO component_models(scope_key,resource_key,created_by) VALUES(%s,%s,%s) RETURNING id',(scope,key,subject())).fetchone()['id']
            conn.execute('INSERT INTO component_model_versions(model_id,version,schema,created_by) VALUES(%s,1,%s,%s)',(mid,Jsonb(schema),subject()))
        else:mid=uuid.UUID(current['id'])
        section['fields'].append(field);version=current['version']+1;schema['version']=version
        conn.execute('INSERT INTO component_model_versions(model_id,version,schema,created_by) VALUES(%s,%s,%s,%s)',(mid,version,Jsonb(schema),subject()))
        conn.execute('UPDATE component_models SET current_version=%s,revision=revision+1,updated_at=now() WHERE id=%s',(version,mid))
        return jsonify(latest(conn,key)),201

def resolve(conn,doc,original=None):
    previous={n['id']:n['data'] for n in (original or {}).get('nodes',[])};models={}
    known={(d['model_ref']['id'],d['model_ref']['version'],d['kind']):d['resource_schema'] for d in previous.values() if d.get('model_ref') and d.get('resource_schema')}
    for node in doc['nodes']:
        data=node['data'];kind=data['kind']
        if model_key(kind) not in KEYS:continue
        old=previous.get(node['id'],{});ref=data.get('model_ref') or (old.get('model_ref') if old.get('kind')==kind else None)
        if ref:
            if old.get('kind')==kind and old.get('model_ref') and ref['id']!=old['model_ref']['id']:raise Fault('KOD-CAT-004',status=403)
            if old.get('kind')==kind and ref==old.get('model_ref') and old.get('resource_schema'):
                schema=old['resource_schema']
            elif (ref['id'],ref['version'],kind) in known:schema=known[(ref['id'],ref['version'],kind)]
            else:
                row=conn.execute('SELECT v.schema FROM component_model_versions v JOIN component_models m ON m.id=v.model_id WHERE m.id=%s AND m.resource_key=%s AND v.version=%s',(ref['id'],model_key(kind),ref['version'])).fetchone()
                if not row:raise Fault('KOD-CAT-004',status=403)
                schema=row['schema']
            data['model_ref']=ref
        elif node['id'] not in previous:
            current=latest(conn,kind,ensure=True);schema=current['schema']
            if current['id']:data['model_ref']=dict(id=current['id'],version=current['version'])
        else:
            schema=copy.deepcopy(old.get('resource_schema')) if old.get('kind')==kind and old.get('resource_schema') else base_model(kind)
            if model_key(kind)=='servers':
                for section in schema['sections']:
                    if section['id']=='controls' and not section['fields']:section['fields']=base_model(kind)['sections'][1]['fields']
        models[node['id']]=schema
    return models

def validate_scalar(value,field):
    if value=='':return value # Drafts may be incomplete; coverage expresses missing requirements.
    fmt=field.get('format','text')
    if fmt=='number':
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or abs(value)>1e15:raise InvalidDiagram('El campo numérico requiere un número válido.')
        return value
    if fmt=='boolean':
        if type(value) is not bool:raise InvalidDiagram('El campo Sí / No requiere una selección válida.')
        return value
    value=text(value,500)
    if fmt=='date':
        try:datetime.date.fromisoformat(value)
        except ValueError:raise InvalidDiagram('La fecha debe tener el formato AAAA-MM-DD.')
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):raise InvalidDiagram('La fecha debe tener el formato AAAA-MM-DD.')
    if fmt=='select' and value not in field.get('options',[]):raise InvalidDiagram('El valor no pertenece a las opciones del campo.')
    return value

@bp.post('/models/<kind>/display-fields')
def display_fields(kind):
    """Explicitly publish missing identity fields before moving legacy display data."""
    body=request.get_json() or {};key=model_key(kind)
    if key not in KEYS:raise Fault('KOD-CAT-004',status=404)
    with connection(subject()) as conn:
        require_member(conn)
        scope=conn.execute('SELECT component_model_scope() AS scope').fetchone()['scope']
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(scope+'|'+key,))
        current=latest(conn,key,ensure=True)
        if current['revision']!=body.get('revision'):raise Fault('KOD-CAT-003',status=409)
        schema=copy.deepcopy(current['schema']);fields=schema['sections'][0]['fields'];changed=False
        for fid,label,description in [('address','Dirección IP / DNS','Dirección o nombre de red del componente.'),('port','Puerto / protocolo','Puerto y protocolo publicados.'),('technology','Tecnología y versión','Producto y versión utilizados.'),('provider','Proveedor','Fabricante o proveedor de la plataforma.'),('location','Ubicación','Sede, datacenter o región.')]:
            if not any(f['id']==fid for f in fields):
                if len(fields)>=64:raise Fault('KOD-CAT-001','El bloque admite hasta 64 campos.')
                fields.append(dict(id=fid,label=label,description=description,format='text',required=False));changed=True
        if changed:
            version=current['version']+1;schema['version']=version
            conn.execute('INSERT INTO component_model_versions(model_id,version,schema,created_by) VALUES(%s,%s,%s,%s)',(current['id'],version,Jsonb(schema),subject()))
            conn.execute('UPDATE component_models SET current_version=%s,revision=revision+1,updated_at=now() WHERE id=%s',(version,current['id']))
        return jsonify(latest(conn,key))
