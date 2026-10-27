const menu = document.querySelector('.user-menu');
document.addEventListener('click', event => { if (menu && !menu.contains(event.target)) menu.open = false; });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu?.open) { menu.open=false; menu.querySelector('summary').focus(); } });
const themeToggle = document.querySelector('.theme-toggle');
const setTheme = theme => {
 document.documentElement.dataset.theme = theme;
 themeToggle?.setAttribute('aria-pressed',String(theme==='dark'));
 themeToggle?.setAttribute('aria-label',theme==='dark'?'Activar tema claro':'Activar tema oscuro');
};
try { setTheme(localStorage.getItem('koodaria-theme')==='dark'?'dark':'light'); } catch { setTheme('light'); }
themeToggle?.addEventListener('click',()=>{
 const theme=document.documentElement.dataset.theme==='dark'?'light':'dark';setTheme(theme);
 try { localStorage.setItem('koodaria-theme',theme); } catch { /* Preference is optional. */ }
});
