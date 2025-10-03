const clock = document.getElementById('clock');
const modeEl = document.getElementById('mode');
const presetButtons = Array.from(document.querySelectorAll('[data-mode-btn]'));
const presetStatus = document.getElementById('presetStatus');
const tempEl = document.getElementById('temp');
const humEl = document.getElementById('hum');
const presEl = document.getElementById('pres');
const senseAvail = document.getElementById('senseAvail');
const postureEventsEl = document.getElementById('postureEvents');
const postureAdjustEl = document.getElementById('postureAdjust');
const postureListEl = document.getElementById('postureRecent');
const tasksTotalEl = document.getElementById('tasksTotal');
const tasksCompletedEl = document.getElementById('tasksCompleted');
const tasksCreatedEl = document.getElementById('tasksCreated');
const tasksListEl = document.getElementById('tasksRecent');
const motionEl = document.getElementById('motion');
const motionSourceEl = document.getElementById('motionSource');
const camEl = document.getElementById('cam');

const VALID_MODES = ['idle', 'focus', 'break', 'alert'];

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
    label: normalized.charAt(0).toUpperCase() + normalized.slice(1)
  };
}

function formatNumber(value){
  const num = Number(value);
  if(!Number.isFinite(num)){
    return '--';
  }
  return num.toFixed(1);
}

function formatInt(value){
  const num = Number.parseInt(value, 10);
  if(!Number.isFinite(num)){
    return '0';
  }
  return String(num);
}

function formatTimestamp(value){
  if(!value){
    return '—';
  }
  const parsed = new Date(value);
  if(Number.isNaN(parsed.getTime())){
    return String(value);
  }
  return parsed.toLocaleString();
}

function tickClock(){
  const now = new Date();
  clock.textContent = now.toLocaleString();
}

function setPresetStatus(message = '', isError = false){
  if(!presetStatus){
    return;
  }
  presetStatus.textContent = message;
  presetStatus.classList.toggle('error', Boolean(isError));
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

function updateModeDisplay(modeValue){
  const info = describeMode(modeValue);
  if(modeEl){
    modeEl.textContent = `Modo: ${info.label}`;
  }
  return info.normalized;
}

function updateSense(senseData){
  const sense = ensureObject(senseData);
  tempEl.textContent = formatNumber(sense.temperature);
  humEl.textContent = formatNumber(sense.humidity);
  presEl.textContent = formatNumber(sense.pressure);

  if(sense.available){
    senseAvail.textContent = 'Sense HAT disponível';
  }else if(hasOwn(sense, 'error') && isPresent(sense.error)){
    senseAvail.textContent = String(sense.error);
  }else{
    senseAvail.textContent = 'Sense HAT indisponível';
  }
}

function renderList(element, items, fallbackText, decorate){
  if(!element){
    return;
  }
  element.textContent = '';
  if(!items.length){
    const li = document.createElement('li');
    li.className = 'event-item empty';
    li.textContent = fallbackText;
    element.appendChild(li);
    return;
  }
  for(const item of items){
    const li = document.createElement('li');
    li.className = 'event-item';
    decorate(li, item);
    element.appendChild(li);
  }
}

function updatePosture(data){
  const info = ensureObject(data);
  postureEventsEl.textContent = formatInt(info.total_events);
  postureAdjustEl.textContent = formatInt(info.adjustments);
  const items = ensureArray(info.recent);
  renderList(postureListEl, items, 'Nenhum evento recente.', (li, entry)=>{
    const ok = Boolean(entry && entry.ok);
    const ts = formatTimestamp(entry && entry.timestamp);
    const reason = entry && entry.reason ? ` · ${entry.reason}` : '';
    const tilt = entry && Number.isFinite(Number(entry.tilt)) ? ` · tilt ${Number(entry.tilt).toFixed(1)}°` : '';
    const nod = entry && Number.isFinite(Number(entry.nod)) ? ` · nod ${Number(entry.nod).toFixed(1)}°` : '';
    li.textContent = `${ts} • ${ok ? 'OK' : 'Ajuste'}${reason}${tilt}${nod}`;
    if(!ok){
      li.classList.add('warn');
    }
  });
}

function updateTasks(data){
  const info = ensureObject(data);
  tasksTotalEl.textContent = formatInt(info.total_events);
  tasksCompletedEl.textContent = formatInt(info.completed);
  tasksCreatedEl.textContent = formatInt(info.created);
  const items = ensureArray(info.recent);
  renderList(tasksListEl, items, 'Nenhum evento recente.', (li, entry)=>{
    const ts = formatTimestamp(entry && entry.timestamp);
    const action = entry && entry.action ? String(entry.action).toUpperCase() : 'EVENTO';
    const section = entry && entry.section_title ? ` · ${entry.section_title}` : '';
    const name = entry && entry.task_name ? ` — ${entry.task_name}` : '';
    li.textContent = `${ts} • ${action}${section}${name}`;
  });
}

function updateMotion(lines, source){
  const list = ensureArray(lines).map((item)=>String(item));
  motionEl.textContent = list.length ? list.join('\n') : 'Nenhum evento recente do Motion.';
  if(motionSourceEl){
    motionSourceEl.textContent = source ? `Fonte: ${source}` : '';
  }
}

function refreshCamera(){
  if(!camEl){
    return;
  }
  const base = '/camera.jpg';
  camEl.src = `${base}?ts=${Date.now()}`;
}

function applyStatus(payload){
  if(!payload || typeof payload !== 'object'){
    return;
  }
  const normalizedMode = updateModeDisplay(payload.mode);
  updatePresetButtons(normalizedMode);
  updateSense(payload.sense);
  updatePosture(payload.posture);
  updateTasks(payload.tasks);
  updateMotion(payload.motion, payload.motion_source);
  refreshCamera();
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
  }catch(err){
    console.error('Initial refresh failed', err);
  }
}

function handleEnvelope(message){
  if(!message){
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

updateModeDisplay('idle');
updatePresetButtons('idle');
setPresetStatus('');
bindPresetButtons();

updateSense({});
updatePosture({});
updateTasks({});
updateMotion([], '');
refreshCamera();

tickClock();
setInterval(tickClock, 500);
refreshOnce();
initWS();
