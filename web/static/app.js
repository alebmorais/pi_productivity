
const clock = document.getElementById('clock');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const motionEl = document.getElementById('motion');
const modeEl = document.getElementById('mode');
const corgi = document.getElementById('corgi');

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

function formatReading(value){
  return isPresent(value) && typeof value.toFixed === 'function' ? value.toFixed(1) : '--';
}

function dogUrl(state, activity){
  const modeValue = state !== undefined && state !== null ? state : 'idle';
  const mode = encodeURIComponent(modeValue);
  const activityValue = activity !== undefined && activity !== null ? activity : 0;
  let act = Number(activityValue);
  if(!Number.isFinite(act)){ act = 0; }
  act = Math.max(0, Math.min(1, act));
  const ts = Date.now();
  return `/dog.svg?mode=${mode}&activity=${act.toFixed(2)}&ts=${ts}`;
}

function tickClock(){
  const now = new Date();
  clock.textContent = now.toLocaleString();
}
setInterval(tickClock, 500);

function setCorgi(state, activity){
  // swap CSS class to animate different states
  const next = isPresent(state) ? state : 'idle';
  corgi.classList.remove('idle','focus','break','alert');
  corgi.classList.add(next);
  corgi.src = dogUrl(next, activity);
  corgi.dataset.mode = next;
}

async function refreshOnce(){
  try{
    const r = await fetch('/api/status');
    const j = await r.json();
    const status = ensureObject(j);
    const sense = ensureObject(status.sense);
    tempEl.textContent = formatReading(sense.temperature);
    humEl.textContent = formatReading(sense.humidity);
    presEl.textContent = formatReading(sense.pressure);
    senseAvail.textContent = sense.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
    const motionValue = ensureArray(status.motion);
    motionEl.textContent = motionValue.slice(-50).join('\n');
    const modeValue = hasOwn(status, 'mode') ? status.mode : undefined;
    const displaySource = isPresent(modeValue) ? modeValue : '--';
    const modeLabel = typeof displaySource === 'string' ? displaySource : String(displaySource);
    modeEl.textContent = 'Mode: ' + modeLabel;

    const rawModeSource = isPresent(modeValue) ? modeValue : 'IDLE';
    const rawModeString = typeof rawModeSource === 'string' ? rawModeSource : String(rawModeSource);
    const state = rawModeString.toLowerCase();
    const activityCandidate = hasOwn(status, 'activity_level') ? status.activity_level : undefined;
    const activity = isPresent(activityCandidate) ? activityCandidate : 0;
    setCorgi(state, activity);
  }catch(e){
    console.error(e);
  }
}

async function initWS(){
  try{
    const ws = new WebSocket((location.protocol==='https:'?'wss':'ws')+'://'+location.host+'/ws');
    ws.onmessage = (ev)=>{
      const j = JSON.parse(ev.data);
      const message = ensureObject(j);
      if(message.kind==='tick'){
        const payload = ensureObject(message.payload);
        const sense = ensureObject(payload.sense);
        tempEl.textContent = formatReading(sense.temperature);
        humEl.textContent = formatReading(sense.humidity);
        presEl.textContent = formatReading(sense.pressure);
        senseAvail.textContent = sense.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
        const motionValue = ensureArray(payload.motion);
        motionEl.textContent = motionValue.slice(-50).join('\n');
        const modeValue = hasOwn(payload, 'mode') ? payload.mode : undefined;
        const displaySource = isPresent(modeValue) ? modeValue : '--';
        const modeLabel = typeof displaySource === 'string' ? displaySource : String(displaySource);
        modeEl.textContent = 'Mode: ' + modeLabel;
        const rawModeSource = isPresent(modeValue) ? modeValue : 'IDLE';
        const modeString = typeof rawModeSource === 'string' ? rawModeSource : String(rawModeSource);
        const activityCandidate = hasOwn(payload, 'activity_level') ? payload.activity_level : undefined;
        const activity = isPresent(activityCandidate) ? activityCandidate : 0;
        setCorgi(modeString.toLowerCase(), activity);
      }
    };
    ws.onclose = ()=> setTimeout(initWS, 2000);
  }catch(e){
    console.error('WS init failed', e);
  }
}

refreshOnce();
initWS();
