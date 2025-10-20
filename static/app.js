document.addEventListener('DOMContentLoaded', () => {
    const clockEl = document.getElementById('clock');
    const modeDisplayEl = document.getElementById('mode-display');
    const tempEl = document.getElementById('temp');
    const humEl = document.getElementById('hum');
    const presEl = document.getElementById('pres');
    const senseAvailEl = document.getElementById('senseAvail');
    const taskContainerEl = document.getElementById('task-container');
    const senseForm = document.getElementById('sense-form');
    const modeSelect = document.getElementById('mode-select');
    const presetStatusEl = document.getElementById('presetStatus');
    const ocrButton = document.getElementById('ocr-button');

    function formatNumber(value, decimals = 1) {
        const num = Number(value);
        return !Number.isFinite(num) ? '--' : num.toFixed(decimals);
    }

    function tickClock() {
        if (clockEl) {
            clockEl.textContent = new Date().toLocaleTimeString();
        }
    }

    function refreshCamera() {
        const cam = document.getElementById('cam');
        if (cam) {
            cam.src = `/camera.jpg?_ts=${Date.now()}`;
        }
    }

    function updateSense(sense) {
        if (!sense) return;
        if (tempEl) tempEl.textContent = formatNumber(sense.temperature);
        if (humEl) humEl.textContent = formatNumber(sense.humidity);
        if (presEl) presEl.textContent = formatNumber(sense.pressure, 0);
        if (senseAvailEl) {
            senseAvailEl.textContent = sense.available ? 'Sense HAT Available' : (sense.error || 'Sense HAT not detected');
            senseAvailEl.className = `availability ${sense.available ? 'success' : 'error'}`;
        }
    }

    function updateTasks(tasks) {
        if (!taskContainerEl) return;
        const list = document.createElement('ul');
        list.className = 'task-list';

        if (!tasks || tasks.length === 0) {
            const li = document.createElement('li');
            li.className = 'task-item empty';
            li.textContent = 'No pending tasks. Great job!';
            list.appendChild(li);
        } else {
            tasks.forEach((task) => {
                const li = document.createElement('li');
                li.className = 'task-item';

                // Form (encode task_id to avoid path injection)
                const form = document.createElement('form');
                form.className = 'complete-form';
                form.method = 'post';
                const taskId = task && task.task_id != null ? String(task.task_id) : '';
                form.action = `/complete_task/${encodeURIComponent(taskId)}`;

                const button = document.createElement('button');
                button.type = 'submit';
                button.textContent = '✅';
                form.appendChild(button);

                // Title span
                const span = document.createElement('span');
                const title = task && task.title != null ? String(task.title) : '';
                span.textContent = title;

                // Tooltip subtitle (attribute value, not HTML)
                if (task && task.subtitle != null && task.subtitle !== '') {
                    span.setAttribute('title', String(task.subtitle));
                }

                li.appendChild(form);
                li.appendChild(span);

                // Optional right-side note
                if (task && task.right != null && task.right !== '') {
                    const small = document.createElement('small');
                    small.textContent = `(${String(task.right)})`;
                    li.appendChild(small);
                }

                list.appendChild(li);
            });
        }
        taskContainerEl.innerHTML = '';
        taskContainerEl.appendChild(list);
    }
    
    function updateMode(modeName) {
        if (modeDisplayEl) {
            modeDisplayEl.textContent = `Mode: ${modeName.replace(/_/g, ' ')}`;
            modeDisplayEl.className = `mode-pill mode-${modeName}`;
        }
        if (modeSelect) {
            modeSelect.value = modeName;
        }
    }

    function applyStatus(payload) {
        if (!payload || typeof payload !== 'object') return;
        updateMode(payload.mode || 'none');
        updateSense(payload.sense);
        updateTasks(payload.tasks);
    }

    async function initWS() {
        const protocol = location.protocol === 'https:' ? 'wss' : 'ws';
        const ws = new WebSocket(`${protocol}://${location.host}/ws`);

        ws.onmessage = (event) => {
            try {
                const message = JSON.parse(event.data);
                if (message.kind === 'tick') {
                    applyStatus(message.payload);
                }
            } catch (err) {
                console.error('Failed to parse WebSocket message', err);
            }
        };

        ws.onclose = () => setTimeout(initWS, 3000);
        ws.onerror = () => ws.close();
    }

    if (senseForm) {
        senseForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (presetStatusEl) presetStatusEl.textContent = 'Setting mode...';
            try {
                const formData = new FormData(senseForm);
                const response = await fetch('/sense/mode', { method: 'POST', body: formData });
                const data = await response.json();
                if (data.status === 'success') {
                    if (presetStatusEl) presetStatusEl.textContent = `Mode set to ${data.mode}.`;
                    updateMode(data.mode);
                } else {
                    throw new Error(data.message || 'Unknown error');
                }
            } catch (err) {
                if (presetStatusEl) presetStatusEl.textContent = `Error: ${err.message}`;
            }
        });
    }

    if (ocrButton) {
        ocrButton.addEventListener('click', async () => {
            ocrButton.textContent = 'Capturing...';
            ocrButton.disabled = true;
            try {
                const response = await fetch('/ocr', { method: 'POST' });
                const data = await response.json();
                if (data.status === 'success') {
                    alert(`Note captured:\n\n${data.text}`);
                } else {
                    throw new Error(data.message || 'OCR failed');
                }
            } catch (err) {
                alert(`Error during OCR: ${err.message}`);
            } finally {
                ocrButton.textContent = 'Capture Note (OCR)';
                ocrButton.disabled = false;
            }
        });
    }

    tickClock();
    setInterval(tickClock, 1000);
    setInterval(refreshCamera, 2000);
    initWS();
});
