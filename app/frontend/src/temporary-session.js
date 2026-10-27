export const temporaryHeaders=()=>{const visit=document.querySelector('meta[name=temporary-visit]')?.content;return visit?{'X-Koodaria-Visit':visit}:{}};
