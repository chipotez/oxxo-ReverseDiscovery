"""Native public login, visibility toggle only. Never authenticates or captures a secret."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
report={'public_native_login':True,'no_authentication_attempt':True,'layouts':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page(viewport={'width':1440,'height':900});errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 page.goto('https://koodaria.com/auth/login');page.locator('button[data-password-toggle]').wait_for(timeout=60000)
 assert page.locator('link[href*="password-field-v1.css"]').count()==1
 toggle=page.locator('button[data-password-toggle]').first;password=page.locator('#'+toggle.get_attribute('aria-controls'));group=toggle.locator('..')
 for theme in ['light','dark']:
  page.emulate_media(color_scheme=theme)
  for w,h in [(1440,900),(390,844),(844,390)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150)
   g=group.bounding_box();r=toggle.bounding_box();assert g and r and r['x']>=g['x'] and r['x']+r['width']<=g['x']+g['width']+1
   assert toggle.evaluate('(e)=>getComputedStyle(e).borderWidth')=='0px'
   assert password.evaluate('(e)=>getComputedStyle(e).borderWidth')=='0px'
   assert toggle.evaluate("(e)=>getComputedStyle(e,'::before').backgroundImage.includes('eye.svg')")
   password.fill('qa-visibility-only');toggle.click();assert password.get_attribute('type')=='text';assert password.input_value()=='qa-visibility-only';assert toggle.evaluate("(e)=>getComputedStyle(e,'::before').backgroundImage.includes('eye-off.svg')")
   toggle.focus();page.keyboard.press('Space');assert password.get_attribute('type')=='password';password.fill('')
   submit=page.locator('#kc-login').bounding_box();assert submit['y']+submit['height']<=h+1,(w,h,submit)
   assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
   report['layouts'].append(dict(theme=theme,width=w,height=h,toggle_inside=True,keyboard_toggle=True,action_visible=True))
 page.set_viewport_size({'width':1440,'height':900});page.screenshot(path='.artifacts/nesting/password-field-empty.png');assert not errors,errors
 report['browser_errors']=errors;Path('docs/evidence/password-field-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS native visibility toggle inside shared boundary, keyboard and six layouts');b.close()
