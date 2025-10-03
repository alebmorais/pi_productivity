const clock = document.getElementById('clock');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const motionEl = document.getElementById('motion');
const modeEl = document.getElementById('mode');
const corgi = document.getElementById('corgi');
const presetButtons = Array.from(document.querySelectorAll('[data-mode-btn]'));
const presetStatus = document.getElementById('presetStatus');

const VALID_MODES = ['idle','focus','break','alert'];

function isPresent(value){
  return value !== undefined && value !== null;
}

function ensureObject(value){
  return value !== undefined && value !== null && typeof value === 'object' ? value : {};
}

function ensureArray(value){
  return Array.isArray(value) ? value : [];
}

function hasOwn(obj, prop){
  return Object.prototype.hasOwnProperty.call(obj, prop);
}

function normalizeMode(value){
  if(!isPresent(value)){
    return 'idle';
  }
  const lower = String(value).toLowerCase();
  for(const candidate of VALID_MODES){
    if(lower.includes(candidate)){
      return candidate;
    }
  }
  return 'idle';
}

function describeMode(value){
  const normalized = normalizeMode(value);
  return {
    normalized,
    label: normalized.charAt(0).toUpperCase() + normalized.slice(1),
  };
}

function formatNumber(value){
  const num = Number(value);
  return Number.isFinite(num) ? num.toFixed(1) : '--';
}

function dogUrl(state, activity){
  const mode = encodeURIComponent(normalizeMode(state));
  let act = Number(activity);
  if(!Number.isFinite(act)){
    act = 0;
  }
  act = Math.max(0, Math.min(1, act));
  const ts = Date.now();
  return `/dog.svg?mode=${mode}&activity=${act.toFixed(2)}&ts=${ts}`;
}

function tickClock(){
  const now = new Date();
  clock.textContent = now.toLocaleString();
}

function setCorgi(state, activity){
  const next = normalizeMode(state);
  corgi.classList.remove('idle','focus','break','alert');
  corgi.classList.add(next);
  corgi.src = dogUrl(next, activity);
  corgi.dataset.mode = next;
}

function setPresetStatus(message = '', isError = false){
  if(!presetStatus){
    return;
  }
  presetStatus.textContent = message;
  if(isError){
    presetStatus.classList.add('error');
  }else{
    presetStatus.classList.remove('error');
  }
}

function updatePresetButtons(activeMode){
  if(!presetButtons.length){
    return;
  }
  const normalized = normalizeMode(activeMode);
  for(const btn of presetButtons){
    const target = normalizeMode(btn.dataset.mode);
    const isActive = target === normalized;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  }
}

function bindPresetButtons(){
  if(!presetButtons.length){
    return;
  }
  for(const btn of presetButtons){
    btn.addEventListener('click', async ()=>{
      const desiredInfo = describeMode(btn.dataset.mode);
      setPresetStatus(`Atualizando para ${desiredInfo.label}...`);
      btn.disabled = true;
      try{
        const response = await fetch('/api/mode', {
          method:'POST',
          headers:{'Content-Type':'application/json'},
          body: JSON.stringify({mode: desiredInfo.normalized})
        });
        if(!response.ok){
          throw new Error(`HTTP ${response.status}`);
        }
        let payload = {};
        try{
          payload = await response.json();
        }catch(_err){
          payload = {};
        }
        const next = updateModeDisplay(payload.mode ?? desiredInfo.normalized);
        setCorgi(next, 0);
        updatePresetButtons(next);
        const nextLabel = describeMode(next).label;
        setPresetStatus(`Modo definido para ${nextLabel}.`);
      }catch(err){
        console.error('Failed to set mode', err);
        setPresetStatus('Não foi possível atualizar o modo agora.', true);
      }finally{
        btn.disabled = false;
      }
    });
  }
}

function updateSense(senseData){
  const sense = ensureObject(senseData);
  tempEl.textContent = formatNumber(sense.temperature);
  humEl.textContent = formatNumber(sense.humidity);
  presEl.textContent = formatNumber(sense.pressure);

  if(sense.available){
    senseAvail.textContent = 'Sense HAT available';
  }else if(hasOwn(sense, 'error') && isPresent(sense.error)){
    senseAvail.textContent = String(sense.error);
  }else{
    senseAvail.textContent = 'Sense HAT unavailable';
  }
}

function updateMotion(lines){
  const list = ensureArray(lines).map((item)=>String(item));
  motionEl.textContent = list.length ? list.join('\n') : 'No recent motion events.';
}

function updateModeDisplay(modeValue){
  const info = describeMode(modeValue);
  modeEl.textContent = `Mode: ${info.label}`;
  return info.normalized;
}

function applyStatus(payload){
  if(!payload || typeof payload !== 'object'){
    return;
  }
  const normalizedMode = updateModeDisplay(payload.mode);
  const activity = Number(payload.activity_level);
  const activityValue = Number.isFinite(activity) ? activity : 0;
  setCorgi(normalizedMode, activityValue);
  updatePresetButtons(normalizedMode);
  updateSense(payload.sense);
  updateMotion(payload.motion);
}

async function refreshOnce(){
  try{
    const r = await fetch('/api/status');
    if(!r.ok){
      console.error('Status fetch failed', r.status, r.statusText);
      return;
    }
    const j = await r.json();
    applyStatus(j);
  }catch(e){
    console.error(e);
  }
}

function handleEnvelope(message){
  if(!message || typeof message !== 'object'){
    return;
  }
  if(hasOwn(message, 'kind') && message.kind === 'tick'){
    applyStatus(message.payload);
    return;
  }
  if(hasOwn(message, 'mode') || hasOwn(message, 'sense') || hasOwn(message, 'motion')){
    applyStatus(message);
  }
}

async function initWS(){
  try{
    const ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');
    ws.onmessage = (ev)=>{
      try{
        const message = JSON.parse(ev.data);
        handleEnvelope(message);
      }catch(err){
        console.error('Failed to parse WS message', err);
      }
    };
    ws.onclose = ()=> setTimeout(initWS, 2000);
  }catch(e){
    console.error('WS init failed', e);
  }
}

setCorgi('idle', 0);
updatePresetButtons('idle');
setPresetStatus('');
bindPresetButtons();

tickClock();
setInterval(tickClock, 500);
refreshOnce();
initWS();
