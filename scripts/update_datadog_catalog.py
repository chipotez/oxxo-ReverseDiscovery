"""Build the global catalog from pinned, public Datadog OpenAPI schemas.
Run with the QA Python environment and PyYAML 6.0.2. Never reads credentials.
"""
import argparse,hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
import yaml
REPO='DataDog/datadog-api-client-python'
ALIASES={'/api/v1/hosts':'hosts','/api/v1/monitor':'monitors','/api/v1/dashboard':'dashboards','/api/v2/logs/events':'logs','/api/v2/events':'events','/api/v2/users':'users','/api/v2/services/definitions':'services','/api/v2/spans/events':'apm'}
def resolve(value,spec):
 if isinstance(value,dict) and '$ref' in value:
  target=spec
  for key in value['$ref'].split('/')[1:]:target=target[key]
  return target
 return value

def build(revision,cache):
 operations=[];sources=[]
 for version in ['v1','v2']:
  url=f'https://raw.githubusercontent.com/{REPO}/{revision}/.generator/schemas/{version}/openapi.yaml'
  path=cache/(version+'.yaml')
  cached_revision=(cache/'revision').read_text().strip() if (cache/'revision').exists() else None
  raw=path.read_bytes() if path.exists() and cached_revision==revision else urllib.request.urlopen(url,timeout=45).read()
  spec=yaml.safe_load(raw);sources.append(dict(version=version,url=url,sha256=hashlib.sha256(raw).hexdigest()))
  for path,item in spec['paths'].items():
   for method,op in item.items():
    if method not in ['get','post','put','patch','delete','head','options']:continue
    parameters=[]
    for p in item.get('parameters',[])+op.get('parameters',[]):
     p=resolve(p,spec)
     if p.get('in') not in ['path','query']:continue
     schema=resolve(p.get('schema',{}),spec);entry={k:p[k] for k in ['name','in','required','style','explode'] if k in p}
     entry.update({k:schema[k] for k in ['type','format','default','enum','minimum','maximum'] if k in schema});parameters.append(entry)
    security=op.get('security',spec.get('security',[]));supports_keys=not security or any('apiKeyAuth' in s for s in security)
    restricted=bool(re.search(r'api[_-]?keys|application[_-]?keys|credentials|tokens|/variables|webhooks',path,re.I)) or any(re.search(r'key management|authentication|integration|oauth',t,re.I) for t in op.get('tags',[]))
    servers=op.get('servers',item.get('servers',[]));special=bool(servers) or not path.startswith('/api/')
    content={mime for status,r in op.get('responses',{}).items() if str(status).startswith('2') for mime in resolve(r,spec).get('content',{})};json_response=bool(content & {'application/json','application/vnd.api+json'})
    preview=bool(op.get('x-unstable')) or '/unstable/' in path;required=[p for p in parameters if p.get('required') and p.get('default') is None]
    policy='write' if method!='get' else 'restricted' if restricted or not supports_keys else 'unsupported' if special or not json_response else 'preview' if preview else 'parameters' if required else 'automatic'
    opid=op.get('operationId',method+'-'+path)
    uid=ALIASES[path] if method=='get' and path in ALIASES else version+'-'+re.sub('[^a-z0-9_-]','-',opid.lower())
    scopes=sorted({scope for auth in security for name,values in auth.items() if name=='AuthZ' for scope in values})
    operations.append(dict(id=uid,operation_id=opid,version=version,method=method.upper(),path=path,label=op.get('summary') or opid,group=(op.get('tags') or ['Other'])[0],tags=op.get('tags',[]),parameters=parameters,scopes=scopes,permission=op.get('x-permission'),preview=preview,deprecated=bool(op.get('deprecated')),policy=policy,docs='https://docs.datadoghq.com/api/latest/'+re.sub('[^a-z0-9]+','-',(op.get('tags') or ['Other'])[0].lower()).strip('-')+'/#'+re.sub('[^a-z0-9]+','-',(op.get('summary') or opid).lower()).strip('-')))
 assert len({o['id'] for o in operations})==len(operations)
 operations.sort(key=lambda o:(o['group'].lower(),o['path'],o['method']))
 return dict(provider='datadog',revision=revision,generated_at=datetime.now(timezone.utc).isoformat(),sources=sources,stats=dict(operations=len(operations),routes=len({o['path'] for o in operations}),groups=len({o['group'] for o in operations}),automatic=sum(o['policy']=='automatic' for o in operations),parameterized=sum(o['policy']=='parameters' for o in operations)),operations=operations)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--revision',required=True);p.add_argument('--cache',type=Path,default=Path('.artifacts/datadog-spec'));a=p.parse_args()
 assert re.fullmatch('[a-f0-9]{40}',a.revision)
 result=build(a.revision,a.cache);Path('app/datadog-api-catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result['stats']))
