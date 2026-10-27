window.KoodariaResourceFlow.mount(document.querySelector('#contenido'));
const expiry=new Date(document.querySelector('meta[name=temporary-expiry]').content);document.querySelector('#link-expiry').textContent='Vence a las '+expiry.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
