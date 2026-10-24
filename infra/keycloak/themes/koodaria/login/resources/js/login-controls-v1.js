/* Input affordances only; authentication and validation remain with Keycloak. */
(() => {
 const initialize=()=>{
  const otp=document.getElementById('otp');
  if(otp)otp.inputMode='numeric';
  const language=document.getElementById('kc-current-locale-link');
  if(language){const label=document.documentElement.lang.startsWith('es')?'Cambiar idioma':'Change language';language.setAttribute('aria-label',label+' · '+language.textContent.trim());}
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});else initialize();
})();
