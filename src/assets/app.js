/** @typedef {'modulos' | 'rutas' | 'especializaciones'} CatalogTab */
const tablist = document.querySelector('.tabs');
const tabs = [...document.querySelectorAll('[data-tab]')];
const panels = [...document.querySelectorAll('.catalog-panel')];

/** @param {string} id @param {boolean} focus */
function selectTab(id, focus = false) {
  const target = tabs.find(tab => tab.dataset.tab === id);
  if (!target) return;
  tabs.forEach(tab => {
    const selected = tab === target;
    tab.setAttribute('aria-selected', String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  panels.forEach(panel => { panel.hidden = panel.id !== `panel-${id}`; });
  if (focus) target.focus();
}
if (tablist && tabs.length) {
  tablist.setAttribute('role', 'tablist');
  tabs.forEach((tab, index) => {
    tab.setAttribute('role', 'tab');
    tab.addEventListener('click', () => selectTab(tab.dataset.tab));
    tab.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) {
        event.preventDefault();
        selectTab(tabs[next].dataset.tab, true);
      }
    });
  });
  panels.forEach(panel => { panel.setAttribute('role', 'tabpanel'); panel.tabIndex = 0; });
  selectTab('modulos');
}
document.querySelectorAll('[data-select-tab]').forEach(link => {
  link.addEventListener('click', () => selectTab(link.dataset.selectTab, true));
});
const menu = document.querySelector('.menu-toggle');
const navigation = document.getElementById('primary-navigation');
if (menu && navigation) {
  document.documentElement.classList.add('js');
  const closeMenu = (restoreFocus = false) => {
    menu.setAttribute('aria-expanded', 'false');
    menu.setAttribute('aria-label', 'Abrir menú');
    navigation.classList.remove('is-open');
    if (restoreFocus) menu.focus();
  };
  menu.addEventListener('click', () => {
    const open = menu.getAttribute('aria-expanded') !== 'true';
    menu.setAttribute('aria-expanded', String(open));
    menu.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    navigation.classList.toggle('is-open', open);
  });
  navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', () => closeMenu()));
  document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') closeMenu(true); });
  document.addEventListener('click', event => { if (!navigation.contains(event.target) && !menu.contains(event.target)) closeMenu(); });
  document.querySelector('.site-header').addEventListener('focusout', event => {
    if (!document.querySelector('.site-header').contains(event.relatedTarget)) closeMenu();
  });
  matchMedia('(min-width: 1200px)').addEventListener('change', () => closeMenu());
}
function revealAnchorDetails() {
  const id = decodeURIComponent(location.hash.slice(1));
  const target = document.getElementById(id);
  if (target instanceof HTMLDetailsElement) target.open = true;
}
window.addEventListener('hashchange', revealAnchorDetails);
revealAnchorDetails();

// Browser-only looping demonstration; commands are never executed.
const terminal = document.querySelector('.terminal');
if (terminal) {
  const screen = terminal.querySelector('.terminal-screen');
  const commands = [...terminal.querySelectorAll('[data-terminal-command]')];
  const output = terminal.querySelector('[data-terminal-output]');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const original = commands.map(command => command.textContent);
  const accessibleText = document.createElement('p');
  accessibleText.className = 'sr-only';
  accessibleText.textContent = screen.textContent;
  terminal.append(accessibleText);
  screen.setAttribute('aria-hidden', 'true');
  terminal.tabIndex = 0;
  terminal.setAttribute('role', 'region');
  terminal.setAttribute('aria-label', 'Demostración de terminal. La animación se pausa al enfocar esta zona.');
  let timer;
  let position = 0;
  let visible = false;
  let focused = false;
  const steps = [{delay: 350, action: () => {
    commands.forEach(command => { command.textContent = ''; });
    output.classList.add('awaiting-output');
  }}];
  original.forEach((text, line) => {
    for (let length = 1; length <= text.length; length++) {
      steps.push({delay: 42, action: () => { commands[line].textContent = text.slice(0, length); }});
    }
    if (line === 0) {
      steps.push({delay: 450, action: () => { output.classList.remove('awaiting-output'); }});
      steps.push({delay: 600, action: () => {}});
    }
  });
  steps.push({delay: 2400, action: () => {}});
  const showComplete = () => {
    commands.forEach((command, i) => { command.textContent = original[i]; });
    output.classList.remove('awaiting-output');
  };
  const advance = () => {
    if (!visible || focused || document.hidden || motion.matches) return;
    const step = steps[position];
    step.action();
    position = (position + 1) % steps.length;
    timer = setTimeout(advance, step.delay);
  };
  const sync = () => {
    clearTimeout(timer);
    if (motion.matches) { position = 0; showComplete(); }
    else advance();
  };
  terminal.addEventListener('focusin', () => { focused = true; sync(); });
  terminal.addEventListener('focusout', () => { focused = false; sync(); });
  motion.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  new IntersectionObserver(entries => {
    visible = entries.some(entry => entry.isIntersecting);
    sync();
  }, { threshold: 0.3 }).observe(terminal);
}
