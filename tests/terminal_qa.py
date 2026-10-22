"""Browser checks for automatic looping and reduced-motion fallback."""
import os
from playwright.sync_api import sync_playwright

url=os.environ.get('KOODARIA_TEST_URL','https://koodaria.com')
with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=os.environ.get('KOODARIA_CHROME_PATH','/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'),headless=True)
    page=browser.new_page()
    errors=[]
    page.on('pageerror', lambda error: errors.append(str(error)))
    page.goto(url,wait_until='networkidle')
    assert page.locator('.terminal button').count()==0
    page.wait_for_function('''() => {
      const commands = [...document.querySelectorAll('[data-terminal-command]')].map(e => e.textContent);
      const state = window.__terminalTest ||= {completed: false, restarts: 0};
      const complete = commands[0] === 'systemctl status example.service' && commands[1] === 'journalctl -u example.service';
      if (state.completed && !complete) { state.restarts++; state.completed = false; }
      if (complete) state.completed = true;
      return state.restarts >= 2;
    }''', timeout=25000)
    page.locator('.terminal').focus()
    paused=page.locator('[data-terminal-command]').all_text_contents()
    page.wait_for_timeout(300)
    assert page.locator('[data-terminal-command]').all_text_contents()==paused
    page.locator('h1').click()
    page.emulate_media(reduced_motion='reduce')
    complete=['systemctl status example.service','journalctl -u example.service']
    page.wait_for_function("document.querySelector('[data-terminal-command]').textContent === 'systemctl status example.service'")
    assert page.locator('[data-terminal-command]').all_text_contents()==complete
    page.wait_for_timeout(300)
    assert page.locator('[data-terminal-command]').all_text_contents()==complete
    assert not errors,errors
    browser.close()
print('Two automatic loops, no button, focus pause and reduced motion passed')
