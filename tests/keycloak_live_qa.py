"""Live authentication QA. Creates and deletes one disposable account.
Requires an authorized administrative service-account file; never writes test secrets.
"""
import argparse,json,sys,urllib.parse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from keycloak_admin import admin_api
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--credentials-file',required=True,type=Path)
parser.add_argument('--server',default='https://login.koodaria.com')
parser.add_argument('--resolve-ip',help='Optional DNS propagation override; TLS verification stays enabled')
args=parser.parse_args()
api=admin_api(args.credentials_file,args.server)
import secrets,time,hmac,hashlib,struct
from playwright.sync_api import sync_playwright
username='qa-koodaria-'+secrets.token_hex(4);password=secrets.token_urlsafe(24)
api('realms/koodaria/users','POST',{'username':username,'email':username+'@example.invalid','emailVerified':True,'firstName':'QA','lastName':'Temporal','enabled':True,'requiredActions':[],'credentials':[{'type':'password','value':password,'temporary':False}]})
user=api('realms/koodaria/users?email='+username+'@example.invalid&exact=true')[0]
report={}
def totp(secret):
 key=secret.encode('utf-8');d=hmac.new(key,struct.pack('>Q',int(time.time())//30),hashlib.sha1).digest();o=d[-1]&15;return str((struct.unpack('>I',d[o:o+4])[0]&0x7fffffff)%1000000).zfill(6)
try:
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True,args=['--host-resolver-rules=MAP login.koodaria.com '+args.resolve_ip] if args.resolve_ip else [])
  context=b.new_context(locale='es-ES',viewport={'width':1440,'height':900});page=context.new_page();seen=set();page.on('request',lambda req:seen.add(urllib.parse.urlparse(req.url).hostname))
  page.goto('https://koodaria.com/login/');page.locator('#username').wait_for(timeout=30000)
  page.screenshot(path='.artifacts/keycloak-login-es.png')
  page.locator('#username').fill(user['email']);page.locator('#password').fill('incorrect-password-qa');page.locator('#kc-login').click();page.locator('#input-error').wait_for();assert page.locator('#totpSecret').count()==0;report['invalid_password_rejected_before_enrollment']=True
  page.locator('#password').fill(password);page.locator('#kc-login').click();page.locator('#totpSecret').wait_for(state='attached');secret=page.locator('#totpSecret').input_value();assert page.locator('#kc-totp-secret-qr-code').count()==1;report['first_login_requires_qr_enrollment']=True
  page.locator('#totp').fill('000000' if totp(secret)!='000000' else '999999');page.locator('input[type=submit]').click();assert page.locator('#totpSecret').count()==1;report['invalid_enrollment_code_rejected']=True
  page.locator('#totp').fill(totp(secret));page.locator('#userLabel').fill('Dispositivo QA');page.locator('input[type=submit]').click();page.wait_for_url('**/account/**',timeout=30000);page.wait_for_timeout(2500)
  assert '/login-actions/' not in page.url;report['enrollment_completes_account_login']=True
  # A fresh browser context must ask for OTP, rather than enrolling again.
  context.close();context=b.new_context(locale='es-ES',viewport={'width':390,'height':844});page=context.new_page();page.on('request',lambda req:seen.add(urllib.parse.urlparse(req.url).hostname));page.goto('https://koodaria.com/login/');page.locator('#username').wait_for();page.locator('#username').fill(user['email']);page.locator('#password').fill(password);page.locator('#kc-login').click();page.locator('#otp').wait_for();assert page.locator('#totpSecret').count()==0;report['subsequent_login_requires_otp']=True
  page.locator('#otp').fill('000000' if totp(secret)!='000000' else '999999');page.locator('#kc-login').click();assert page.locator('#otp').count()==1;report['invalid_otp_rejected']=True
  # Avoid reusing the enrollment code in the same TOTP period.
  remaining=30-int(time.time())%30
  page.wait_for_timeout((remaining+1)*1000)
  page.locator('#otp').fill(totp(secret));page.locator('#kc-login').click();page.wait_for_url('**/account/**',timeout=30000);page.wait_for_timeout(1500);assert '/login-actions/' not in page.url;report['subsequent_valid_otp_succeeds']=True
  report['customer_hosts']=sorted(x for x in seen if x);assert all(x in ['koodaria.com','login.koodaria.com'] for x in seen if x),seen
  report['customer_flow_stays_on_koodaria_domains']=True
  report['mobile_no_horizontal_overflow']=page.evaluate('document.documentElement.scrollWidth<=innerWidth')
  context.close();b.close()
finally:
 api('realms/koodaria/users/'+user['id'],'DELETE');report['temporary_test_user_deleted']=True
 Path('docs/evidence/keycloak-2fa-report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
