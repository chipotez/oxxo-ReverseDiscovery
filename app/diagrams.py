"""Authenticated diagram storage. Every query is scoped to the verified OIDC subject."""
import math
import os
import uuid
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from flask import Blueprint, jsonify, request, session, send_file, abort
from werkzeug.exceptions import HTTPException
import secrets
import time

from access import is_member, capabilities
from invitations import normalize_email, notify_existing, IdentityProvider, InvitationUnavailable, provision_ready, mail_ready

bp = Blueprint('diagrams', __name__, url_prefix='/bienvenida/api/diagrams')
from diagram_catalog import LABELS, starter
KINDS = set(LABELS)

class InvalidDiagram(ValueError):
    pass

def text(value, maximum, required=False):
    if not isinstance(value, str) or len(value) > maximum or (required and not value.strip()):
        raise InvalidDiagram()
    return value.strip()

def number(value, low, high):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not low <= value <= high:
        raise InvalidDiagram()
    return value

def validate(value,schemas=None,defer_instances=False):
    if not isinstance(value, dict): raise InvalidDiagram()
    name = text(value.get('name'), 100, True)
    nodes, edges = value.get('nodes'), value.get('edges')
    if not isinstance(nodes, list) or not isinstance(edges, list) or len(nodes)>200 or len(edges)>500:
        raise InvalidDiagram()
    clean, ids = [], {}
    for index,n in enumerate(nodes,1):
        try:
            if not isinstance(n, dict): raise InvalidDiagram()
            key = text(n.get('id'), 100, True)
            kind = n.get('type')
            data, pos = n.get('data'), n.get('position')
            if key in ids or kind not in ('resource', 'resourceGroup') or not isinstance(data, dict) or not isinstance(pos, dict): raise InvalidDiagram()
            if data.get('kind') not in KINDS or (kind=='resourceGroup') != (data['kind']=='grupo'): raise InvalidDiagram()
            out = dict(id=key, type=kind, position=dict(x=number(pos.get('x'),-100000,100000),y=number(pos.get('y'),-100000,100000)), data=dict(label=text(data.get('label'),100,True),kind=data['kind'],address=text(data.get('address',''),120),port=text(data.get('port',''),40)))
            for field in ['provider','technology','location']:
                if field in data:out['data'][field]=text(data[field],120)
            for field in ['collapsed','positionLocked']:
                if field in data:
                    if type(data[field]) is not bool:raise InvalidDiagram()
                    out['data'][field]=data[field]
            if 'server_instance' in data:
                from standards import instance
                if data['kind'] not in ['servidor','virtual']:raise InvalidDiagram()
                try:out['data']['server_instance']=data['server_instance'] if defer_instances else instance(data['server_instance'],(schemas or {}).get(key))
                except InvalidDiagram:raise InvalidDiagram('Los datos de un servidor no coinciden con los campos o formatos de su estándar. Revisa sus cuatro secciones.')
            if 'component_instance' in data:
                from standards import instance
                from diagram_catalog import resource_model
                schema=(schemas or {}).get(key) or resource_model(data['kind'])
                if not schema or data['kind'] in ['servidor','virtual']:raise InvalidDiagram()
                try:out['data']['component_instance']=data['component_instance'] if defer_instances else instance(data['component_instance'],schema)
                except InvalidDiagram:raise InvalidDiagram('Los datos de un componente no coinciden con su estándar. Revisa sus cuatro secciones.')
            if data.get('model_ref') is not None:
                ref=data['model_ref']
                if not isinstance(ref,dict) or type(ref.get('version')) is not int or not 1<=ref['version']<=1000:raise InvalidDiagram('La referencia del modelo no es válida.')
                out['data']['model_ref']=dict(id=str(uuid.UUID(ref['id'])),version=ref['version'])
            if data.get('standard') is not None:
                from standards import reference
                out['data']['standard']=reference(data['standard'])
            if kind=='resourceGroup':
                style=n.get('style',{})
                if not isinstance(style,dict): raise InvalidDiagram()
                out['style']=dict(width=number(style.get('width',380),260,100000),height=number(style.get('height',260),180,100000))
            if n.get('parentId'):
                out.update(parentId=text(n['parentId'],100,True),extent='parent')
            ids[key]=out
            clean.append(out)
        except InvalidDiagram as exc:
            raise InvalidDiagram(f'Recurso {index}: '+(str(exc) or 'revisa el tipo, los campos del estándar y los límites de sus valores.')) from None
    for n in clean:
        if n.get('parentId') and ids.get(n['parentId'],{}).get('type')!='resourceGroup': raise InvalidDiagram()
        trail={n['id']};parent=n.get('parentId')
        while parent:
            if parent in trail:raise InvalidDiagram('Los grupos no pueden contenerse a sí mismos ni formar ciclos.')
            trail.add(parent);parent=ids[parent].get('parentId')
    connections, seen = [], set()
    for e in edges:
        if not isinstance(e,dict): raise InvalidDiagram()
        try:key=text(e.get('id'),240,True)
        except InvalidDiagram:raise InvalidDiagram('Una conexión tiene un identificador inválido. Elimínala y vuelve a conectarla.')
        source, target=e.get('source'),e.get('target')
        if not isinstance(source,str) or not isinstance(target,str) or key in seen or source==target or ids.get(source,{}).get('type')!='resource' or ids.get(target,{}).get('type')!='resource': raise InvalidDiagram('Una conexión tiene extremos inexistentes, repetidos o iguales. Revisa sus recursos.')
        seen.add(key)
        item=dict(id=key,source=source,target=target,label=text(e.get('label',''),100))
        for field,node_id in [('sourceHandle',source),('targetHandle',target)]:
            handle=e.get(field)
            if handle is not None:
                if handle not in ['north','south','east','west'] or (handle in ['north','south'] and ids[node_id]['data']['kind'] in ['grupo','nota','etiqueta']):raise InvalidDiagram('Una conexión usa un punto de unión no disponible para ese recurso.')
                item[field]=handle
        if e.get('relation'):
            if e['relation'] not in ['hosts','belongs','depends','connected','storage','managed','used']:
                import re
                if not re.fullmatch(r'custom_[0-9a-f]{32}',str(e['relation'])):raise InvalidDiagram()
                if not defer_instances and e['relation'] not in {f['id'] for section in (schemas or {}).get(source,{}).get('sections',[]) if section['id']=='relationships' for f in section['fields']}:raise InvalidDiagram('La relación no pertenece al modelo del recurso de origen.')
            item['relation']=e['relation']
        if 'type' in e:
            if e['type'] not in ['straight','default','smoothstep','step']:raise InvalidDiagram()
            item['type']=e['type']
        for field,options in [('pattern',['solid','dashed','dotted','dashdot','longdash']),('arrows',['none','start','end','both']),('color',['auto','forest','graphite','blue','purple','amber','rose'])]:
            if field in e:
                if e[field] not in options:raise InvalidDiagram('Revisa el estilo de la conexión.')
                item[field]=e[field]
        if 'routePoints' in e:
            if not isinstance(e['routePoints'],list) or not (len(e['routePoints'])==0 or 2<=len(e['routePoints'])<=64):raise InvalidDiagram('El recorrido admite de 2 a 64 puntos.')
            item['routePoints']=[dict(x=number(v.get('x'),-100000,100000),y=number(v.get('y'),-100000,100000)) for v in e['routePoints']]
        if 'bends' in e:
            if not isinstance(e['bends'],list) or len(e['bends'])!=3 or not all(isinstance(v,dict) for v in e['bends']):raise InvalidDiagram('El recorrido necesita tres puntos de ajuste válidos.')
            item['bends']=[dict(x=number(v.get('x'),-10000,10000),y=number(v.get('y'),-10000,10000)) for v in e['bends']]
        connections.append(item)
    hosting={};children={}
    for edge in connections:
        if edge.get('relation')!='hosts':continue
        if edge['target'] in hosting:raise InvalidDiagram('Un componente no puede estar dentro de dos recursos. Usa una relación de dependencia para el segundo vínculo.')
        hosting[edge['target']]=edge['source'];children.setdefault(edge['source'],[]).append(edge['target'])
    def visit(n,trail):
        if n in trail:raise InvalidDiagram('El alojamiento forma un ciclo: un componente no puede contener a su propio contenedor.')
        for child in children.get(n,[]):visit(child,trail|{n})
    for root in children:visit(root,set())
    clean.sort(key=lambda n:n['type']!='resourceGroup')
    return dict(name=name,nodes=clean,edges=connections)

