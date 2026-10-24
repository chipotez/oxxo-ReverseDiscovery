/* Presentation only. Codes remain in Keycloak's native form and export actions. */
(() => {
 const initialize=()=>{
  const list=document.getElementById('kc-recovery-codes-list');
  const form=document.getElementById('kc-recovery-codes-settings-form');
  if(!list||!form)return;
  const card=list.closest('.card-pf'),warning=list.previousElementSibling;
  const notice=card.querySelector('#kc-content-wrapper > .alert-warning');
  const actions=document.getElementById('printRecoveryCodes')?.parentElement;
  const confirmation=document.getElementById('kcRecoveryCodesConfirmationCheck')?.parentElement;
  if(!actions||!confirmation)return;
  const es=document.documentElement.lang.startsWith('es'),items=[...list.children];
  card.classList.add('recovery-enrollment');
  const warningTitle=warning?.querySelector('.pf-c-alert__title'),warningDescription=warning?.querySelector('.pf-c-alert__description p');
  if(warningTitle)warningTitle.textContent=es?'Guárdalos antes de continuar.':'Save your codes.';
  if(warningDescription)warningDescription.textContent=es?'No volverán a mostrarse. Descárgalos o cópialos a tu gestor de contraseñas. Cada código sirve una vez. Cancelar los invalida.':'You will not see these codes again. Save them in your password manager. Each works once. Canceling invalidates them.';
  const status=document.createElement('p');status.className='recovery-step-status';status.setAttribute('role','status');list.before(status);
  const nav=document.createElement('nav');nav.className='enrollment-navigation';nav.setAttribute('aria-label',es?'Configuración de recuperación':'Recovery setup');
  const back=document.createElement('button'),next=document.createElement('button');back.type=next.type='button';back.className='enrollment-previous';next.className='enrollment-next';back.textContent=es?'Anterior':'Back';next.textContent=es?'Continuar':'Continue';nav.append(back,next);card.append(nav);
  let stage=0,page=0,size=4;
  function render(focus=false){
   const pages=Math.ceil(items.length/size);
   if(warning)warning.hidden=stage!==0;
   if(notice&&notice!==warning)notice.hidden=stage!==0;
   list.hidden=actions.hidden=stage!==1;confirmation.hidden=form.hidden=stage!==2;
   items.forEach((item,i)=>item.hidden=stage===1&&(i<page*size||i>=(page+1)*size));
   status.textContent=stage===0?(es?'Guarda tus códigos.':'Save your codes.'):stage===1?(es?'Códigos ':'Codes ')+(page*size+1)+'–'+Math.min((page+1)*size,items.length)+(es?' de ':' of ')+items.length:(es?'Confirma que guardaste tus códigos.':'Confirm that you saved your codes.');
   back.hidden=stage===0;next.hidden=stage===2;
   if(focus){status.tabIndex=-1;status.focus({preventScroll:true});}
  }
  back.onclick=()=>{if(stage===1&&page>0)page--;else stage--;render(true);};
  next.onclick=()=>{if(stage===1&&page<Math.ceil(items.length/size)-1)page++;else stage++;render(true);};
  function resize(){const h=window.visualViewport?.height||innerHeight;size=innerWidth<480&&h<620?3:h<700?4:8;page=Math.min(page,Math.ceil(items.length/size)-1);render();}
  addEventListener('resize',resize,{passive:true});window.visualViewport?.addEventListener('resize',resize,{passive:true});resize();
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});else initialize();
})();
