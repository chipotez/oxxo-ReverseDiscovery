"""Anchored discussion, separate from graph revisions; permissions on every request."""
import uuid
from flask import request,jsonify,abort

def register(bp):
    from diagrams import connection,subject,key,fetch,InvalidDiagram
    from collaboration import lock_diagram,current_identity
    def access(conn,diagram_id,edit=False):
        lock_diagram(conn,diagram_id)
        row=fetch(conn,diagram_id)
        if not row:abort(404)
        if edit and not conn.execute('SELECT diagram_owned(%s) OR diagram_granted(%s) AS allowed',(key(diagram_id),key(diagram_id))).fetchone()['allowed']:abort(403)
        return row
    def serialize(row):
        return {**row,'id':str(row['id']),'diagram_id':str(row['diagram_id']),'created_at':row['created_at'].isoformat(),'updated_at':row['updated_at'].isoformat()}
    @bp.get('/<diagram_id>/comments')
    def comments_list(diagram_id):
        with connection(subject()) as conn:
            access(conn,diagram_id)
            page=max(1,min(100000,int(request.args.get('page',1))))
            kind=request.args.get('anchor_type');anchor=request.args.get('anchor_id')
            clause='diagram_id=%s';params=[key(diagram_id)]
            if kind in ('node','edge') and anchor:clause+=' AND anchor_type=%s AND anchor_id=%s';params.extend([kind,anchor])
            total=conn.execute('SELECT count(*) AS total FROM diagram_comments WHERE '+clause,params).fetchone()['total']
            rows=conn.execute('SELECT * FROM diagram_comments WHERE '+clause+' ORDER BY created_at DESC LIMIT 3 OFFSET %s',params+[(page-1)*3]).fetchall()
        return jsonify(items=[serialize(r) for r in rows],total=total,page=page)
    @bp.post('/<diagram_id>/comments')
    def comments_create(diagram_id):
        body=request.get_json();kind=body.get('anchor_type');anchor=body.get('anchor_id');message=body.get('body','').strip();mentions=body.get('mentions',[])
        if kind not in ('node','edge') or not isinstance(anchor,str) or not 1<=len(message)<=2000 or not isinstance(mentions,list) or len(mentions)>10:raise InvalidDiagram('Revisa el comentario y su recurso de destino.')
        from psycopg.types.json import Jsonb
        with connection(subject()) as conn:
            diagram=access(conn,diagram_id,True)
            if not any(n['id']==anchor for n in diagram['document']['nodes' if kind=='node' else 'edges']):raise InvalidDiagram('El recurso anclado ya no existe.')
            # Mentions only target people who already have access. Never invite implicitly.
            allowed=conn.execute('SELECT * FROM diagram_comment_people(%s)',(key(diagram_id),)).fetchall()
            if any(v not in {p['subject'] for p in allowed} for v in mentions):abort(403)
            row=conn.execute('INSERT INTO diagram_comments(diagram_id,anchor_type,anchor_id,author_sub,author_name,body,mentions) VALUES(%s,%s,%s,%s,%s,%s,%s) RETURNING *',(key(diagram_id),kind,anchor,subject(),current_identity().get('name','Colaborador')[:200],message,Jsonb(mentions))).fetchone()
        return jsonify(item=serialize(row)),201
    @bp.patch('/<diagram_id>/comments/<comment_id>')
    def comments_resolve(diagram_id,comment_id):
        body=request.get_json()
        if type(body.get('resolved')) is not bool or type(body.get('revision')) is not int:raise InvalidDiagram()
        with connection(subject()) as conn:
            access(conn,diagram_id,True)
            row=conn.execute('UPDATE diagram_comments SET resolved=%s,revision=revision+1,updated_at=now() WHERE id=%s AND diagram_id=%s AND revision=%s RETURNING *',(body['resolved'],key(comment_id),key(diagram_id),body['revision'])).fetchone()
            if not row:return jsonify(error='Este comentario cambió. Actualiza antes de resolverlo.'),409
        return jsonify(item=serialize(row))
    @bp.get('/<diagram_id>/comment-people')
    def comment_people(diagram_id):
        with connection(subject()) as conn:
            access(conn,diagram_id)
            rows=conn.execute('SELECT * FROM diagram_comment_people(%s)',(key(diagram_id),)).fetchall()
        return jsonify(items=rows)