@contextmanager
def connection(subject):
    with psycopg.connect(os.environ['DIAGRAM_DATABASE_URL'],connect_timeout=5,row_factory=dict_row) as conn:
        # Transaction-local identity; never accepts a subject/organization from a browser.
        conn.execute("SELECT set_config('koodaria.subject', %s, true)",(subject,))
        yield conn

@bp.before_request
def authorize():
    if not session.get('identity',{}).get('sub') or session.get('expires_at',0)<=time.time():
        return jsonify(error='La sesión venció. Vuelve a iniciar sesión.',code='session_expired'),401
    if request.method not in ('GET','HEAD','OPTIONS'):
        expected=session.get('csrf','')
        if not expected or not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),expected):
            return jsonify(error='No se pudo verificar la solicitud. Recupera tu sesión para continuar.',code='csrf_invalid'),403
        if request.mimetype!='application/json': return jsonify(error='Se requiere JSON.'),415

@bp.errorhandler(Exception)
def failure(exc):
    from faults import Fault
    if isinstance(exc,Fault):return jsonify(error=str(exc),error_code=exc.code),exc.status
    if isinstance(exc, InvitationUnavailable): return jsonify(error=str(exc),error_code='KOD-MAIL-001'),503
    if isinstance(exc, psycopg.errors.UniqueViolation): return jsonify(error='Ya existe una carpeta con ese nombre.'),409
    if isinstance(exc, HTTPException): return jsonify(error='La solicitud no es válida.'),exc.code
    if isinstance(exc,InvalidDiagram) and str(exc):return jsonify(error=str(exc)),400
    if isinstance(exc,(InvalidDiagram,TypeError,KeyError,ValueError)): return jsonify(error='El diagrama no es válido. Revisa sus datos.'),400
    # No connection strings, diagram data or credentials in errors/logs.
    return jsonify(error='No se pudo acceder al guardado. Tus cambios siguen en esta pestaña; vuelve a intentarlo.'),503

