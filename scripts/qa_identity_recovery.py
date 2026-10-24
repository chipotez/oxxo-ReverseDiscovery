"""Disposable identity fixture only; no screenshots, secret output or human account edits."""
import json,urllib.parse,base64,hmac,hashlib,struct,time,stat
from pathlib import Path
from playwright.sync_api import sync_playwright
fixture=Path('.artifacts/mfa-sharing-qa.json');assert stat.S_IMODE(fixture.stat().st_mode)==0o600
cfg=json.loads(fixture.read_text());assert cfg['realm'].startswith('qa-koodaria-') and cfg['username'].startswith('qa-')
url='https://login.koodaria.com/realms/'+cfg['realm']+'/protocol/openid-connect/auth?'+urllib.parse.urlencode({'client_id':'qa-mfa-client','redirect_uri':'http://localhost:18179/__qa/mfa-complete','response_type':'code','scope':'openid','state':'qa-state'})
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page();page.goto(url);page.locator('#username').fill(cfg['username']);page.locator('#password').fill(cfg['password']);page.locator('#kc-login').click();page.wait_for_timeout(700)
 secret=page.locator('#kc-totp-secret-key').text_content().replace(' ','').strip() if page.locator('#kc-totp-secret-key').count() else base64.b32encode(page.locator('#totpSecret').input_value().encode()).decode()
 key=base64.b32decode(secret.upper()+'='*((8-len(secret)%8)%8));digest=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();offset=digest[-1]&15;code=str((struct.unpack('>I',digest[offset:offset+4])[0]&0x7fffffff)%1000000).zfill(6)
 page.locator('#totp').fill(code);page.locator('#userLabel').fill('Disposable QA');page.locator('#saveTOTPBtn').click();page.wait_for_timeout(700)
 checks=[]
 for w,h in [(1440,900),(1366,768),(1024,600),(768,1024),(390,844),(375,667),(320,568),(844,390)]:
  page.set_viewport_size({'width':w,'height':h});page.reload();page.locator('.recovery-enrollment').wait_for()
  steps=0
  while True:
   dims=page.evaluate('()=>[document.documentElement.scrollWidth,document.documentElement.scrollHeight]')

   if dims!=[w,h]:print('Overflow layout:',page.locator('.card-pf,.login-pf-header,.recovery-step-status,.pf-c-alert,.enrollment-navigation').evaluate_all('(xs)=>xs.map(e=>({id:e.id,cls:e.className,h:e.getBoundingClientRect().height,y:e.getBoundingClientRect().y}))'))
   assert dims==[w,h],('recovery',w,h,steps,dims)
   next=page.locator('.recovery-enrollment .enrollment-next')
   if not next.is_visible():break
   next.click();steps+=1;assert steps<12
  assert page.locator('#saveRecoveryAuthnCodesBtn').is_visible()
  checks.append({'width':w,'height':h,'pages_verified':steps+1,'no_overflow':True})
 codes=page.locator('input[name="generatedRecoveryAuthnCodes"]').input_value()
 page.locator('#kcRecoveryCodesConfirmationCheck').check();page.locator('#saveRecoveryAuthnCodesBtn').click();page.wait_for_timeout(500)
 assert '/__qa/mfa-complete' in page.url
 Path('docs/evidence/recovery-enrollment-report.json').write_text(json.dumps({'synthetic_identity_only':True,'no_secrets_or_screenshots_recorded':True,'states':checks},indent=2)+'\n')
 try:codes=json.loads(codes)
 except:codes=codes.split(',')
 def recover(code):
  context=b.new_context();target=context.new_page();target.goto(url);target.locator('#username').fill(cfg['username']);target.locator('#password').fill(cfg['password']);target.locator('#kc-login').click();target.get_by_text('Try Another Way',exact=True).click();target.get_by_role('button',name='Recovery Authentication Code').click();target.locator('#recoveryCodeInput').fill(code);target.locator('#kc-login').click();target.wait_for_timeout(400);passed='/__qa/mfa-complete' in target.url;context.close();return passed
 assert recover(codes[0]);assert not recover(codes[0])
 print('Eight recovery viewports, enrollment, native confirmation, second factor and one-time-code reuse rejection PASS');b.close()
