"""Password-protected, one-hour diagram capabilities. Never creates an OIDC identity."""
import hashlib,secrets,time,uuid
from flask import Blueprint,request,session,render_template,abort,jsonify,g,current_app,redirect
from werkzeug.security import generate_password_hash,check_password_hash
from diagrams import connection,subject,key,owner_record,require_member,InvalidDiagram
from invitations import normalize_email
public=Blueprint('temporary_diagrams',__name__)

def current_identity():return getattr(g,'diagram_identity',None) or session.get('identity',{})
def temporary_authorization():
    visit=request.headers.get('X-Koodaria-Visit')
    if not visit:return None
    identity=session.get('diagram_visits',{}).get(visit)
    did=(request.view_args or {}).get('diagram_id')
    # Capability applies only to this diagram's edit, collaboration and comments API.
    if not identity or identity['expires_at']<=time.time() or did!=identity['diagram_id'] or not request.path.startswith('/bienvenida/api/diagrams/'):
        return jsonify(error='El enlace temporal venció o no permite esta operación.',error_code='KOD-LINK-001'),403
    allowed_suffix=request.path.split('/'+did,1)[1]
    if allowed_suffix and not (allowed_suffix.startswith('/collaboration/') or allowed_suffix.startswith('/comments') or allowed_suffix=='/comment-people' or allowed_suffix=='/pdf'):
        return jsonify(error='Este acceso solo permite colaborar en el diagrama.',error_code='KOD-LINK-001'),403
    with connection(identity['sub']) as db:
        allowed=db.execute('SELECT link_visit_active(%s,%s,%s) AS allowed',(key(visit),identity['sub'],key(did))).fetchone()['allowed']
    if not allowed:return jsonify(error='El enlace temporal venció o fue revocado.',error_code='KOD-LINK-001'),403
    g.diagram_identity=identity
    return True

def register(bp):
    @bp.post('/<diagram_id>/links')
    def create_link(diagram_id):
        password=(request.get_json() or {}).get('password')
        if not isinstance(password,str) or not 14<=len(password)<=128 or not password.strip():raise InvalidDiagram('Usa una contraseña de al menos 14 caracteres.')
        digest=generate_password_hash(password);token=secrets.token_urlsafe(32)
        with connection(subject()) as db:
            from collaboration import lock_diagram
            lock_diagram(db,key(diagram_id));require_member(db)
            if not owner_record(db,diagram_id):abort(404)
            if db.execute("SELECT count(*) AS n FROM diagram_links WHERE diagram_id=%s AND created_at>now()-interval '1 hour'",(key(diagram_id),)).fetchone()['n']>=20:
                return jsonify(error='Puedes crear hasta 20 enlaces por hora para este diagrama.'),429
            row=db.execute('INSERT INTO diagram_links(diagram_id,owner_sub,token_hash,password_hash) VALUES(%s,%s,%s,%s) RETURNING id,expires_at',(key(diagram_id),subject(),hashlib.sha256(token.encode()).hexdigest(),digest)).fetchone()
        return jsonify(id=str(row['id']),url='https://koodaria.com/bienvenida/colaborar/#'+token,expires_at=row['expires_at'].isoformat()),201
    @bp.get('/<diagram_id>/links')
    def list_links(diagram_id):
        with connection(subject()) as db:
            if not owner_record(db,diagram_id):abort(404)
            links=db.execute('SELECT id,created_at,expires_at,revoked_at FROM diagram_links WHERE diagram_id=%s ORDER BY created_at DESC LIMIT 50',(key(diagram_id),)).fetchall()
            visits=db.execute('SELECT v.id,v.link_id,v.display_name,v.email,v.joined_at FROM diagram_link_visits v JOIN diagram_links l ON l.id=v.link_id WHERE l.diagram_id=%s ORDER BY v.joined_at DESC LIMIT 200',(key(diagram_id),)).fetchall()
        return jsonify(items=[{k:str(v) if isinstance(v,uuid.UUID) else v.isoformat() if hasattr(v,'isoformat') else v for k,v in r.items()} for r in links],visits=[{k:str(v) if isinstance(v,uuid.UUID) else v.isoformat() if hasattr(v,'isoformat') else v for k,v in r.items()} for r in visits])
    @bp.delete('/<diagram_id>/links/<link_id>')
    def revoke_link(diagram_id,link_id):
        with connection(subject()) as db:
            from collaboration import lock_diagram
            lock_diagram(db,key(diagram_id))
            if not owner_record(db,diagram_id):abort(404)
            row=db.execute('UPDATE diagram_links SET revoked_at=now() WHERE id=%s AND diagram_id=%s RETURNING id',(key(link_id),key(diagram_id))).fetchone()
            if not row:abort(404)
        return '',204

