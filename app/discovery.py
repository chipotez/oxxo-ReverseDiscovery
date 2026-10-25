"""Organization-scoped, read-only discovery. Provider endpoints never come from clients."""
import base64,json,os,time,uuid
from datetime import datetime,timezone
import requests
from cryptography.fernet import Fernet,InvalidToken
from flask import Blueprint,jsonify,request,abort
from psycopg.types.json import Jsonb
from psycopg.errors import UniqueViolation
from diagrams import authorize,failure,connection,subject,require_member,key
from faults import Fault
SITES={s:'https://api.'+s for s in ['datadoghq.com','us3.datadoghq.com','us5.datadoghq.com','datadoghq.eu','ap1.datadoghq.com','ap2.datadoghq.com','ddog-gov.com','uk1.datadoghq.com','us2.ddog-gov.com']}
STAGES=['Conectividad','Credenciales','Permisos','Consulta de muestra']
bp=Blueprint('discovery',__name__,url_prefix='/bienvenida/api/discovery')
bp.before_request(authorize);bp.register_error_handler(Exception,failure)
@bp.errorhandler(UniqueViolation)
def duplicate(exc):return jsonify(error_code='KOD-CON-006',error='Ya existe una conexión con ese nombre.'),409

def cipher():
 try:return Fernet(os.environ['DISCOVERY_ENCRYPTION_KEY'].encode())
 except (KeyError,ValueError):raise Fault('KOD-CON-007',status=503) from None

def serial(row):
 # Explicit allowlist: encrypted credentials never leave the server.
 return {k:str(row[k]) if k in ['id','run_id'] and row[k] else row[k].isoformat() if k in ['updated_at','tested_at'] and row[k] else row[k] for k in ['id','name','provider','site','revision','status','run_id','stages','sample','sample_total','updated_at','tested_at']}

def owned(conn,cid,lock=False):
 row=conn.execute('SELECT * FROM discovery_connections WHERE id=%s'+(' FOR UPDATE' if lock else ''),(key(cid),)).fetchone()
 if not row:abort(404)
 return row

def input_values(body,old=None):
 if not isinstance(body,dict):raise Fault('KOD-CON-006')
 name=body.get('name');site=body.get('site')
 if not isinstance(name,str) or not 1<=len(name.strip())<=100 or site not in SITES:raise Fault('KOD-CON-006')
 if body.get('provider','datadog')!='datadog':raise Fault('KOD-CON-006')
 try:secrets=json.loads(cipher().decrypt(old['credentials'].encode())) if old else {}
 except (InvalidToken,ValueError):raise Fault('KOD-CON-007',status=503) from None
 for field in ['api_key','app_key']:
  value=body.get(field,'')
  if value:
   if not isinstance(value,str) or not 10<=len(value)<=200 or not value.isascii() or any(c.isspace() for c in value):raise Fault('KOD-CON-006')
   secrets[field]=value
 if set(secrets)!={'api_key','app_key'}:raise Fault('KOD-CON-006')
 return name.strip(),site,cipher().encrypt(json.dumps(secrets).encode()).decode()

