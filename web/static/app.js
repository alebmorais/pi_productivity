
const clock = document.getElementById('clock');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const motionEl = document.getElementById('motion');
const modeEl = document.getElementById('mode');
const corgi = document.getElementById('corgi');

function dogUrl(state, activity){
  const mode = encodeURIComponent(state ?? 'idle');
  let act = Number(activity ?? 0);
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
  const next = (state || 'idle');
  corgi.classList.remove('idle','focus','break','alert');
  corgi.classList.add(next);
  corgi.src = dogUrl(next, activity);
  corgi.dataset.mode = next;
}

async function refreshOnce(){
  try{
    const r = await fetch('/api/status');
    if(!r.ok){
      console.error('Status fetch failed', r.status, r.statusText);
      return;
    }
    const j = await r.json();
    const sense = (j && j.sense) ? j.sense : {};
    tempEl.textContent = ('temperature' in sense && sense.temperature != null) ? Number(sense.temperature).toFixed(1) : '--';
    humEl.textContent = ('humidity' in sense && sense.humidity != null) ? Number(sense.humidity).toFixed(1) : '--';
    presEl.textContent = ('pressure' in sense && sense.pressure != null) ? Number(sense.pressure).toFixed(1) : '--';
    senseAvail.textContent = sense.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
    const motionLines = Array.isArray(j?.motion) ? j.motion : [];
    motionEl.textContent = motionLines.slice(-50).join('\n');
    const rawMode = (j && Object.prototype.hasOwnProperty.call(j, 'mode')) ? j.mode : undefined;
    const mode = rawMode != null ? String(rawMode) : 'UNKNOWN';
    modeEl.textContent = 'Mode: ' + mode;

    const stateCandidate = mode.toLowerCase();
    const validStates = ['idle','focus','break','alert'];
    const state = validStates.includes(stateCandidate) ? stateCandidate : 'idle';
    let activity = ('activity_level' in (j||{})) && j.activity_level != null ? Number(j.activity_level) : 0;
    if(!Number.isFinite(activity)){ activity = 0; }
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
      if(j.kind==='tick'){
        const payload = j.payload || {};
        const sense = payload.sense || {};
        tempEl.textContent = ('temperature' in sense && sense.temperature != null) ? Number(sense.temperature).toFixed(1) : '--';
        humEl.textContent = ('humidity' in sense && sense.humidity != null) ? Number(sense.humidity).toFixed(1) : '--';
        presEl.textContent = ('pressure' in sense && sense.pressure != null) ? Number(sense.pressure).toFixed(1) : '--';
        senseAvail.textContent = sense.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
        const motionLines = Array.isArray(payload.motion) ? payload.motion : [];
        motionEl.textContent = motionLines.slice(-50).join('\n');
        const rawMode = Object.prototype.hasOwnProperty.call(payload, 'mode') ? payload.mode : undefined;
        const mode = rawMode != null ? String(rawMode) : 'UNKNOWN';
        modeEl.textContent = 'Mode: ' + mode;
        let activity = ('activity_level' in payload && payload.activity_level != null) ? Number(payload.activity_level) : 0;
        if(!Number.isFinite(activity)){ activity = 0; }
        const stateCandidate = mode.toLowerCase();
        const validStates = ['idle','focus','break','alert'];
        const state = validStates.includes(stateCandidate) ? stateCandidate : 'idle';
        setCorgi(state, activity);
      }
    };
    ws.onclose = ()=> setTimeout(initWS, 2000);
  }catch(e){
    console.error('WS init failed', e);
  }
}

refreshOnce();
initWS();