def subject(): return session['identity']['sub']
def key(value):
    if not isinstance(value,str):raise InvalidDiagram()
    return uuid.UUID(value)
def serialize(row):
    row=dict(row)
    row['id']=str(row['id'])
    row['updated_at']=row['updated_at'].isoformat()
    if row.get('folder_id'): row['folder_id']=str(row['folder_id'])
    return row

def require_member(conn):
    if not is_member(conn): abort(403)

def owner_record(conn, diagram_id):
    return conn.execute('SELECT id,name,document,revision,updated_at,folder_id FROM resource_diagrams WHERE id=%s AND owner_sub=%s',(key(diagram_id),subject())).fetchone()

def fetch(conn, diagram_id):
    return conn.execute('SELECT id,name,document,revision,updated_at,folder_id FROM resource_diagrams WHERE id=%s AND (owner_sub=%s OR diagram_visible(id))',(key(diagram_id),subject())).fetchone()

def visible_folder(conn, folder_id):
    return conn.execute('SELECT id,name,revision,updated_at FROM diagram_folders WHERE id=%s AND owner_sub=%s',(key(folder_id),subject())).fetchone()

@bp.get('')
def listing():
    page=max(1,min(100000,int(request.args.get('page',1))))
    page_size=max(1,min(8,int(request.args.get('page_size',8))))
    folder=request.args.get('folder','all')
    scope=request.args.get('scope','mine')
    if scope not in ('mine','shared'):raise InvalidDiagram()
    with connection(subject()) as conn:
        member=is_member(conn)
        if scope=='shared':
            query="SELECT id,name,revision,updated_at,'diagram' AS kind,NULL::uuid AS folder_id,jsonb_array_length(document->'nodes') AS resources FROM resource_diagrams WHERE owner_sub<>%s AND diagram_visible(id)"
            params=(subject(),)
        elif not member:
            return jsonify(items=[],total=0,page=page,page_size=page_size)
        elif folder=='root':
            query="""SELECT id,name,revision,updated_at,'folder' AS kind, NULL::uuid AS folder_id,
                     (SELECT count(*) FROM resource_diagrams d WHERE d.folder_id=f.id AND d.owner_sub=f.owner_sub) AS resources
                     FROM diagram_folders f WHERE owner_sub=%s
                     UNION ALL SELECT id,name,revision,updated_at,'diagram' AS kind,folder_id,jsonb_array_length(document->'nodes') AS resources
                     FROM resource_diagrams WHERE owner_sub=%s AND folder_id IS NULL"""
            params=(subject(),subject())
        else:
            condition=''
            params=(subject(),)
            if folder=='none': condition=' AND folder_id IS NULL'
            elif folder!='all':
                if not visible_folder(conn,folder):return jsonify(error='Carpeta no encontrada.'),404
                condition=' AND folder_id=%s';params+=(key(folder),)
            query="SELECT id,name,revision,updated_at,'diagram' AS kind,folder_id,jsonb_array_length(document->'nodes') AS resources FROM resource_diagrams WHERE owner_sub=%s"+condition
        total=conn.execute('SELECT count(*) AS count FROM ('+query+') AS items',params).fetchone()['count']
        rows=conn.execute('SELECT * FROM ('+query+") AS items ORDER BY (kind='folder') DESC, CASE WHEN kind='folder' THEN lower(name) END,updated_at DESC,id LIMIT %s OFFSET %s",params+(page_size,(page-1)*page_size)).fetchall()
    return jsonify(items=[serialize(r) for r in rows],total=total,page=page,page_size=page_size)

