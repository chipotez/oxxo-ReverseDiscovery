"""Organization-scoped, read-only discovery. Provider endpoints never come from clients."""
import base64,json,os,time,uuid,re
from pathlib import Path
from urllib.parse import quote
from datetime import datetime,timezone,timedelta
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

def call_provider(site,path,keys=None,params=None,diagnostics=None,accept_list=False):
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
    if not isinstance(result,(dict,list) if accept_list else dict):raise Fault('KOD-CON-005',status=502)
    trace['checks']['json_object']=isinstance(result,dict)
    if accept_list:trace['checks']['json_collection']=isinstance(result,(dict,list))
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
  c.execute('DELETE FROM discovery_capabilities WHERE connection_id=%s',(key(cid),))
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

# A curated set of concrete read endpoints, not an assertion of all Datadog APIs.
FAMILIES={
 'hosts':dict(label='Hosts',path='/api/v1/hosts',collection='host_list',mode='offset',note='Hosts reportados por Datadog en su ventana reciente (2 horas por defecto). No equivale a un inventario histórico completo.'),
 'monitors':dict(label='Monitores y alertas',path='/api/v1/monitor',collection=None,mode='page',note='Configuración de monitores, estados y mensajes de notificación devueltos por esta API.'),
 'dashboards':dict(label='Dashboards',path='/api/v1/dashboard',collection='dashboards',mode='offset',note='Listado de dashboards. Esta consulta no carga los widgets de cada dashboard.'),
 'logs':dict(label='Logs',path='/api/v2/logs/events',collection='data',mode='cursor',note='Eventos de logs de los últimos 15 minutos. Puede contener datos sensibles de tu organización.'),
 'events':dict(label='Eventos',path='/api/v2/events',collection='data',mode='cursor',note='Eventos de los últimos 15 minutos. No representa todos los canales de notificación.'),
 'users':dict(label='Personas',path='/api/v2/users',collection='data',mode='number',note='Usuarios visibles para esta cuenta. Solo lectura; no crea ni invita personas.'),
 'services':dict(label='Catálogo de servicios',path='/api/v2/services/definitions',collection='data',mode='number',note='Definiciones del catálogo de servicios; no implica acceso a todas las trazas APM.'),
 'apm':dict(label='APM · trazas',path='/api/v2/spans/events',collection='data',mode='cursor',note='Spans indexados de los últimos 15 minutos. Esta consulta no incluye todas las métricas o configuraciones APM.')}

CATALOG=json.loads(Path(__file__).with_name('datadog-api-catalog.json').read_text())
OPERATIONS={o['id']:o for o in CATALOG['operations']}
# Keep the established adapters and identifiers; every other entry is global metadata.
for ident,op in OPERATIONS.items():
 base=FAMILIES.get(ident,dict(collection='auto',mode='generic',note=op['label']))
 FAMILIES[ident]=dict(base,**{k:op[k] for k in ['method','group','parameters','scopes','policy','docs','operation_id','version','preview','deprecated']},path=op['path'],label=base.get('label',op['label']))

def operation_public(ident,check=None):
 config=family_config(ident);check=check or {}
 return dict(id=ident,label=config['label'],endpoint=config['path'],note=config['note'],**{k:config[k] for k in ['method','group','parameters','scopes','policy','docs','preview','deprecated']},status=check.get('status','unchecked'),diagnostics=check.get('diagnostics',{}),checked_at=check['checked_at'].isoformat() if check.get('checked_at') else None)

