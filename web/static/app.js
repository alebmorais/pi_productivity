const clock = document.getElementById('clock');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const motionEl = document.getElementById('motion');
const modeEl = document.getElementById('mode');
const corgi = document.getElementById('corgi');

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
  const normalized = normalizeMode(modeValue);
  const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);
  modeEl.textContent = `Mode: ${label}`;
  return normalized;
}

function applyStatus(payload){
  if(!payload || typeof payload !== 'object'){
    return;
  }
  const normalizedMode = updateModeDisplay(payload.mode);
  const activity = Number(payload.activity_level);
  const activityValue = Number.isFinite(activity) ? activity : 0;
  setCorgi(normalizedMode, activityValue);
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

tickClock();
setInterval(tickClock, 500);
refreshOnce();
initWS();
