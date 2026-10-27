// The capability stays out of request URLs and access logs; submit only in POST body.
const tokenInput=document.querySelector('input[name=token]');
if(tokenInput&&!tokenInput.value)tokenInput.value=location.hash.slice(1);