def catalog_request(family,values=None,page=0,query='',cursor='',limit=1):
 config=family_config(family)
 if config['policy'] not in ['automatic','parameters'] or config['method']!='GET':raise Fault('KOD-CON-006','Esta operación está catalogada, pero no se ejecuta desde el explorador de lectura.')
 values=values or {}
 if not isinstance(values,dict) or len(values)>30:raise Fault('KOD-CON-006')
 allowed={p['name']:p for p in config['parameters']}
 if set(values)-set(allowed):raise Fault('KOD-CON-006','Parámetro no definido por Datadog.')
 path=config['path'];params=family_params(family,page,query,cursor,limit)
 for name,p in allowed.items():
  value=values.get(name,p.get('default'))
  if value is None or value=='':
   if p.get('required'):raise Fault('KOD-CON-006','Falta el parámetro requerido: '+name)
   continue
  if p.get('type')=='array' and p['in']=='query':
   value=value.split(',') if isinstance(value,str) else value
   if not isinstance(value,list) or len(value)>25 or any(not isinstance(v,(str,int,float)) or len(str(v))>200 for v in value):raise Fault('KOD-CON-006','Lista de parámetros no válida.')
   if p.get('explode') is False:value=','.join(map(str,value))
  elif isinstance(value,(dict,list)):
   if name not in values and not p.get('required'):continue
   raise Fault('KOD-CON-006','Usa un valor simple para este parámetro.')
  if len(str(value))>500:raise Fault('KOD-CON-006','Valor de parámetro no admitido.')
  if p.get('type') in ['integer','number']:
   try:value=int(value) if p['type']=='integer' else float(value)
   except (ValueError,TypeError):raise Fault('KOD-CON-006','Valor numérico requerido: '+name) from None
   if value<float(p.get('minimum',float('-inf'))) or value>float(p.get('maximum',float('inf'))):raise Fault('KOD-CON-006','Valor fuera de rango: '+name)
  if p.get('enum') and value not in p['enum']:raise Fault('KOD-CON-006','Valor no permitido: '+name)
  if p['in']=='path':
   if not re.fullmatch(r'[A-Za-z0-9_.:@-]{1,200}',str(value)) or str(value) in ['.','..']:raise Fault('KOD-CON-006','Identificador no válido: '+name)
   path=path.replace('{'+name+'}',quote(str(value),safe=''))
  else:params.setdefault(name,value)
 if '{' in path:raise Fault('KOD-CON-006','Esta consulta requiere un identificador.')
 if config['mode']=='generic':
  for field in ['page[size]','page[limit]','page_size','limit','count','per_page']:
   if field in allowed:
    param=allowed[field];params[field]=max(int(param.get('minimum',1)),min(limit,int(param.get('maximum',limit))))
  for field in ['start','offset','page[offset]']:
   if field in allowed:params[field]=page*limit
  for field in ['page[number]','page']:
   if field in allowed:params[field]=page
  if cursor:
   for field in ['page[cursor]','cursor','next_record_id']:
    if field in allowed:params[field]=cursor
 return path,params

def provider_keys(row):
 try:return json.loads(cipher().decrypt(row['credentials'].encode()))
 except (InvalidToken,ValueError):raise Fault('KOD-CON-007',status=503) from None

def require_verified(row):
 if row['status'] not in ['verified','saved'] and not (len(row['stages'])>1 and row['stages'][1].get('status')=='complete'):raise Fault('KOD-CON-008','Comprueba primero la conexión.',409)

def family_config(family):
 if family not in FAMILIES:raise Fault('KOD-CON-006','Familia de API no admitida.',400)
 return FAMILIES[family]

def family_params(family,page=0,query='',cursor='',limit=25):
 if family=='hosts':return dict(start=page*limit,count=limit,include_hosts_metadata='true',include_muted_hosts_data='true',**({'filter':query} if query else {}))
 if family=='dashboards':return dict(start=page*limit,count=limit)
 if family=='monitors':return dict(page=page,page_size=limit,**({'name':query} if query else {}))
 if family in ['users','services']:return {'page[size]':limit,'page[number]':page,**({'filter':query} if query and family=='users' else {})}
 if family in ['logs','events','apm']:return {'filter[from]':(datetime.now(timezone.utc)-timedelta(minutes=15)).isoformat(),'filter[to]':datetime.now(timezone.utc).isoformat(),'page[limit]':limit,**({'page[cursor]':cursor} if cursor else {}),**({'filter[query]':query} if query else {})}
 return {}

def family_items(data,config):
 items=data if config['collection'] is None else data.get(config['collection']) if isinstance(data,dict) else None
 if config['collection']=='auto':
  if isinstance(data,list):return data
  if not isinstance(data,dict) or data.get('errors'):raise Fault('KOD-CON-005',status=502)
  for name in ['data','items','results','records','accounts','roles','tests','groups','metrics','tags']:
   if isinstance(data.get(name),list):return data[name]
  arrays=[v for v in data.values() if isinstance(v,list)]
  return arrays[0] if len(arrays)==1 else [data]
 if not isinstance(items,list):raise Fault('KOD-CON-005',status=502)
 return items

