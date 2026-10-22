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

// Local, finite demonstration: never opens a shell or sends a network request.
const terminal = document.querySelector('.terminal');
if (terminal) {
  const screen = terminal.querySelector('.terminal-screen');
  const commands = [...terminal.querySelectorAll('[data-terminal-command]')];
  const output = terminal.querySelector('[data-terminal-output]');
  const control = terminal.querySelector('.terminal-control');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const original = commands.map(command => command.textContent);
  const accessibleText = document.createElement('p');
  accessibleText.className = 'sr-only';
  accessibleText.textContent = screen.textContent;
  terminal.append(accessibleText);
  screen.setAttribute('aria-hidden', 'true');
  let timer;
  let started = false;
  let paused = false;
  let finished = false;
  let line = 0;
  let character = 0;
  const complete = () => {
    clearTimeout(timer);
    commands.forEach((command, i) => { command.textContent = original[i]; });
    output.classList.remove('awaiting-output');
    terminal.classList.remove('is-typing');
    finished = true;
    paused = false;
    control.textContent = 'Repetir animación';
  };
  const step = () => {
    if (paused || finished) return;
    const current = commands[line];
    current.textContent = original[line].slice(0, ++character);
    if (character < original[line].length) {
      timer = setTimeout(step, 42);
    } else if (line === 0) {
      timer = setTimeout(() => {
        output.classList.remove('awaiting-output');
        line = 1;
        character = 0;
        timer = setTimeout(step, 600);
      }, 450);
    } else {
      complete();
    }
  };
  const start = () => {
    clearTimeout(timer);
    line = 0;
    character = 0;
    paused = false;
    finished = false;
    started = true;
    commands.forEach(command => { command.textContent = ''; });
    output.classList.add('awaiting-output');
    terminal.classList.add('is-typing');
    control.hidden = false;
    control.textContent = 'Pausar animación';
    step();
  };
  control.addEventListener('click', () => {
    if (motion.matches) return;
    if (finished) { start(); return; }
    paused = !paused;
    terminal.classList.toggle('is-paused', paused);
    control.textContent = paused ? 'Continuar animación' : 'Pausar animación';
    if (paused) clearTimeout(timer);
    else step();
  });
  motion.addEventListener('change', () => {
    if (motion.matches) { complete(); control.hidden = true; }
  });
  if (!motion.matches) {
    const observer = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting) && !started) {
        start();
        observer.disconnect();
      }
    }, { threshold: 0.3 });
    observer.observe(terminal);
  }
}
