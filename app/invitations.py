"""Optional Keycloak/SMTP integration. Never accepts credentials from browser requests."""
import os
import re
import smtplib
import ssl
from email.message import EmailMessage
import requests

BASE='https://login.koodaria.com'
REALM='koodaria'
class InvitationUnavailable(Exception): pass

def normalize_email(value):
    if not isinstance(value,str) or len(value)>254 or not re.fullmatch(r'[^\s@<>(),:;"\\\x00-\x1f]+@[^\s@<>(),:;"\\\x00-\x1f]+\.[^\s@<>(),:;"\\\x00-\x1f]+',value):
        raise ValueError('Introduce un correo electrónico válido.')
    return value.strip().lower()

def mail_ready():return os.environ.get('SMTP_VERIFIED')=='true' and bool(os.environ.get('SMTP_HOST') and os.environ.get('SMTP_FROM') and os.environ.get('SMTP_USERNAME') and os.environ.get('SMTP_PASSWORD'))
def provision_ready():return mail_ready() and bool(os.environ.get('INVITE_CLIENT_ID') and os.environ.get('INVITE_CLIENT_SECRET'))

def notify_existing(email,name):
    if not mail_ready():return False
    message=EmailMessage();message['Subject']='Te compartieron un diagrama en Koodaria';message['From']=os.environ['SMTP_FROM'];message['To']=email
    message.set_content('Te compartieron el diagrama «'+name+'».\n\nEntra con tu cuenta en https://koodaria.com/auth/login y abre Compartidos conmigo.\n\nKoodaria')
    try:
        port=int(os.environ.get('SMTP_PORT','587'))
        if os.environ.get('SMTP_SSL')=='true':server=smtplib.SMTP_SSL(os.environ['SMTP_HOST'],port,timeout=8,context=ssl.create_default_context())
        else:
            server=smtplib.SMTP(os.environ['SMTP_HOST'],port,timeout=8);server.ehlo();server.starttls(context=ssl.create_default_context());server.ehlo()
        with server:
            server.login(os.environ['SMTP_USERNAME'],os.environ['SMTP_PASSWORD']);server.send_message(message)
        return True
    except Exception:return False

class IdentityProvider:
    def __init__(self):
        if not provision_ready():raise InvitationUnavailable('Falta configurar el correo y el servicio de invitaciones. No se creó ninguna cuenta.')
        try:
            response=requests.post(BASE+'/realms/koodaria/protocol/openid-connect/token',data={'grant_type':'client_credentials','client_id':os.environ['INVITE_CLIENT_ID'],'client_secret':os.environ['INVITE_CLIENT_SECRET']},timeout=8)
            response.raise_for_status();self.token=response.json()['access_token']
        except Exception:raise InvitationUnavailable('El servicio de invitaciones no está disponible.') from None
    def call(self,path,method='GET',body=None,allow404=False,params=None):
        try:
            r=requests.request(method,BASE+'/admin/realms/'+REALM+'/'+path,headers={'Authorization':'Bearer '+self.token},json=body,params=params,timeout=8)
            if allow404 and r.status_code==404:return None
            if r.status_code>=400:raise InvitationUnavailable('No se pudo completar la invitación en el servicio de identidad.')
            return r.json() if r.content else None
        except requests.RequestException:raise InvitationUnavailable('El servicio de identidad no respondió. Vuelve a intentarlo.') from None
    def find(self,email):
        users=self.call('users',params={'email':email,'exact':'true','max':2})
        exact=[u for u in users if u.get('email','').lower()==email]
        if len(exact)>1:raise InvitationUnavailable('El correo requiere revisión por el administrador.')
        return exact[0] if exact else None
    def organization_for(self,owner):
        # Explicit membership only. Never infer customer access from an email domain.
        matches=[]
        for first in range(0,1000,100):
            orgs=self.call('organizations',params={'first':first,'max':100})
            for org in orgs:
                if self.call('organizations/'+org['id']+'/members/'+owner,allow404=True):matches.append(org['id'])
            if len(orgs)<100:break
        if len(matches)!=1:raise InvitationUnavailable('El propietario debe tener una organización definida antes de invitar nuevas cuentas.')
        return matches[0]
    def provision(self,email,owner):
        existing=self.find(email)
        if existing:
            if not existing.get('enabled'):raise InvitationUnavailable('La cuenta requiere revisión por el administrador.')
            remaining=existing.get('requiredActions',[])
            # Do not depend on unmanaged attributes: Keycloak can discard them.
            # Only a passwordless account awaiting its initial password is onboarding.
            onboarding='UPDATE_PASSWORD' in remaining and not any(c.get('type')=='password' for c in self.call('users/'+existing['id']+'/credentials'))
            if onboarding:self.onboarding_actions=[a for a in remaining if a in ['VERIFY_EMAIL','UPDATE_PROFILE','UPDATE_PASSWORD','CONFIGURE_TOTP','CONFIGURE_RECOVERY_AUTHN_CODES']]
            elif not existing.get('emailVerified'):
                # An established account may still need to prove this email address.
                # Verification alone must not reset its password or second factor.
                self.onboarding_actions=['VERIFY_EMAIL'];onboarding=True
            return existing['id'],onboarding
        organization=self.organization_for(owner)
        actions=['VERIFY_EMAIL','UPDATE_PROFILE','UPDATE_PASSWORD','CONFIGURE_TOTP']
        if os.environ.get('INVITE_RECOVERY_CODES')=='true':actions.append('CONFIGURE_RECOVERY_AUTHN_CODES')
        self.onboarding_actions=actions
        self.call('users','POST',{'username':email,'email':email,'enabled':True,'emailVerified':False,'requiredActions':actions,'attributes':{'koodaria_access':['diagram_guest']}})
        user=self.find(email)
        if not user:raise InvitationUnavailable('No se pudo preparar la cuenta invitada.')
        self.call('organizations/'+organization+'/members','POST',user['id'])
        return user['id'],True
    def send_onboarding(self,user_id):
        self.call('users/'+user_id+'/execute-actions-email','PUT',getattr(self,'onboarding_actions',['VERIFY_EMAIL','UPDATE_PROFILE','UPDATE_PASSWORD','CONFIGURE_TOTP']),params={'client_id':'koodaria-web','redirect_uri':'https://koodaria.com/auth/login','lifespan':86400})
