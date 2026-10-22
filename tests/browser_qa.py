"""Optional QA: pip install playwright==1.55.0; uses installed Chrome, no browser download."""
from pathlib import Path
import json
import os
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'.artifacts'
URL=os.environ.get('KOODARIA_TEST_URL','http://127.0.0.1:4173')
report={'url':URL,'viewports':[],'console_errors':[],'failed_requests':[]}
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('KOODARIA_CHROME_PATH','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),headless=True)
    context=browser.new_context()
    page=context.new_page()
    page.route('**/__qa/axe.js', lambda route: route.fulfill(path=str(ART/'axe.min.js'), content_type='application/javascript'))
    page.on('pageerror',lambda error:report['console_errors'].append(str(error)))
    page.on('console',lambda msg: report['console_errors'].append(msg.text) if msg.type=='error' else None)
    page.on('requestfailed',lambda req:report['failed_requests'].append(req.url))
    for width,height in [(1440,1000),(1280,900),(1024,768),(768,1024),(390,844),(320,740)]:
        page.set_viewport_size({'width':width,'height':height})
        print(f'Checking {width}px', flush=True)
        page.goto(URL,wait_until='networkidle')
        assert page.title().startswith('Koodaria')
        overflow=page.evaluate('document.documentElement.scrollWidth > innerWidth')
        assert not overflow, f'Overflow at {width}'
        tabs=page.get_by_role('tab')
        assert tabs.count()==3
        tabs.nth(1).click()
        assert page.get_by_role('tabpanel').count()==1
        assert page.get_by_role('tabpanel').get_by_role('article').count()==3
        tabs.nth(1).press('ArrowRight')
        assert tabs.nth(2).get_attribute('aria-selected')=='true'
        tabs.nth(2).press('Home')
        assert tabs.nth(0).get_attribute('aria-selected')=='true'
        assert page.get_by_role('tabpanel').get_by_role('article').count()==6
        page.locator('#panel-modulos summary').first.click()
        assert page.locator('#panel-modulos details').first.get_attribute('open') is not None
        page.locator('#panel-modulos summary').first.click()
        if width<1200:
            toggle=page.locator('.menu-toggle')
            toggle.click()
            assert toggle.get_attribute('aria-expanded')=='true'
            page.get_by_role('navigation',name='Principal').get_by_role('link',name='Tecnologías',exact=True).click()
            assert toggle.get_attribute('aria-expanded')=='false'
            assert page.evaluate('location.hash')=='#tecnologias'
            toggle.click()
            toggle.press('Escape')
            assert toggle.get_attribute('aria-expanded')=='false'
        page.locator('.footer-grid [data-select-tab="rutas"]').click()
        assert tabs.nth(1).get_attribute('aria-selected')=='true'
        page.locator('.footer-grid a[href="#contacto"]').click()
        expect(page.locator('#contacto')).to_have_attribute('open', '')
        page.goto(URL,wait_until='networkidle')
        if (ART/'axe.min.js').exists():
            page.add_script_tag(url=URL+'/__qa/axe.js')
            result=page.evaluate("""async () => await axe.run(document, {runOnly: {type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})""")
            violations=[{'id':v['id'],'impact':v['impact'],'nodes':[{'target':n['target'],'failure':n['failureSummary']} for n in v['nodes']]} for v in result['violations']]
        else:
            raise RuntimeError('Supply .artifacts/axe.min.js v4.10.3 for accessibility verification')
        report['viewports'].append({'width':width,'height':height,'overflow':overflow,'axe_violations':violations})
        if width in [1440,768,390]:
            page.screenshot(path=str(ART/f'home-{width}.png'),full_page=True,animations='disabled')
            page.screenshot(path=str(ART/f'home-{width}-viewport.png'),full_page=False,animations='disabled')
    # 200% equivalent text/viewport reflow, and reduced-motion behavior.
    page.set_viewport_size({'width':640,'height':900})
    page.emulate_media(reduced_motion='reduce')
    page.goto(URL,wait_until='networkidle')
    assert page.evaluate('getComputedStyle(document.documentElement).scrollBehavior')=='auto'
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
    fallback=nojs.new_page()
    fallback.goto(URL)
    assert fallback.locator('.competency-card:visible').count()==12
    assert fallback.get_by_role('navigation',name='Principal').is_visible()
    report['no_js_fallback']='12 cards and navigation visible'
    report['reflow_640_and_reduced_motion']='passed'
    browser.close()
(ART/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
assert not report['console_errors'],report['console_errors']
assert not report['failed_requests'],report['failed_requests']
assert not any(v['axe_violations'] for v in report['viewports']), 'Accessibility violations; see report'
