"""Transactional collaboration. All coordination is PostgreSQL-backed across workers.
No last-writer-wins: writes compare the exact field before applying an atomic batch.
"""
import copy, uuid
from flask import jsonify, request, session
from psycopg.types.json import Jsonb
from faults import Fault

def lock_diagram(conn,diagram_id):
    # The same lock is acquired by operations, leases, legacy writes and revocation.
    conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',('collab:'+str(diagram_id),))

def peers(conn,diagram_id):
    return conn.execute('SELECT client_id,actor_sub,display_name,resource_id FROM diagram_collaborators WHERE diagram_id=%s AND expires_at>now()',(diagram_id,)).fetchall()

def check_legacy_edit(conn,diagram_id):
    if peers(conn,diagram_id):raise Fault('KOD-COL-004','Hay una sesión colaborativa activa. Actualiza esta pestaña antes de editar.',status=409)

def conflict(message='Este campo cambió durante tu edición. Revisa la versión compartida antes de aplicar tus cambios.'):
    raise Fault('KOD-COL-001',message,status=409)

def descendant_ids(document,roots):
    found=set(roots)
    while True:
        previous=len(found)
        found.update(e['target'] for e in document['edges'] if e.get('relation')=='hosts' and e['source'] in found)
        found.update(n['id'] for n in document['nodes'] if n.get('parentId') in found)
        if len(found)==previous:return found

def apply_changes(document,changes):
    if not isinstance(changes,list) or not 1<=len(changes)<=4000:raise Fault('KOD-COL-002',status=400)
    value=copy.deepcopy(document);seen=set();touched=set()
    for change in changes:
        if not isinstance(change,dict):raise Fault('KOD-COL-002',status=400)
        collection=change.get('collection');identifier=change.get('id');path=change.get('path');before=change.get('before');after=change.get('after')
        if collection not in ('nodes','edges','document') or not isinstance(path,list) or len(path)>12 or any(not isinstance(k,str) or not k or k in ('__proto__','constructor','prototype') for k in path):raise Fault('KOD-COL-002',status=400)
        if not all(isinstance(v,dict) and type(v.get('exists')) is bool and (not v['exists'] or 'value' in v) for v in [before,after]):raise Fault('KOD-COL-002',status=400)
        token=(collection,identifier,tuple(path))
        if token in seen:raise Fault('KOD-COL-002',status=400)
        seen.add(token)
        if collection=='document':
            if path!=['name'] or identifier is not None:raise Fault('KOD-COL-002',status=400)
            target=value
        else:
            if not isinstance(identifier,str) or not 1<=len(identifier)<=240:raise Fault('KOD-COL-002',status=400)
            target=next((r for r in value[collection] if r['id']==identifier),None)
            if collection=='nodes':touched.add(identifier)
            else:
                edge=target or after.get('value',{})
                if isinstance(edge,dict):touched.update([edge.get('source'),edge.get('target')])
            if not path:
                actual={'exists':target is not None,**({'value':target} if target is not None else {})}
                if actual!=before:conflict()
                if after['exists']:
                    if not isinstance(after['value'],dict) or after['value'].get('id')!=identifier:raise Fault('KOD-COL-002',status=400)
                    if target is None:value[collection].append(copy.deepcopy(after['value']))
                    else:value[collection][value[collection].index(target)]=copy.deepcopy(after['value'])
                elif target is not None:value[collection].remove(target)
                continue
            if target is None:conflict('El componente o la conexión se eliminó. Conservamos tus cambios pendientes para que puedas revisarlos.')
            if path[0] in ('id','type') or collection=='nodes' and path[:2]==['data','kind']:raise Fault('KOD-COL-002',status=400)
        cursor=target
        for part in path[:-1]:
            if part not in cursor:cursor[part]={}
            if not isinstance(cursor[part],dict):conflict()
            cursor=cursor[part]
        actual={'exists':path[-1] in cursor,**({'value':cursor[path[-1]]} if path[-1] in cursor else {})}
        if actual!=before:conflict()
        if after['exists']:cursor[path[-1]]=copy.deepcopy(after['value'])
        else:cursor.pop(path[-1],None)
    return value,touched-{None}