@bp.get('/folders')
def folders():
    with connection(subject()) as conn:
        rows=conn.execute('SELECT id,name,revision,updated_at FROM diagram_folders WHERE owner_sub=%s ORDER BY lower(name),id LIMIT 200',(subject(),)).fetchall()
    return jsonify(items=[serialize(r) for r in rows])

@bp.post('/folders')
def create_folder():
    name=text((request.get_json() or {}).get('name'),100,True)
    with connection(subject()) as conn:
        require_member(conn)
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(subject(),))
        if conn.execute('SELECT count(*) AS count FROM diagram_folders WHERE owner_sub=%s',(subject(),)).fetchone()['count']>=200:
            return jsonify(error='Puedes crear hasta 200 carpetas.'),400
        row=conn.execute('INSERT INTO diagram_folders(owner_sub,name) VALUES(%s,%s) RETURNING id,name,revision,updated_at',(subject(),name)).fetchone()
    return jsonify(serialize(row)),201

@bp.put('/folders/<folder_id>')
def rename_folder(folder_id):
    body=request.get_json() or {};name=text(body.get('name'),100,True)
    if type(body.get('revision'))!=int:raise InvalidDiagram()
    with connection(subject()) as conn:
        require_member(conn)
        row=conn.execute('UPDATE diagram_folders SET name=%s,revision=revision+1,updated_at=now() WHERE id=%s AND owner_sub=%s AND revision=%s RETURNING id,name,revision,updated_at',(name,key(folder_id),subject(),body['revision'])).fetchone()
        if not row:return jsonify(error='La carpeta cambió o ya no está disponible. Actualiza la lista.'),409
    return jsonify(serialize(row))

@bp.delete('/folders/<folder_id>')
def delete_folder(folder_id):
    revision=(request.get_json() or {}).get('revision')
    if type(revision)!=int:raise InvalidDiagram()
    with connection(subject()) as conn:
        require_member(conn)
        row=conn.execute('DELETE FROM diagram_folders WHERE id=%s AND owner_sub=%s AND revision=%s RETURNING id',(key(folder_id),subject(),revision)).fetchone()
        if not row:return jsonify(error='La carpeta cambió o ya no está disponible. Actualiza la lista.'),409
    return '',204

@bp.post('/move')
def move():
    body=request.get_json() or {};items=body.get('items');destination=body.get('folder_id')
    if not isinstance(items,list) or not 1<=len(items)<=8:raise InvalidDiagram()
    ids=[]
    for item in items:
        if not isinstance(item,dict) or type(item.get('revision'))!=int:raise InvalidDiagram()
        ids.append(key(item.get('id')))
    if len(set(ids))!=len(ids):raise InvalidDiagram()
    with connection(subject()) as conn:
        require_member(conn)
        if destination and not visible_folder(conn,destination):return jsonify(error='Carpeta no encontrada.'),404
        from collaboration import lock_diagram
        for did in sorted(ids,key=str):lock_diagram(conn,did)
        rows=conn.execute('SELECT id,revision FROM resource_diagrams WHERE owner_sub=%s AND id=ANY(%s) ORDER BY id FOR UPDATE',(subject(),ids)).fetchall()
        revisions={r['id']:r['revision'] for r in rows}
        if len(rows)!=len(items) or any(revisions.get(id)!=item['revision'] for id,item in zip(ids,items)):
            return jsonify(error='Algún diagrama cambió o ya no está disponible. Actualiza la lista antes de moverlo.'),409
        conn.execute('UPDATE resource_diagrams SET folder_id=%s,revision=revision+1,updated_at=now() WHERE owner_sub=%s AND id=ANY(%s)',(key(destination) if destination else None,subject(),ids))
    return jsonify(moved=len(ids))