def call_provider(site,path,keys=None,params=None,diagnostics=None):
 # Diagnostic values are explicitly allowlisted; never return credentials or raw headers.
 trace=diagnostics if diagnostics is not None else {}
 trace.update(method='GET',endpoint=path,host=SITES[site].split('://',1)[1],request_headers=['Accept']+(['DD-API-KEY','DD-APPLICATION-KEY'] if keys else []),parameters=params or {},checks={'https_verified':False},response_headers={})
 began=time.monotonic()
 # No redirects, proxies from process environment, arbitrary hosts or caller URLs.
 try:
  with requests.Session() as client:
   client.trust_env=False
   headers={'Accept':'application/json'}
   if keys:headers.update({'DD-API-KEY':keys['api_key'],'DD-APPLICATION-KEY':keys['app_key']})
   with client.get(SITES[site]+path,params=params,headers=headers,timeout=(3,6),allow_redirects=False,stream=True) as r:
    trace.update(http_status=r.status_code,headers_ms=round((time.monotonic()-began)*1000))
    trace['checks']['https_verified']=True
    content_type=r.headers.get('Content-Type','').split(';',1)[0].strip().lower()
    trace['response_headers']['content_type']=content_type if content_type in ['application/json','application/problem+json','text/html'] else 'No informado u otro'
    for header in ['X-RateLimit-Limit','X-RateLimit-Remaining','X-RateLimit-Period','X-RateLimit-Reset','Retry-After']:
     value=r.headers.get(header,'')
     if isinstance(value,str) and value.isdigit() and len(value)<=12:trace['response_headers'][header]=int(value)
    if keys is None and r.status_code in [200,401,403]:
     trace['checks']['http_reachable']=True
     trace['note']='Respuesta HTTPS recibida sin enviar credenciales; 401/403 puede ser esperado.'
     return {}
    if r.status_code==429:raise Fault('KOD-CON-004',status=429)
    if r.status_code in [401,403]:raise Fault('KOD-CON-002' if path.endswith('/validate') else 'KOD-CON-003')
    if r.status_code>=300:raise Fault('KOD-CON-001',status=502)
    if keys is None:return {} # HTTPS reachability only; no body needed.
    trace['checks']['json_content_type']=content_type in ['application/json','application/problem+json'] or content_type.endswith('+json')
    if not trace['checks']['json_content_type']:raise Fault('KOD-CON-005',status=502)
    content=bytearray();deadline=time.monotonic()+10
    for chunk in r.iter_content(16384):
     content.extend(chunk)
     if len(content)>1000000 or time.monotonic()>deadline:raise Fault('KOD-CON-005',status=502)
    trace['response_bytes']=len(content)
    result=json.loads(content)
    if not isinstance(result,dict):raise ValueError()
    trace['checks']['json_object']=True
    return result
 except Fault:raise
 except (requests.RequestException,ValueError):raise Fault('KOD-CON-001',status=502) from None

def perform(stage,row,diagnostics=None):
 try:keys=json.loads(cipher().decrypt(row['credentials'].encode()))
 except (InvalidToken,ValueError):raise Fault('KOD-CON-007',status=503) from None
 def probe(path,keys=None,params=None):return call_provider(row['site'],path,keys,params,diagnostics=diagnostics)
 if stage==0:probe('/api/v1/validate');return None
 if stage==1:
  if probe('/api/v1/validate',keys).get('valid') is not True:raise Fault('KOD-CON-002')
  return None
 if stage==2:
  if not isinstance(probe('/api/v1/hosts',keys,{'count':1,'start':0}).get('host_list'),list):raise Fault('KOD-CON-005',status=502)
  return None
 result=probe('/api/v1/hosts',keys,{'count':25,'start':0,'include_hosts_metadata':'true'})
 hosts=result.get('host_list')
 if not isinstance(hosts,list):raise Fault('KOD-CON-005',status=502)
 sample=[]
 for host in hosts[:25]:
  if not isinstance(host,dict):continue
  tags=host.get('tags_by_source',{});tags=[str(t)[:200] for values in tags.values() if isinstance(values,list) for t in values][:30] if isinstance(tags,dict) else []
  meta=host.get('meta') if isinstance(host.get('meta'),dict) else {}
  sample.append(dict(external_id=str(host.get('id',''))[:120],name=str(host.get('name',''))[:200],platform=str(meta.get('platform',''))[:100],tags=tags,source='Datadog'))
 total=result.get('total_matching',len(sample));total=total if type(total)==int and total>=0 else len(sample)
 return sample,total

@bp.get('')
def listing():
 with connection(subject()) as c:
  require_member(c);rows=c.execute('SELECT * FROM discovery_connections ORDER BY updated_at DESC LIMIT 100').fetchall()
 return jsonify(items=[serial(r) for r in rows])

@bp.post('')
def create():
 with connection(subject()) as c:
  require_member(c);name,site,secret=input_values(request.get_json());scope=c.execute('SELECT component_model_scope() AS scope').fetchone()['scope']
  c.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(scope,))
  if c.execute('SELECT count(*) AS n FROM discovery_connections').fetchone()['n']>=50:raise Fault('KOD-CON-006','Puedes configurar hasta 50 conexiones.',400)
  row=c.execute('INSERT INTO discovery_connections(scope_key,created_by,name,site,credentials) VALUES(%s,%s,%s,%s,%s) RETURNING *',(scope,subject(),name,site,secret)).fetchone()
 return jsonify(serial(row)),201