def register(bp):
    from diagrams import connection,subject,key,fetch,serialize,prepare_document,owner_record
    def access(conn,did):
        row=fetch(conn,str(did))
        if not row:raise Fault('KOD-COL-003','El diagrama ya no está disponible o tu acceso fue retirado.',status=403)
        return row
    def client_key(body):return key(body.get('client_id'))
    def can_edit(conn,did):
        return conn.execute('SELECT diagram_owned(%s) OR diagram_granted(%s) AS allowed',(did,did)).fetchone()['allowed']
    def packet(conn,row):
        roster=[dict(client_id=str(p['client_id']),name=p['display_name'],resource_id=p['resource_id']) for p in peers(conn,row['id'])]
        visible=dict(row)
        if not owner_record(conn,str(row['id'])):visible['folder_id']=None
        return dict(**serialize(visible),participants=roster,can_edit=can_edit(conn,row['id']))
    @bp.post('/<diagram_id>/collaboration/sync')
    def sync(diagram_id):
        body=request.get_json() or {};cid=client_key(body);did=key(diagram_id);resource=body.get('resource_id')
        if resource is not None and (not isinstance(resource,str) or len(resource)>100):raise Fault('KOD-COL-002',status=400)
        with connection(subject()) as conn:
            lock_diagram(conn,did);row=access(conn,did)
            # A client ID cannot be used to steal another user's lease.
            prior=conn.execute('SELECT actor_sub FROM diagram_collaborators WHERE diagram_id=%s AND client_id=%s',(did,cid)).fetchone()
            if prior and prior['actor_sub']!=subject():raise Fault('KOD-COL-003',status=403)
            names={n['id'] for n in row['document']['nodes']}
            if resource not in names or not can_edit(conn,did):resource=None
            other=next((p for p in peers(conn,did) if p['client_id']!=cid and p['resource_id']==resource and resource is not None),None)
            held=None if other else resource
            identity=session.get('identity',{});display=str(identity.get('name') or identity.get('preferred_username') or 'Colaborador')[:80]
            conn.execute("INSERT INTO diagram_collaborators(diagram_id,client_id,actor_sub,display_name,resource_id,expires_at) VALUES(%s,%s,%s,%s,%s,now()+interval '20 seconds') ON CONFLICT(diagram_id,client_id) DO UPDATE SET resource_id=excluded.resource_id,display_name=excluded.display_name,expires_at=excluded.expires_at",(did,cid,subject(),display,held))
            payload=packet(conn,row)
            if body.get('revision')==row['revision']:payload.pop('document',None)
            return jsonify(**payload,reservation=dict(resource_id=held,blocked_by=other['display_name'] if other else None))
    @bp.post('/<diagram_id>/collaboration/leave')
    def leave(diagram_id):
        body=request.get_json() or {}
        with connection(subject()) as conn:conn.execute('DELETE FROM diagram_collaborators WHERE diagram_id=%s AND client_id=%s AND actor_sub=%s',(key(diagram_id),client_key(body),subject()))
        return '',204
    @bp.post('/<diagram_id>/collaboration/operations')
    def operations(diagram_id):
        body=request.get_json() or {};did=key(diagram_id);cid=client_key(body);oid=key(body.get('operation_id'));changes=body.get('changes')
        if type(body.get('base_revision')) is not int:raise Fault('KOD-COL-002',status=400)
        with connection(subject()) as conn:
            lock_diagram(conn,did);row=access(conn,did)
            if not can_edit(conn,did):raise Fault('KOD-COL-003',status=403)
            prior=conn.execute('SELECT actor_sub,client_id,changes FROM diagram_operations WHERE diagram_id=%s AND operation_id=%s',(did,oid)).fetchone()
            if prior:
                if prior['actor_sub']!=subject() or prior['client_id']!=cid or prior['changes']!=changes:raise Fault('KOD-COL-002',status=409)
                return jsonify(**packet(conn,row),operation_id=str(oid),duplicate=True)
            session_row=conn.execute('SELECT actor_sub FROM diagram_collaborators WHERE diagram_id=%s AND client_id=%s AND expires_at>now()',(did,cid)).fetchone()
            if not session_row or session_row['actor_sub']!=subject():raise Fault('KOD-COL-004','Recupera tu sesión colaborativa antes de enviar cambios.',status=409)
            if not 1<=body['base_revision']<=row['revision']:raise Fault('KOD-COL-002',status=400)
            value,touched=apply_changes(row['document'],changes)
            deleted={n['id'] for n in row['document']['nodes']}-{n['id'] for n in value['nodes']}
            protected=descendant_ids(row['document'],deleted)
            if protected-deleted:conflict('El recurso contiene componentes. Retíralos o elimínalos explícitamente antes de continuar.')
            affected=touched|protected
            for p in peers(conn,did):
                if p['client_id']!=cid and p['resource_id'] in affected:raise Fault('KOD-COL-004',p['display_name']+' está editando uno de los recursos afectados. Reintenta cuando termine.',status=409)
            # Removing parent or a hosts edge touches its children even if the node survives.
            for c in changes:
                if c.get('collection')=='edges':
                    edge=next((e for e in row['document']['edges'] if e['id']==c['id']),None)
                    if edge and edge.get('relation')=='hosts':
                        for p in peers(conn,did):
                            if p['client_id']!=cid and p['resource_id'] in descendant_ids(row['document'],{edge['target']}):raise Fault('KOD-COL-004','Hay una edición activa dentro del componente alojado.',status=409)
            value=prepare_document(conn,value,row)
            saved=conn.execute('UPDATE resource_diagrams SET name=%s,document=%s,revision=revision+1,updated_at=now() WHERE id=%s RETURNING id,name,document,revision,updated_at,folder_id',(value['name'],Jsonb(value),did)).fetchone()
            conn.execute('INSERT INTO diagram_operations(diagram_id,operation_id,actor_sub,client_id,display_name,revision,changes) VALUES(%s,%s,%s,%s,%s,%s,%s)',(did,oid,subject(),cid,str(session['identity'].get('name') or 'Colaborador')[:80],saved['revision'],Jsonb(changes)))
            if deleted:
                removed=dict(nodes=[n for n in row['document']['nodes'] if n['id'] in deleted],edges=[e for e in row['document']['edges'] if e['source'] in deleted or e['target'] in deleted])
                conn.execute('INSERT INTO diagram_trash(diagram_id,operation_id,actor_sub,resources) VALUES(%s,%s,%s,%s)',(did,oid,subject(),Jsonb(removed)))
            conn.execute("INSERT INTO diagram_audit(diagram_id,actor_sub,action) VALUES(%s,%s,'edit')",(did,subject()))
            return jsonify(**packet(conn,saved),operation_id=str(oid))
    @bp.get('/<diagram_id>/collaboration/history')
    def history(diagram_id):
        with connection(subject()) as conn:
            access(conn,diagram_id)
            rows=conn.execute('SELECT operation_id,revision,created_at,display_name,changes AS detail,actor_sub=current_setting(\'koodaria.subject\',true) AS mine,jsonb_array_length(changes) AS changes FROM diagram_operations WHERE diagram_id=%s ORDER BY revision DESC LIMIT 50',(key(diagram_id),)).fetchall()
            return jsonify(items=[dict(id=str(r['operation_id']),revision=r['revision'],actor=r['display_name'],at=r['created_at'].isoformat(),mine=r['mine'],changes=r['changes'],resources=list(dict.fromkeys(c.get('id') for c in r['detail'] if c.get('id')))[:5]) for r in rows])
    @bp.get('/<diagram_id>/collaboration/trash')
    def trash(diagram_id):
        with connection(subject()) as conn:
            if not owner_record(conn,diagram_id):raise Fault('KOD-COL-003',status=403)
            rows=conn.execute('SELECT id,created_at,resources FROM diagram_trash WHERE diagram_id=%s AND restored_at IS NULL ORDER BY created_at DESC LIMIT 30',(key(diagram_id),)).fetchall()
            return jsonify(items=[dict(id=str(r['id']),at=r['created_at'].isoformat(),names=[n['data']['label'] for n in r['resources']['nodes']]) for r in rows])
    @bp.post('/<diagram_id>/collaboration/trash/<trash_id>/restore')
    def restore(diagram_id,trash_id):
        did=key(diagram_id)
        with connection(subject()) as conn:
            lock_diagram(conn,did)
            row=owner_record(conn,diagram_id)
            if not row:raise Fault('KOD-COL-003',status=403)
            trash=conn.execute('SELECT resources FROM diagram_trash WHERE id=%s AND diagram_id=%s AND restored_at IS NULL',(key(trash_id),did)).fetchone()
            if not trash:raise Fault('KOD-COL-002',status=404)
            affected={n['id'] for n in trash['resources']['nodes']}|{e[k] for e in trash['resources']['edges'] for k in ['source','target']}
            if any(p['resource_id'] in affected for p in peers(conn,did)):raise Fault('KOD-COL-004','Hay una edición activa en un recurso relacionado con la restauración.',status=409)
            value=copy.deepcopy(row['document']);ids={n['id'] for n in value['nodes']}
            if any(n['id'] in ids for n in trash['resources']['nodes']):conflict('Algún componente ya fue restaurado. No se crearon duplicados.')
            value['nodes']+=trash['resources']['nodes'];ids={n['id'] for n in value['nodes']};eids={e['id'] for e in value['edges']}
            value['edges'] += [e for e in trash['resources']['edges'] if e['id'] not in eids and e['source'] in ids and e['target'] in ids]
            value=prepare_document(conn,value,row)
            conn.execute('UPDATE resource_diagrams SET document=%s,revision=revision+1,updated_at=now() WHERE id=%s',(Jsonb(value),did))
            conn.execute('UPDATE diagram_trash SET restored_at=now() WHERE id=%s',(key(trash_id),))
            changes=[dict(collection=col,id=r['id'],path=[],before=dict(exists=False),after=dict(exists=True,value=r)) for col in ['nodes','edges'] for r in value[col] if r['id'] not in {v['id'] for v in row['document'][col]}]
            conn.execute('INSERT INTO diagram_operations(diagram_id,operation_id,actor_sub,client_id,display_name,revision,changes) VALUES(%s,%s,%s,%s,%s,%s,%s)',(did,uuid.uuid4(),subject(),uuid.uuid4(),str(session['identity'].get('name') or 'Colaborador')[:80],row['revision']+1,Jsonb(changes)))
            conn.execute("INSERT INTO diagram_audit(diagram_id,actor_sub,action) VALUES(%s,%s,'edit')",(did,subject()))
            return jsonify(restored=True)

    @bp.put('/<diagram_id>/shares/<share_id>')
    def change_permission(diagram_id,share_id):
        permission=(request.get_json() or {}).get('permission')
        if permission not in ('read','edit'):raise Fault('KOD-COL-002',status=400)
        with connection(subject()) as conn:
            lock_diagram(conn,key(diagram_id))
            if not owner_record(conn,diagram_id):raise Fault('KOD-COL-003',status=403)
            row=conn.execute("UPDATE diagram_shares SET permission=%s,updated_at=now() WHERE id=%s AND diagram_id=%s AND status='active' RETURNING id,recipient_sub",(permission,key(share_id),key(diagram_id))).fetchone()
            if not row:raise Fault('KOD-COL-002',status=404)
            if permission=='read':conn.execute('DELETE FROM diagram_collaborators WHERE diagram_id=%s AND actor_sub=%s',(key(diagram_id),row['recipient_sub']))
            conn.execute("INSERT INTO diagram_audit(diagram_id,actor_sub,action) VALUES(%s,%s,'share')",(key(diagram_id),subject()))
        return jsonify(permission=permission)