@bp.post('')
def create():
    body=request.get_json() or {}
    value=validate(starter(body.get('template_id','blank'),body.get('name','Nuevo diagrama')))
    folder_id=(request.get_json() or {}).get('folder_id')
    with connection(subject()) as conn:
        require_member(conn)
        from standards import bind,reference
        if body.get('standard'):
            for node in value['nodes']:
                if node['data']['kind'] in ['servidor','virtual']:node['data']['standard']=reference(body['standard'])
        from component_models import resolve
        models=resolve(conn,value)
        value=validate(value,models)
        value=bind(conn,value,models=models)
        if folder_id and not visible_folder(conn,folder_id):return jsonify(error='Carpeta no encontrada.'),404
        row=conn.execute('INSERT INTO resource_diagrams(owner_sub,name,document,folder_id) VALUES (%s,%s,%s,%s) RETURNING id,name,document,revision,updated_at,folder_id',(subject(),value['name'],Jsonb(value),key(folder_id) if folder_id else None)).fetchone()
    return jsonify(serialize(row)),201

@bp.get('/<diagram_id>')
def get(diagram_id):
    with connection(subject()) as conn:
        row=fetch(conn,diagram_id)
        owned=bool(owner_record(conn,diagram_id))
        editable=conn.execute('SELECT diagram_granted(%s) AS allowed',(key(diagram_id),)).fetchone()['allowed']
    if not row: return jsonify(error='Diagrama no encontrado.'),404
    row['access']='owner' if owned else 'editor' if editable else 'viewer'
    if not owned:row['folder_id']=None
    return jsonify(serialize(row))

def prepare_document(conn,incoming_document,original):
    value=validate(incoming_document,defer_instances=True)
    from standards import bind
    old_nodes={n['id']:n for n in original['document']['nodes']}
    for node in value['nodes']:
        old=old_nodes.get(node['id'],{}).get('data',{})
        if old and old.get('kind')!=node['data']['kind']:
            require_member(conn)
            if not node['data'].get('model_ref'):raise InvalidDiagram('Selecciona un estándar publicado para reclasificar el componente.')
        for field in ['provider','technology','location','server_instance','component_instance']:
            if field not in node['data'] and field in old and old.get('kind')==node['data']['kind'] and not (field in ['server_instance','component_instance'] and node['data'].get('model_ref') and node['data']['model_ref']!=old.get('model_ref')):node['data'][field]=old[field]
    old_edges={e['id']:e for e in original['document']['edges']}
    for edge in value['edges']:
        old=old_edges.get(edge['id'],{})
        for field in ['type','pattern','arrows','color','bends','routePoints']:
            if field not in edge and field in old:edge[field]=old[field]
        incoming=next(e for e in incoming_document['edges'] if e['id']==edge['id'])
        if 'relation' not in incoming and 'relation' in old and old.get('source')==edge['source'] and old.get('target')==edge['target']:edge['relation']=old['relation']
        for field,endpoint in [('sourceHandle','source'),('targetHandle','target')]:
            incoming=next(e for e in incoming_document['edges'] if e['id']==edge['id'])
            if field not in incoming and old.get(endpoint)==edge[endpoint] and field in old and next(n for n in value['nodes'] if n['id']==edge[endpoint])['data']['kind'] in ['servidor','virtual']:edge[field]=old[field]
    from component_models import resolve
    models=resolve(conn,value,original['document'])
    value=validate(value,models)
    value=bind(conn,value,original['document'],models=models)
    return value