@bp.put('/<cid>')
def update(cid):
 body=request.get_json() or {}
 with connection(subject()) as c:
  require_member(c);old=owned(c,cid,True)
  if body.get('revision')!=old['revision']:raise Fault('KOD-CON-008',status=409)
  name,site,secret=input_values(body,old)
  row=c.execute("UPDATE discovery_connections SET name=%s,site=%s,credentials=%s,revision=revision+1,status='draft',run_id=NULL,stages='[]',sample='[]',sample_total=0,tested_at=NULL,updated_at=now() WHERE id=%s RETURNING *",(name,site,secret,key(cid))).fetchone()
 return jsonify(serial(row))

@bp.delete('/<cid>')
def delete(cid):
 with connection(subject()) as c:require_member(c);owned(c,cid);c.execute('DELETE FROM discovery_connections WHERE id=%s',(key(cid),))
 return '',204

@bp.post('/<cid>/test/start')
def start(cid):
 with connection(subject()) as c:
  require_member(c);row=owned(c,cid,True)
  if (datetime.now(timezone.utc)-row['updated_at']).total_seconds()<5 and row['run_id']:raise Fault('KOD-CON-004',status=429)
  row=c.execute("UPDATE discovery_connections SET run_id=%s,status='testing',stages='[]',sample='[]',sample_total=0,tested_at=NULL,updated_at=now(),revision=revision+1 WHERE id=%s RETURNING *",(uuid.uuid4(),key(cid))).fetchone()
 return jsonify(serial(row))

@bp.post('/<cid>/test/step')
def step(cid):
 body=request.get_json() or {};error=None
 with connection(subject()) as c:
  require_member(c);row=owned(c,cid,True)
  if row['status']!='testing' or str(row['run_id'])!=body.get('run_id') or (type(body.get('stage'))!=int or body['stage']!=len(row['stages'])):raise Fault('KOD-CON-008',status=409)
  stage=len(row['stages']);stages=row['stages'];began=time.monotonic();sample=row['sample'];total=row['sample_total'];trace={}
  try:
   result=perform(stage,row,trace)
   trace.setdefault('checks',{})['response_contract']=True
   if stage==3:sample,total=result
   stages.append(dict(label=STAGES[stage],status='complete',duration_ms=round((time.monotonic()-began)*1000),diagnostics=trace))
   status='verified' if stage==3 else 'testing'
  except Fault as exc:
   error=exc;status='failed';trace.setdefault('checks',{})['response_contract']=False;stages.append(dict(label=STAGES[stage],status='failed',code=exc.code,duration_ms=round((time.monotonic()-began)*1000),diagnostics=trace))
  row=c.execute('UPDATE discovery_connections SET stages=%s,sample=%s,sample_total=%s,status=%s,tested_at=now(),updated_at=now(),revision=revision+1 WHERE id=%s RETURNING *',(Jsonb(stages),Jsonb(sample),total,status,key(cid))).fetchone()
 if error:return jsonify(**serial(row),error=str(error),error_code=error.code),error.status
 return jsonify(serial(row))

@bp.post('/<cid>/confirm')
def confirm(cid):
 with connection(subject()) as c:
  require_member(c);row=owned(c,cid,True)
  if row['status']!='verified':raise Fault('KOD-CON-008',status=409)
  row=c.execute("UPDATE discovery_connections SET status='saved',updated_at=now(),revision=revision+1 WHERE id=%s RETURNING *",(key(cid),)).fetchone()
 return jsonify(serial(row))

@bp.post('/<cid>/test/cancel')
def cancel(cid):
 body=request.get_json() or {}
 with connection(subject()) as c:
  require_member(c);row=owned(c,cid,True)
  if str(row['run_id'])!=body.get('run_id'):raise Fault('KOD-CON-008',status=409)
  row=c.execute("UPDATE discovery_connections SET status='draft',run_id=NULL,updated_at=now(),revision=revision+1 WHERE id=%s RETURNING *",(key(cid),)).fetchone()
 return jsonify(serial(row))
