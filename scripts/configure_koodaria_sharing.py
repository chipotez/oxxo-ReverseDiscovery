"""One-time Koodaria invitation setup. Private service credentials; no human password/MFA changes.
Defaults to validation; --apply requires a temporary administrative service account.
"""
import argparse,json,os,stat,secrets,subprocess
from urllib.parse import quote
from pathlib import Path
from keycloak_admin import admin_api

BASE='https://login.koodaria.com'
ROLES=['manage-users','query-users','view-users','manage-organizations','query-organizations']

def read_env(path):
    if stat.S_IMODE(path.stat().st_mode)&0o077:raise ValueError('SMTP file must have mode 600.')
    result={}
    for line in path.read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1);v=v.strip()
            if len(v)>1 and v[0]==v[-1] and v[0] in ['"',"'"]:v=v[1:-1]
            result[k.strip()]=v
    return result

def configure(credentials_file,smtp_file,output_file,apply=False):
    cfg=read_env(smtp_file)
    required=['SMTP_HOST','SMTP_PORT','SMTP_FROM','SMTP_USERNAME','SMTP_PASSWORD']
    if not all(cfg.get(k) for k in required):raise ValueError('SMTP settings are incomplete.')
    if not apply:
        print('Configuration validated; no identity settings changed.');return
    api=admin_api(credentials_file,BASE);prefix='realms/koodaria/'
    realm=api('realms/koodaria')
    original=output_file.with_suffix('.realm-before.json');original.write_text(json.dumps(realm));original.chmod(0o600)
    verified=cfg.get('SMTP_VERIFIED')=='true'
    smtp={'host':cfg['SMTP_HOST'],'port':cfg['SMTP_PORT'],'from':cfg['SMTP_FROM'],'fromDisplayName':'Koodaria','auth':'true','ssl':cfg.get('SMTP_SSL','true'),'starttls':'false' if cfg.get('SMTP_SSL','true')=='true' else 'true','user':cfg['SMTP_USERNAME'],'password':cfg['SMTP_PASSWORD']}
    # Password recovery is enabled only after successful TLS authentication.
    clients=api(prefix+'clients?clientId=koodaria-invitations')
    if not clients:
        secret=secrets.token_hex(32)
        api(prefix+'clients','POST',{'clientId':'koodaria-invitations','name':'Koodaria invitations','enabled':True,'publicClient':False,'protocol':'openid-connect','serviceAccountsEnabled':True,'standardFlowEnabled':False,'directAccessGrantsEnabled':False,'secret':secret})
        clients=api(prefix+'clients?clientId=koodaria-invitations')
    client=clients[0];secret=api(prefix+'clients/'+client['id']+'/client-secret')['value']
    service=api(prefix+'clients/'+client['id']+'/service-account-user')
    management=api(prefix+'clients?clientId=realm-management')[0]
    available={r['name']:r for r in api(prefix+'clients/'+management['id']+'/roles')}
    if not all(name in available for name in ROLES):raise ValueError('Expected scoped roles unavailable; refusing realm-admin fallback.')
    api(prefix+'users/'+service['id']+'/role-mappings/clients/'+management['id'],'POST',[available[name] for name in ROLES])
    web=api(prefix+'clients?clientId=koodaria-web')[0]
    web['redirectUris']=list(dict.fromkeys(web['redirectUris']+['https://koodaria.com/auth/login']))
    api(prefix+'clients/'+web['id'],'PUT',web)
    actions=api(prefix+'authentication/required-actions')
    priorities={'VERIFY_EMAIL':10,'UPDATE_PROFILE':20,'UPDATE_PASSWORD':30,'CONFIGURE_TOTP':40,'CONFIGURE_RECOVERY_AUTHN_CODES':50}
    for action in actions:
        if action['alias'] in priorities:
            action['enabled']=True;action['priority']=priorities[action['alias']]
            # Keep existing MFA enrollment required; recovery codes are requested for invited users.
            if action['alias']=='CONFIGURE_RECOVERY_AUTHN_CODES':action['defaultAction']=False
            api(prefix+'authentication/required-actions/'+action['alias'],'PUT',action)
    if not any(a['alias']=='CONFIGURE_RECOVERY_AUTHN_CODES' for a in actions):raise ValueError('Recovery code action unavailable.')
    browser_path=prefix+'authentication/flows/'+quote(realm['browserFlow'],safe='')+'/executions'
    executions=api(browser_path)
    if not any('Conditional 2FA' in e.get('displayName','') and e['requirement']=='REQUIRED' for e in executions):raise ValueError('Required second-factor parent flow missing; refusing changes.')
    # OTP remains REQUIRED inside an ALTERNATIVE subflow. This permits first-login
    # enrollment while allowing a previously enrolled recovery code as another factor.
    # Making OTP directly ALTERNATIVE rejects users who have not enrolled yet.
    parent=next(e for e in executions if 'Conditional 2FA' in e.get('displayName',''))
    alias='koodaria OTP enrollment'
    if not any(e['displayName']==alias for e in executions):
        api(prefix+'authentication/flows/'+quote(parent['displayName'],safe='')+'/executions/flow','POST',{'alias':alias,'type':'basic-flow','provider':'basic-flow','description':'Required OTP with first-login enrollment'})
        api(prefix+'authentication/flows/'+quote(alias,safe='')+'/executions/execution','POST',{'provider':'auth-otp-form'})
    for execution in api(browser_path):
        if execution['displayName']==alias:execution['requirement']='ALTERNATIVE'
        elif execution.get('providerId')=='auth-otp-form':execution['requirement']='REQUIRED' if execution['level']==parent['level']+2 else 'DISABLED'
        elif execution.get('providerId')=='auth-recovery-authn-code-form':execution['requirement']='ALTERNATIVE'
        else:continue
        api(browser_path,'PUT',execution)
    # Email resets the password only. Lost MFA uses a recovery code or verified admin assistance.
    reset_path=prefix+'authentication/flows/'+quote(realm.get('resetCredentialsFlow') or 'reset credentials',safe='')+'/executions'
    for execution in api(reset_path):
        if execution.get('providerId')=='reset-otp' or 'Conditional OTP' in execution.get('displayName',''):
            execution['requirement']='DISABLED';api(reset_path,'PUT',execution)
    if verified:api('realms/koodaria','PUT',{'smtpServer':smtp,'resetPasswordAllowed':True,'emailTheme':'koodaria'})
    cfg.update(INVITE_CLIENT_ID='koodaria-invitations',INVITE_CLIENT_SECRET=secret,INVITE_RECOVERY_CODES='true')
    output_file.write_text('\n'.join(k+'='+v for k,v in cfg.items())+'\n');output_file.chmod(0o600)
    print('Koodaria scoped invitation service configured. No human MFA credential removed.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--credentials-file',type=Path,required=True);p.add_argument('--smtp-file',type=Path,required=True);p.add_argument('--output-file',type=Path,required=True);p.add_argument('--apply',action='store_true');args=p.parse_args()
    os.umask(0o077)
    try:configure(args.credentials_file,args.smtp_file,args.output_file,args.apply)
    except Exception as e:raise SystemExit('Invitation configuration failed ('+type(e).__name__+'); sensitive response omitted.') from None
