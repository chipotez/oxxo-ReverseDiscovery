"""Browser checks for the finite, pausable terminal demonstration."""
import os
from playwright.sync_api import sync_playwright, expect

url=os.environ.get('KOODARIA_TEST_URL','http://127.0.0.1:4174')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('KOODARIA_CHROME_PATH','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),headless=True)
    page=browser.new_page()
    page.goto(url,wait_until='networkidle')
    control=page.locator('.terminal-control')
    expect(control).to_be_visible()
    control.click()
    expect(control).to_have_text('Continuar animación')
    paused=page.locator('[data-terminal-command]').all_text_contents()
    page.wait_for_timeout(250)
    assert page.locator('[data-terminal-command]').all_text_contents()==paused
    control.click()
    expect(control).to_have_text('Repetir animación',timeout=10000)
    complete=['systemctl status example.service','journalctl -u example.service']
    assert page.locator('[data-terminal-command]').all_text_contents()==complete
    control.click()
    expect(control).to_have_text('Pausar animación')
    page.emulate_media(reduced_motion='reduce')
    expect(control).to_be_hidden()
    assert page.locator('[data-terminal-command]').all_text_contents()==complete
    assert page.locator('.skip-link').bounding_box()['y']<0
    page.goto(url,wait_until='networkidle')
    expect(control).to_be_hidden()
    assert page.locator('[data-terminal-command]').all_text_contents()==complete
    browser.close()
print('Typing, pause, resume, replay and reduced motion passed')