@bp.put('/<diagram_id>')
def save(diagram_id):
    body=request.get_json()
    if not isinstance(body,dict): raise InvalidDiagram()
    revision=body.get('revision')
    if type(revision)!=int or revision<1: raise InvalidDiagram()
    value=validate(body.get('document'),defer_instances=True)
    with connection(subject()) as conn:
        from collaboration import lock_diagram, check_legacy_edit
        lock_diagram(conn,diagram_id)
        original=fetch(conn,diagram_id)
        if not original:return jsonify(error='Diagrama no encontrado.'),404
        if not conn.execute('SELECT diagram_owned(%s) OR diagram_granted(%s) AS allowed',(key(diagram_id),key(diagram_id))).fetchone()['allowed']:abort(403)
        check_legacy_edit(conn,diagram_id)
        value=prepare_document(conn,body['document'],original)
        row=conn.execute('UPDATE resource_diagrams SET name=%s,document=%s,revision=revision+1,updated_at=now() WHERE id=%s AND (owner_sub=%s OR diagram_granted(id)) AND revision=%s RETURNING id,name,revision,updated_at',(value['name'],Jsonb(value),key(diagram_id),subject(),revision)).fetchone()
        if not row:
            if not fetch(conn,diagram_id): return jsonify(error='Diagrama no encontrado.'),404
            return jsonify(error='Este diagrama cambió en otra pestaña. Conservamos tus cambios aquí. Guárdalos como copia o vuelve a abrir la versión guardada.'),409
        conn.execute("INSERT INTO diagram_audit(diagram_id,actor_sub,action) VALUES(%s,%s,'edit')",(key(diagram_id),subject()))
    return jsonify(serialize(row))

@bp.delete('/<diagram_id>')
def delete(diagram_id):
    revision=(request.get_json() or {}).get('revision')
    if type(revision)!=int: raise InvalidDiagram()
    with connection(subject()) as conn:
        from collaboration import lock_diagram,check_legacy_edit
        lock_diagram(conn,diagram_id);check_legacy_edit(conn,diagram_id)
        row=conn.execute('DELETE FROM resource_diagrams WHERE id=%s AND owner_sub=%s AND revision=%s RETURNING id',(key(diagram_id),subject(),revision)).fetchone()
        if not row:
            return jsonify(error='No se eliminó. El diagrama no existe o cambió; actualiza la lista.'),409
    return '',204

@bp.post('/<diagram_id>/pdf')
def canvas_pdf(diagram_id):
    from faults import Fault
    request.max_content_length=9000000
    body=request.get_json()
    if not isinstance(body,dict) or type(body.get('revision')) is not int:raise Fault('KOD-PDF-001')
    with connection(subject()) as conn:row=fetch(conn,diagram_id)
    if not row:return jsonify(error='Diagrama no encontrado.'),404
    if body['revision']!=row['revision']:return jsonify(error='El diagrama cambió. Vuelve a abrir la versión guardada antes de exportar.',error_code='KOD-DIA-002'),409
    from diagram_pdf import render_canvas_pdf
    return send_file(render_canvas_pdf(row,body),mimetype='application/pdf',as_attachment=True,download_name='koodaria-diagrama.pdf',max_age=0)


@bp.get('/<diagram_id>/pdf')
def pdf(diagram_id):
    with connection(subject()) as conn: row=fetch(conn,diagram_id)
    if not row: return jsonify(error='Diagrama no encontrado.'),404
    from diagram_pdf import render_pdf
    return send_file(render_pdf(row),mimetype='application/pdf',as_attachment=True,download_name='koodaria-mapeo-recursos.pdf',max_age=0)


@bp.get('/capabilities')
def get_capabilities():
    with connection(subject()) as conn: value=capabilities(conn)
    return jsonify(**value,invitations_ready=provision_ready(),notifications_ready=mail_ready())

@bp.get('/<diagram_id>/shares')
def shares(diagram_id):
    with connection(subject()) as conn:
        if not owner_record(conn,diagram_id):return jsonify(error='Diagrama no encontrado.'),404
        rows=conn.execute('SELECT id,recipient_email,permission,status,updated_at FROM diagram_shares WHERE diagram_id=%s AND owner_sub=%s ORDER BY updated_at DESC LIMIT 100',(key(diagram_id),subject())).fetchall()
    return jsonify(items=[serialize(r) for r in rows])