@public.route('/bienvenida/colaborar/',methods=['GET','POST'])
def join():
    session.setdefault('csrf',secrets.token_urlsafe(32))
    if request.method=='GET':return render_template('link-gate.html',csrf=session['csrf'],unavailable=False,token='')
    if not secrets.compare_digest(request.form.get('csrf',''),session['csrf']):abort(403)
    token=request.form.get('token','')
    if not 20<=len(token)<=100:return render_template('link-gate.html',unavailable=True,csrf=session['csrf']),410
    with connection('link-gate') as db:row=db.execute('SELECT * FROM link_lookup(%s)',(hashlib.sha256(token.encode()).hexdigest(),)).fetchone()
    error=None;status=200
    if not row:return render_template('link-gate.html',unavailable=True,csrf=session['csrf']),410
    if request.method=='POST':
        if not secrets.compare_digest(request.form.get('csrf',''),session['csrf']):abort(403)
        password=request.form.get('password','');name=request.form.get('name','').strip();email=request.form.get('email','').strip().lower()
        bucket=hashlib.sha256((str(row['id'])+'|'+request.remote_addr+'|'+current_app.secret_key).encode()).hexdigest()
        with connection('link-gate') as db:allowed=db.execute('SELECT link_throttle(%s) AS allowed',(bucket,)).fetchone()['allowed']
        if not allowed:error='Demasiados intentos. Vuelve a intentar en diez minutos.';status=429
        elif not 2<=len(name)<=80 or len(password)>128:error='Completa tu nombre, correo y contraseña.';status=400
        else:
            try:email=normalize_email(email)
            except (ValueError,InvalidDiagram):error='Escribe un correo válido.';status=400
            if not error and not check_password_hash(row['password_hash'],password):error='No se pudo abrir el enlace. Revisa la contraseña.';status=403
            if not error:
                with connection('link-gate') as db:visit=db.execute('SELECT * FROM link_join(%s,%s,%s)',(row['id'],name,email)).fetchone()
                if not visit:return render_template('link-gate.html',unavailable=True,csrf=session['csrf']),410
                with connection('link-gate') as db:db.execute('SELECT link_throttle_reset(%s)',(bucket,))
                identity=dict(sub=visit['actor_sub'],name=name,email=email,diagram_id=str(visit['diagram_id']),expires_at=visit['expires_at'].timestamp())
                visits=dict(session.get('diagram_visits',{}));visits[str(visit['visit_id'])]=identity;session['diagram_visits']=dict(list(visits.items())[-10:])
                session.permanent=True
                return redirect('/bienvenida/colaborar/sesion/'+str(visit['visit_id']),code=303)
    return render_template('link-gate.html',csrf=session['csrf'],error=error,unavailable=False,token=token),status

@public.get('/bienvenida/colaborar/sesion/<visit>')
def visitor_workspace(visit):
    identity=session.get('diagram_visits',{}).get(visit)
    if not identity or identity['expires_at']<=time.time():return render_template('link-gate.html',unavailable=True,csrf=session.get('csrf','')),410
    with connection(identity['sub']) as db:
        allowed=db.execute('SELECT link_visit_active(%s,%s,%s) AS allowed',(key(visit),identity['sub'],key(identity['diagram_id']))).fetchone()['allowed']
    if not allowed:return render_template('link-gate.html',unavailable=True,csrf=session.get('csrf','')),410
    from datetime import datetime,timezone
    return render_template('temporary-workspace.html',identity=identity,visit=visit,csrf=session['csrf'],expires_at=datetime.fromtimestamp(identity['expires_at'],timezone.utc).isoformat())
