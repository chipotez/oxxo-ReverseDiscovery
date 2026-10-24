"""Authenticated diagram storage. Every query is scoped to the verified OIDC subject."""
import math
import os
import uuid
from contextlib import contextmanager
import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from flask import Blueprint, jsonify, request, session, send_file
from werkzeug.exceptions import HTTPException
import secrets
import time

bp = Blueprint('diagrams', __name__, url_prefix='/bienvenida/api/diagrams')
KINDS = {'origen', 'balanceador', 'servidor', 'servicio', 'datos', 'externo', 'grupo'}

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

def validate(value):
    if not isinstance(value, dict): raise InvalidDiagram()
    name = text(value.get('name'), 100, True)
    nodes, edges = value.get('nodes'), value.get('edges')
    if not isinstance(nodes, list) or not isinstance(edges, list) or len(nodes)>200 or len(edges)>500:
        raise InvalidDiagram()
    clean, ids = [], {}
    for n in nodes:
        if not isinstance(n, dict): raise InvalidDiagram()
        key = text(n.get('id'), 100, True)
        kind = n.get('type')
        data, pos = n.get('data'), n.get('position')
        if key in ids or kind not in ('resource', 'resourceGroup') or not isinstance(data, dict) or not isinstance(pos, dict): raise InvalidDiagram()
        if data.get('kind') not in KINDS or (kind=='resourceGroup') != (data['kind']=='grupo'): raise InvalidDiagram()
        out = dict(id=key, type=kind, position=dict(x=number(pos.get('x'),-100000,100000),y=number(pos.get('y'),-100000,100000)), data=dict(label=text(data.get('label'),100,True),kind=data['kind'],address=text(data.get('address',''),120),port=text(data.get('port',''),40)))
        if kind=='resourceGroup':
            style=n.get('style',{})
            if not isinstance(style,dict) or n.get('parentId'): raise InvalidDiagram()
            out['style']=dict(width=number(style.get('width',380),260,3000),height=number(style.get('height',260),180,3000))
        if n.get('parentId'):
            out.update(parentId=text(n['parentId'],100,True),extent='parent')
        ids[key]=out
        clean.append(out)
    for n in clean:
        if n.get('parentId') and ids.get(n['parentId'],{}).get('type')!='resourceGroup': raise InvalidDiagram()
    connections, seen = [], set()
    for e in edges:
        if not isinstance(e,dict): raise InvalidDiagram()
        key=text(e.get('id'),120,True)
        source, target=e.get('source'),e.get('target')
        if not isinstance(source,str) or not isinstance(target,str) or key in seen or source==target or ids.get(source,{}).get('type')!='resource' or ids.get(target,{}).get('type')!='resource': raise InvalidDiagram()
        seen.add(key)
        connections.append(dict(id=key,source=source,target=target,label=text(e.get('label',''),100)))
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
    if isinstance(exc, HTTPException): return jsonify(error='La solicitud no es válida.'),exc.code
    if isinstance(exc,(InvalidDiagram,TypeError,KeyError,ValueError)): return jsonify(error='El diagrama no es válido. Revisa sus datos.'),400
    # No connection strings, diagram data or credentials in errors/logs.
    return jsonify(error='No se pudo acceder al guardado. Tus cambios siguen en esta pestaña; vuelve a intentarlo.'),503

def subject(): return session['identity']['sub']
def key(value): return uuid.UUID(value)
def serialize(row):
    row=dict(row)
    row['id']=str(row['id'])
    row['updated_at']=row['updated_at'].isoformat()
    return row

def fetch(conn, diagram_id):
    return conn.execute('SELECT id,name,document,revision,updated_at FROM resource_diagrams WHERE id=%s AND owner_sub=%s',(key(diagram_id),subject())).fetchone()

@bp.get('')
def listing():
    page=max(1,int(request.args.get('page',1)))
    page=min(page,100000)
    page_size=max(1,min(8,int(request.args.get('page_size',8))))
    with connection(subject()) as conn:
        total=conn.execute('SELECT count(*) AS count FROM resource_diagrams WHERE owner_sub=%s',(subject(),)).fetchone()['count']
        rows=conn.execute('SELECT id,name,revision,updated_at,jsonb_array_length(document->\'nodes\') AS resources FROM resource_diagrams WHERE owner_sub=%s ORDER BY updated_at DESC,id LIMIT %s OFFSET %s',(subject(),page_size,(page-1)*page_size)).fetchall()
    return jsonify(items=[serialize(r) for r in rows],total=total,page=page,page_size=page_size)

@bp.post('')
def create():
    value=validate(dict(name=(request.get_json() or {}).get('name','Nuevo diagrama'),nodes=[],edges=[]))
    with connection(subject()) as conn:
        row=conn.execute('INSERT INTO resource_diagrams(owner_sub,name,document) VALUES (%s,%s,%s) RETURNING id,name,document,revision,updated_at',(subject(),value['name'],Jsonb(value))).fetchone()
    return jsonify(serialize(row)),201

@bp.get('/<diagram_id>')
def get(diagram_id):
    with connection(subject()) as conn: row=fetch(conn,diagram_id)
    if not row: return jsonify(error='Diagrama no encontrado.'),404
    return jsonify(serialize(row))

@bp.put('/<diagram_id>')
def save(diagram_id):
    body=request.get_json()
    if not isinstance(body,dict): raise InvalidDiagram()
    revision=body.get('revision')
    if type(revision)!=int or revision<1: raise InvalidDiagram()
    value=validate(body.get('document'))
    with connection(subject()) as conn:
        row=conn.execute('UPDATE resource_diagrams SET name=%s,document=%s,revision=revision+1,updated_at=now() WHERE id=%s AND owner_sub=%s AND revision=%s RETURNING id,name,revision,updated_at',(value['name'],Jsonb(value),key(diagram_id),subject(),revision)).fetchone()
        if not row:
            if not fetch(conn,diagram_id): return jsonify(error='Diagrama no encontrado.'),404
            return jsonify(error='Este diagrama cambió en otra pestaña. Conservamos tus cambios aquí. Guárdalos como copia o vuelve a abrir la versión guardada.'),409
    return jsonify(serialize(row))

@bp.delete('/<diagram_id>')
def delete(diagram_id):
    revision=(request.get_json() or {}).get('revision')
    if type(revision)!=int: raise InvalidDiagram()
    with connection(subject()) as conn:
        row=conn.execute('DELETE FROM resource_diagrams WHERE id=%s AND owner_sub=%s AND revision=%s RETURNING id',(key(diagram_id),subject(),revision)).fetchone()
        if not row:
            return jsonify(error='No se eliminó. El diagrama no existe o cambió; actualiza la lista.'),409
    return '',204

@bp.get('/<diagram_id>/pdf')
def pdf(diagram_id):
    with connection(subject()) as conn: row=fetch(conn,diagram_id)
    if not row: return jsonify(error='Diagrama no encontrado.'),404
    from diagram_pdf import render_pdf
    return send_file(render_pdf(row),mimetype='application/pdf',as_attachment=True,download_name='koodaria-mapeo-recursos.pdf',max_age=0)
