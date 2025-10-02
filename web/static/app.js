
const clock = document.getElementById('clock');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const motionEl = document.getElementById('motion');
const modeEl = document.getElementById('mode');
const corgi = document.getElementById('corgi');

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
  const next = (state || 'idle');
  corgi.classList.remove('idle','focus','break','alert');
  corgi.classList.add(next);
  corgi.src = dogUrl(next, activity);
  corgi.dataset.mode = next;
}

async function refreshOnce(){
  try{
    const r = await fetch('/api/status');
    const j = await r.json();
    const s = j && j.sense ? j.sense : {};
    const tempValue = s.temperature;
    const humValue = s.humidity;
    const presValue = s.pressure;
    tempEl.textContent = tempValue !== undefined && tempValue !== null && tempValue.toFixed ? tempValue.toFixed(1) : '--';
    humEl.textContent = humValue !== undefined && humValue !== null && humValue.toFixed ? humValue.toFixed(1) : '--';
    presEl.textContent = presValue !== undefined && presValue !== null && presValue.toFixed ? presValue.toFixed(1) : '--';
    senseAvail.textContent = s.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
    const motionValue = j && j.motion ? j.motion : [];
    motionEl.textContent = motionValue.slice(-50).join('\n');
    const modeText = j && Object.prototype.hasOwnProperty.call(j, 'mode') ? j.mode : undefined;
    modeEl.textContent = 'Mode: ' + modeText;

    const rawMode = j && j.mode ? j.mode : 'IDLE';
    const state = rawMode.toLowerCase();
    const activity = j && j.activity_level !== undefined && j.activity_level !== null ? j.activity_level : 0;
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
      if(j && j.kind==='tick'){
        const s = j.payload ? j.payload : {};
        const sense = s && s.sense ? s.sense : {};
        const tempValue = sense.temperature;
        const humValue = sense.humidity;
        const presValue = sense.pressure;
        tempEl.textContent = tempValue !== undefined && tempValue !== null && tempValue.toFixed ? tempValue.toFixed(1) : '--';
        humEl.textContent = humValue !== undefined && humValue !== null && humValue.toFixed ? humValue.toFixed(1) : '--';
        presEl.textContent = presValue !== undefined && presValue !== null && presValue.toFixed ? presValue.toFixed(1) : '--';
        senseAvail.textContent = sense.available ? 'Sense HAT ✓' : 'Sense HAT unavailable';
        const motionValue = s && s.motion ? s.motion : [];
        motionEl.textContent = motionValue.slice(-50).join('\n');
        const modeText = s && Object.prototype.hasOwnProperty.call(s, 'mode') ? s.mode : undefined;
        modeEl.textContent = 'Mode: ' + modeText;
        const modeRaw = s && s.mode ? s.mode : 'IDLE';
        const activity = s && s.activity_level !== undefined && s.activity_level !== null ? s.activity_level : 0;
        setCorgi(modeRaw.toLowerCase(), activity);
      }
    };
    ws.onclose = ()=> setTimeout(initWS, 2000);
  }catch(e){
    console.error('WS init failed', e);
  }
}

refreshOnce();
initWS();
