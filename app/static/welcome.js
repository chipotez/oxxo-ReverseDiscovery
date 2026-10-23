const menu = document.querySelector('.user-menu');
document.addEventListener('click', event => { if (menu && !menu.contains(event.target)) menu.open = false; });
document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu?.open) { menu.open=false; menu.querySelector('summary').focus(); } });
document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => {
 document.querySelectorAll('[data-view]').forEach(tab => tab.setAttribute('aria-pressed',String(tab===button)));
 document.querySelector('#view-label').textContent = button.textContent;
}));
