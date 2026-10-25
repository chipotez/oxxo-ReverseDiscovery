"""Stable error contract; correlation logs intentionally exclude payloads and identity."""
import json,logging,uuid
from pathlib import Path
from flask import request
path=Path(__file__).with_name('error-catalog.json')
if not path.exists():path=Path(__file__).parent/'frontend/src/error-catalog.json'
CATALOG=json.loads(path.read_text())
class Fault(ValueError):
    def __init__(self,code,message=None,status=400):
        self.code=code;self.status=status;super().__init__(message or CATALOG[code]['message'])
def decorate_error(response):
    if response.status_code<400 or not (request.path.startswith('/bienvenida/api/') or request.path=='/auth/session'):return response
    body=response.get_json(silent=True)
    if not isinstance(body,dict):body={}
    code=body.get('error_code')
    if code not in CATALOG:
        status=response.status_code
        code='KOD-AUTH-001' if status==401 else 'KOD-AUTH-002' if body.get('code')=='csrf_invalid' else 'KOD-ACCESS-001' if status==403 else 'KOD-RATE-001' if status==429 else 'KOD-ITEM-001' if status==404 else 'KOD-SYS-001' if status>=500 else 'KOD-PDF-001' if '/pdf' in request.path else 'KOD-FOLDER-001' if '/folders' in request.path or '/move' in request.path else 'KOD-SHARE-001' if '/shares' in request.path else 'KOD-CAT-003' if status==409 and '/catalog/' in request.path else 'KOD-STD-002' if status==409 and '/standards' in request.path else 'KOD-DIA-002' if status==409 else 'KOD-STD-001' if '/standards' in request.path else 'KOD-DIA-001' if '/diagrams' in request.path else 'KOD-REQ-001'
    reference=str(uuid.uuid4());entry=CATALOG[code]
    body.update(error=body.get('error') or entry['message'],error_code=code,reference=reference,action=entry['action'])
    logging.getLogger('koodaria.errors').warning(json.dumps(dict(reference=reference,code=code,status=response.status_code,operation=request.method,route=request.url_rule.rule if request.url_rule else 'unmatched')))
    response.set_data(json.dumps(body,ensure_ascii=False));response.content_type='application/json';response.headers['X-Error-Reference']=reference
    return response