@bp.post('/<diagram_id>/shares')
def share(diagram_id):
    body=request.get_json() or {}
    try:email=normalize_email(body.get('email'))
    except ValueError:return jsonify(error='Introduce un correo electrónico válido.'),400
    provider=None;onboarding=False;notification=False
    with connection(subject()) as conn:
        from collaboration import lock_diagram
        lock_diagram(conn,diagram_id)
        require_member(conn)
        row=owner_record(conn,diagram_id)
        if not row:return jsonify(error='Diagrama no encontrado.'),404
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(diagram_id+email,))
        if conn.execute("SELECT count(*) AS count FROM diagram_shares WHERE owner_sub=%s AND last_sent_at>now()-interval '1 minute'",(subject(),)).fetchone()['count']>=10:
            return jsonify(error='Se alcanzó el límite de invitaciones por minuto. Vuelve a intentarlo más tarde.'),429
        previous=conn.execute('SELECT * FROM diagram_shares WHERE diagram_id=%s AND recipient_email=%s AND owner_sub=%s',(key(diagram_id),email,subject())).fetchone()
        if previous and previous['last_sent_at'] and (time.time()-previous['last_sent_at'].timestamp())<60:
            return jsonify(error='Espera un minuto antes de reenviar la invitación.'),429
        if not previous and conn.execute('SELECT count(*) AS count FROM diagram_shares WHERE diagram_id=%s AND owner_sub=%s',(key(diagram_id),subject())).fetchone()['count']>=100:
            return jsonify(error='Este diagrama admite hasta 100 personas invitadas.'),400
        found=conn.execute('SELECT * FROM principal_by_email(%s)',(email,)).fetchall()
        if len(found)>1:return jsonify(error='El correo requiere revisión por el administrador.'),409
        if found:
            recipient=found[0]['subject'];status='active'
        else:
            provider=IdentityProvider()
            recipient,onboarding=provider.provision(email,subject());status='pending'
        if recipient==subject():return jsonify(error='Ya eres propietario de este diagrama.'),400
        result=conn.execute("INSERT INTO diagram_shares(diagram_id,owner_sub,recipient_email,recipient_sub,status,last_sent_at) VALUES(%s,%s,%s,%s,%s,now()) ON CONFLICT(diagram_id,recipient_email) DO UPDATE SET recipient_sub=EXCLUDED.recipient_sub,status=EXCLUDED.status,updated_at=now(),expires_at=now()+interval '7 days',last_sent_at=now() RETURNING id,recipient_email,status,updated_at",(key(diagram_id),subject(),email,recipient,status)).fetchone()
        conn.execute("INSERT INTO diagram_audit(diagram_id,actor_sub,action) VALUES(%s,%s,'share')",(key(diagram_id),subject()))
    if onboarding:
        try:provider.send_onboarding(recipient);notification=True
        except InvitationUnavailable:
            with connection(subject()) as conn:conn.execute("UPDATE diagram_shares SET status='delivery_failed',updated_at=now() WHERE id=%s AND owner_sub=%s",(result['id'],subject()))
            return jsonify(error='La cuenta invitada quedó preparada, pero no se pudo entregar el correo. Reintenta la invitación; todavía no tiene acceso al diagrama.'),503
    else:notification=notify_existing(email,row['name'])
    return jsonify(**serialize(result),notification_sent=notification,message='Invitación enviada.' if notification else 'Acceso compartido. El aviso por correo está pendiente de configuración.'),201

@bp.delete('/<diagram_id>/shares/<share_id>')
def revoke_share(diagram_id,share_id):
    with connection(subject()) as conn:
        from collaboration import lock_diagram
        lock_diagram(conn,diagram_id)
        if not owner_record(conn,diagram_id):return jsonify(error='Diagrama no encontrado.'),404
        row=conn.execute("UPDATE diagram_shares SET status='revoked',updated_at=now() WHERE id=%s AND diagram_id=%s AND owner_sub=%s RETURNING id,recipient_sub",(key(share_id),key(diagram_id),subject())).fetchone()
        if not row:return jsonify(error='Acceso no encontrado.'),404
        conn.execute('DELETE FROM diagram_collaborators WHERE diagram_id=%s AND actor_sub=%s',(key(diagram_id),row['recipient_sub']))
        conn.execute("INSERT INTO diagram_audit(diagram_id,actor_sub,action) VALUES(%s,%s,'revoke')",(key(diagram_id),subject()))
    return '',204

from collaboration import register as register_collaboration
register_collaboration(bp)

from diagram_comments import register as register_comments
register_comments(bp)
