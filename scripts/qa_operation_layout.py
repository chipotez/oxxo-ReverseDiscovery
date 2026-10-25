"""Rendered catalog pagination and compact card alignment, synthetic session."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
base='http://localhost:18179';report={'synthetic_identity_only':True,'layouts':[]}
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless=True);page=b.new_page();page.goto(base+'/__qa/session')
 for route in ['catalogo','catalogo/observabilidad']:
  page.goto(base+'/bienvenida/#/'+route)
  for theme in ['light','dark']:
   page.evaluate('(t)=>document.documentElement.dataset.theme=t',theme)
   for w,h in [(1440,900),(390,844),(844,390)]:
    page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(250)
    r=page.locator('.catalog-pagination').bounding_box();last=page.locator('.catalog-card').last.bounding_box();assert r and r['y']+r['height']<=h+2,(route,w,h,'pagination',r);assert last['y']+last['height']<=r['y']+2,(route,w,h,'card',last,r)
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
    report['layouts'].append(dict(route=route,theme=theme,width=w,height=h))
    if theme=='light' and (w,h)==(1440,900):page.screenshot(path='.artifacts/nesting/operation-'+route.replace('/','-')+'.png')
 Path('docs/evidence/operation-layout-report.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS operation catalog layouts');b.close()
