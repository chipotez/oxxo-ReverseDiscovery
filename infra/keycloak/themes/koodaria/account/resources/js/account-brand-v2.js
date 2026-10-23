/* Keep the same text metrics as Home; never access account fields or tokens. */
const brandAccount = () => {
  document.querySelectorAll('button.pf-v5-c-menu-toggle.pf-m-plain:not([aria-label])').forEach(button => {
    if (!button.textContent.trim()) button.setAttribute('aria-label', document.documentElement.lang.startsWith('es') ? 'Opciones' : 'Options');
  });
  const brand = document.querySelector('.pf-v5-c-masthead__brand');
  if (!brand || brand.querySelector('.koodaria-wordmark')) return;
  const text = document.createElement('span');
  text.className = 'koodaria-wordmark';
  text.textContent = 'koodaria';
  brand.replaceChildren(text);
  brand.href = 'https://koodaria.com/';
  brand.setAttribute('aria-label', 'Koodaria');
};
new MutationObserver(brandAccount).observe(document.documentElement, {childList:true, subtree:true});
brandAccount();

// Compact personal details into two usable pages on short/narrow viewports.
let currentForm;
let resizeProfile = () => {};
const adaptProfile = () => {
 const input = document.querySelector('#firstName');
 const form = input?.closest('form');
 if (!form || form === currentForm) return;
 currentForm = form;
 const groups = [...form.querySelectorAll('.pf-v5-c-form__group:not(.pf-m-action)')];
 const action = form.querySelector('.pf-m-action');
 if (groups.length < 4 || !action) return;
 const es = document.documentElement.lang.startsWith('es');
 const nav = document.createElement('nav');
 nav.className = 'account-profile-steps';
 nav.setAttribute('aria-label', es ? 'Datos de la cuenta' : 'Account details');
 const previous = document.createElement('button');
 previous.type = 'button'; previous.className = 'pf-v5-c-button pf-m-link';
 previous.textContent = es ? 'Anterior' : 'Previous';
 const next = document.createElement('button');
 next.type = 'button'; next.className = 'pf-v5-c-button pf-m-primary';
 next.textContent = es ? 'Continuar' : 'Continue';
 const status = document.createElement('span'); status.setAttribute('aria-live','polite');
 nav.append(previous, status, next); form.before(nav);
 let step = 1;
 const update = () => {
  const height = window.visualViewport?.height || innerHeight;
  const compact = (innerWidth < 768 && height < 780) || height < 540;
  nav.hidden = !compact;
  groups.forEach((g,i) => { g.hidden = compact && (step === 1 ? i >= 3 : i < 3); });
  action.hidden = compact && step === 1;
  previous.hidden = step === 1; next.hidden = step === 2;
  status.textContent = `${step} / 2 · ${step === 1 ? (es ? 'Cuenta' : 'Account') : (es ? 'Nombre' : 'Name')}`;
 };
 previous.onclick = () => {step=1;update();groups[0].querySelector('button,input')?.focus();};
 next.onclick = () => {step=2;update();input.focus();};
 resizeProfile = update; update();
};
new MutationObserver(adaptProfile).observe(document.documentElement,{childList:true,subtree:true});
window.addEventListener('resize',()=>resizeProfile());
window.visualViewport?.addEventListener('resize',()=>resizeProfile());
adaptProfile();

let currentSecurity;
let resizeSecurity = () => {};
const adaptSecurity = () => {
 const password = document.querySelector('[data-testid="password/help"]');
 const section = password?.closest('section');
 const container = section?.parentElement;
 if (!container || container === currentSecurity) return;
 const sections = [...container.children].filter(e=>e.tagName === 'SECTION');
 if (sections.length < 2) return;
 currentSecurity = container;
 const nav = document.createElement('nav');nav.className='account-security-tabs';
 nav.setAttribute('aria-label',document.documentElement.lang.startsWith('es')?'Métodos de acceso':'Sign-in methods');
 let active=0;
 const buttons=sections.map((panel,i)=>{
  const button=document.createElement('button');button.type='button';button.className='pf-v5-c-button pf-m-secondary';
  button.textContent=panel.querySelector('h2')?.textContent || String(i+1);
  button.onclick=()=>{active=i;update();};nav.append(button);return button;
 });
 container.prepend(nav);
 const update=()=>{
  const compact=innerWidth<800 || (window.visualViewport?.height || innerHeight)<620;
  nav.hidden=!compact;
  sections.forEach((panel,i)=>{panel.hidden=compact && i!==active;});
  buttons.forEach((button,i)=>button.setAttribute('aria-pressed',String(i===active)));
 };
 resizeSecurity=update;update();
};
new MutationObserver(adaptSecurity).observe(document.documentElement,{childList:true,subtree:true});
window.addEventListener('resize',()=>resizeSecurity());
window.visualViewport?.addEventListener('resize',()=>resizeSecurity());
adaptSecurity();
// Secondary session metadata remains available without overwhelming small screens.
const adaptDevices = () => {
 document.querySelectorAll('.signed-in-device-grid').forEach(list=>{
  if (list.dataset.koodariaDetails) return;
  const groups=[...list.children];if(groups.length<4)return;
  list.dataset.koodariaDetails='true';
  const details=document.createElement('details');details.className='account-device-details';
  const summary=document.createElement('summary');summary.textContent=document.documentElement.lang.startsWith('es')?'Más detalles de la sesión':'More session details';
  const extra=document.createElement('dl');extra.className='pf-v5-c-description-list account-device-extra';
  groups.slice(2).forEach(group=>extra.append(group));details.append(summary,extra);list.after(details);
 });
};
new MutationObserver(adaptDevices).observe(document.documentElement,{childList:true,subtree:true});
adaptDevices();
