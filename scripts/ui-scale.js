/* Scale the whole app while keeping viewport fit, responsive panes and menus. */
function uiScaleFactor(){const value=Number(state.uiScale);return Number.isFinite(value)&&value>=75&&value<=200?value/100:1.4;}
function applyUiScale(){state.uiScale=Math.round(uiScaleFactor()*100);document.documentElement.style.setProperty('--ui-scale',String(uiScaleFactor()));const width=window.innerWidth/uiScaleFactor();document.body.classList.toggle('compact-layout',width<=850);document.body.classList.toggle('narrow-layout',width<=480);$('ui-scale').value=String(state.uiScale);closeMessageMenu();}
$('ui-scale').onchange=()=>{const next=Number($('ui-scale').value);state.uiScale=Number.isFinite(next)&&next>=75&&next<=200?next:140;persist('uiScale',state.uiScale);applyUiScale();};
window.addEventListener('resize',applyUiScale);
