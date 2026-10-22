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