@bp.get('/<cid>/capabilities')
def capabilities(cid):
 with connection(subject()) as c:
  require_member(c);row=owned(c,cid);require_verified(row)
  checks={r['family']:r for r in c.execute('SELECT family,status,diagnostics,checked_at FROM discovery_capabilities WHERE connection_id=%s',(key(cid),)).fetchall() if r['diagnostics'].get('catalog_revision')==CATALOG['revision']}
 return jsonify(catalog={k:CATALOG[k] for k in ['revision','generated_at','sources','stats']},items=[operation_public(f,checks.get(f)) for f in FAMILIES])

@bp.post('/<cid>/capabilities/<family>/probe')
def probe_family(cid,family):
 config=family_config(family);body=request.get_json(silent=True)
 if not isinstance(body,dict):raise Fault('KOD-CON-006')
 values=body.get('parameters',{});path,params=catalog_request(family,values);trace={};began=time.monotonic();status='unknown';code=None
 with connection(subject()) as c:
  require_member(c);row=owned(c,cid,True);require_verified(row)
  previous=c.execute('SELECT checked_at FROM discovery_capabilities WHERE connection_id=%s AND family=%s',(key(cid),family)).fetchone()
  if previous and (datetime.now(timezone.utc)-previous['checked_at']).total_seconds()<3:raise Fault('KOD-CON-004',status=429)
  try:
   data=call_provider(row['site'],path,provider_keys(row),params,diagnostics=trace,accept_list=config['collection'] in [None,'auto'])
   family_items(data,config);status='available'
  except Fault as exc:
   code=exc.code;http=trace.get('http_status');status='denied' if http in [401,403] else 'unavailable' if http in [404,405,410] else 'unknown'
  trace.update(duration_ms=round((time.monotonic()-began)*1000),error_code=code,catalog_revision=CATALOG['revision'],catalog_parameters=values)
  c.execute('INSERT INTO discovery_capabilities(connection_id,scope_key,family,status,diagnostics) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(connection_id,family) DO UPDATE SET status=EXCLUDED.status,diagnostics=EXCLUDED.diagnostics,checked_at=now()',(key(cid),row['scope_key'],family,status,Jsonb(trace)))
 return jsonify(operation_public(family,dict(status=status,diagnostics=trace,checked_at=datetime.now(timezone.utc))))

@bp.get('/<cid>/resources/<family>')
def family_resources(cid,family):
 config=family_config(family)
 try:values=json.loads(request.args.get('parameters','{}'))
 except ValueError:raise Fault('KOD-CON-006') from None
 try:page=int(request.args.get('page','0'));limit=int(request.args.get('limit','5'))
 except ValueError:raise Fault('KOD-CON-006') from None
 query=request.args.get('query','').strip();cursor=request.args.get('cursor','')
 if not 1<=limit<=25 or page<0 or page>100000 or len(query)>250 or len(cursor)>4096:raise Fault('KOD-CON-006')
 path,params=catalog_request(family,values,page,query,cursor,limit)
 # Local-only filters cannot be presented as searches over all remote records.
 if query and family not in ['hosts','monitors','users','logs','events','apm']:raise Fault('KOD-CON-006','Esta API no admite búsqueda en esta vista.')
 with connection(subject()) as c:
  require_member(c);row=owned(c,cid);require_verified(row)
  checked=c.execute('SELECT status,diagnostics FROM discovery_capabilities WHERE connection_id=%s AND family=%s',(key(cid),family)).fetchone()
  if not checked or checked['status']!='available' or checked['diagnostics'].get('catalog_revision')!=CATALOG['revision']:raise Fault('KOD-CON-003','Identifica primero el acceso a esta API.',403)
  trace={};data=call_provider(row['site'],path,provider_keys(row),params,diagnostics=trace,accept_list=config['collection'] in [None,'auto'])
  items=family_items(data,config);total=data.get('total_matching') if family=='hosts' else None
  after=data.get('meta',{}).get('page',{}).get('after') if config['mode']=='cursor' else None
  if not isinstance(after,str):after=None
  if config['mode']=='local' or config['mode']=='generic' and not any(k in params for k in ['page[size]','page[limit]','page_size','limit','count','per_page','start','offset','page[offset]','page[number]','page']):total=len(items);items=items[page*limit:(page+1)*limit]
  more=bool(after) if config['mode']=='cursor' else (page+1)*limit<total if type(total)==int else len(items)==limit
 return jsonify(items=items,page=page,total=total if type(total)==int else None,has_more=more,next_cursor=after,endpoint=config['path'],note=config['note'],queried_at=datetime.now(timezone.utc).isoformat())
