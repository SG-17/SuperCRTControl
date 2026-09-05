const COLORS = [
      '#e53935', '#1e88e5', '#43a047', '#fb8c00',
      '#8e24aa', '#00acc1', '#fdd835', '#6d4c41',
    ];

    const STORAGE_KEY = 'extronMatrixStates';
    const THEME_KEY   = 'extronMatrixTheme';

    const deviceStates = {};
    let currentDevice = null;
    let videoOn  = true;
    let audioOn  = true;
    let presetOn = false;

    // Theme
    function applyTheme(theme, refresh) {
      document.documentElement.setAttribute('data-theme', theme);
      const btn = document.getElementById('themeToggle');
      btn.textContent = theme === 'dark' ? '☀️' : '🌒';
      btn.title = theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme';
      try { localStorage.setItem(THEME_KEY, theme); } catch (_) {}
      if (refresh && currentDevice) refreshAllVisuals();
    }

    function initTheme() {
      let theme = 'light';
      try {
        const saved = localStorage.getItem(THEME_KEY);
        if (saved === 'dark' || saved === 'light') theme = saved;
        else if (window.matchMedia('(prefers-color-scheme: dark)').matches) theme = 'dark';
      } catch (_) {}
      applyTheme(theme, false);
    }

    document.getElementById('themeToggle').addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      applyTheme(current === 'dark' ? 'light' : 'dark', true);
    });

    // Mode buttons
    function updateModeHint() {
      const parts = [];
      if (videoOn && audioOn) parts.push('Video + Audio');
      else if (videoOn) parts.push('Video Only');
      else if (audioOn) parts.push('Audio Only');
      parts.push(presetOn ? '  Preset On — Click an I/O button to recall' : '  Preset Off');
      document.getElementById('modeHint').textContent = 'Mode: ' + parts.join(' -- ');
    }

    function syncModeButtons() {
      document.getElementById('btnVideo').classList.toggle('on', videoOn);
      document.getElementById('btnAudio').classList.toggle('on', audioOn);
      document.getElementById('btnPreset').classList.toggle('preset-on', presetOn);
      updateModeHint();
    }

    document.getElementById('btnVideo').addEventListener('click', () => {
      if (videoOn && !audioOn) return;
      videoOn = !videoOn;
      syncModeButtons();
    });

    document.getElementById('btnAudio').addEventListener('click', () => {
      if (audioOn && !videoOn) return;
      audioOn = !audioOn;
      syncModeButtons();
    });

    document.getElementById('btnPreset').addEventListener('click', () => {
      presetOn = !presetOn;
      syncModeButtons();
    });

    function tieTerminator() {
      if (videoOn && audioOn) return '!';
      if (videoOn) return '%'; 
      return '$';
    }

    // localStorage
    function serializeState(state) {
      const committedObj = {};
      state.committed.forEach((data, inp) => {
        committedObj[inp] = {
          outputs: [...data.outputs],
          color: data.color,
        };
      });
      return {
        pendingInput: state.pendingInput,
        pendingOutputs: [...state.pendingOutputs],
        pendingColor: state.pendingColor,
        committed: committedObj,
      };
    }

    function deserializeState(raw) {
      const committed = new Map();
      if (raw.committed) {
        Object.entries(raw.committed).forEach(([inp, data]) => {
          committed.set(Number(inp), {
            outputs: new Set(data.outputs || []),
            color: data.color || 0,
          });
        });
      }
      return {
        pendingInput: raw.pendingInput ?? null,
        pendingOutputs: new Set(raw.pendingOutputs || []),
        pendingColor: raw.pendingColor || 0,
        committed,
      };
    }

    function loadAllStates() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (!raw) return;
        const parsed = JSON.parse(raw);
        Object.entries(parsed).forEach(([name, data]) => {
          deviceStates[name] = deserializeState(data);
        });
      } catch (e) {
        console.warn('Could not load saved states', e);
      }
    }

    function saveAllStates() {
      try {
        const toSave = {};
        Object.entries(deviceStates).forEach(([name, state]) => {
          toSave[name] = serializeState(state);
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
      } catch (e) {
        console.warn('Could not save states', e);
      }
    }

    function getState() {
      if (!deviceStates[currentDevice.name]) {
        deviceStates[currentDevice.name] = {
          pendingInput: null,
          pendingOutputs: new Set(),
          pendingColor: 0,
          committed: new Map(),
        };
      }
      return deviceStates[currentDevice.name];
    }

    // Visuals
    function getButton(containerId, num) {
      return document.querySelector(`#${containerId} button[data-num="${num}"]`);
    }

    function refreshAllVisuals() {
      if (!currentDevice) return;
      const state = getState();
      const borderDefault = getComputedStyle(document.documentElement)
        .getPropertyValue('--border').trim() || '#555';

      document.querySelectorAll('button.io').forEach(btn => {
        btn.classList.remove('blinking');
        btn.style.borderColor = borderDefault;
        btn.style.background  = '#ffffff';
        btn.style.color       = '#000000';
      });

      state.committed.forEach((data, inp) => {
        const color = COLORS[data.color % COLORS.length];
        const inBtn = getButton('inputs', inp);
        if (inBtn) {
          inBtn.style.borderColor = color;
          if (!inBtn.classList.contains('img-btn')) {
            inBtn.style.background = color;
            inBtn.style.color = '#fff';
          }
        }
        data.outputs.forEach(o => {
          const outBtn = getButton('outputs', o);
          if (outBtn) {
            outBtn.style.borderColor = color;
            if (!outBtn.classList.contains('img-btn')) {
              outBtn.style.background = color;
              outBtn.style.color = '#fff';
            }
          }
        });
      });

      if (state.pendingInput !== null) {
        const color = COLORS[state.pendingColor % COLORS.length];
        const inBtn = getButton('inputs', state.pendingInput);
        if (inBtn) {
          inBtn.style.borderColor = color;
          inBtn.classList.add('blinking');
          if (!inBtn.classList.contains('img-btn')) {
            inBtn.style.background = color;
            inBtn.style.color = '#fff';
          }
        }
        state.pendingOutputs.forEach(o => {
          const outBtn = getButton('outputs', o);
          if (outBtn) {
            outBtn.style.borderColor = color;
            outBtn.classList.add('blinking');
            if (!outBtn.classList.contains('img-btn')) {
              outBtn.style.background = color;
              outBtn.style.color = '#fff';
            }
          }
        });
      }
    }

    function removeOutputFromCommitted(out) {
      const state = getState();
      for (const [inp, data] of state.committed) {
        if (data.outputs.has(out)) {
          data.outputs.delete(out);
          if (data.outputs.size === 0) state.committed.delete(inp);
          return;
        }
      }
    }

    // Preset numbers
    function presetNumberForButton(isInput, num) {
      if (isInput) return num;
      return currentDevice.numInputs + num;
    }

    // Buttons
    function buildButtons() {
      const inputsEl  = document.getElementById('inputs');
      const outputsEl = document.getElementById('outputs');
      inputsEl.innerHTML  = '';
      outputsEl.innerHTML = '';

      const dev = currentDevice;

      function make(container, count, isInput) {
        const imageMap = isInput ? (dev.inputImages || {}) : (dev.outputImages || {});
        const dir = dev.imageDir || '/images/';

        for (let i = 1; i <= count; i++) {
          const btn = document.createElement('button');
          btn.className = 'io';
          btn.dataset.num = i;

          const filename = imageMap[i];
          if (filename) {
            btn.classList.add('img-btn');
            const img = document.createElement('img');
            img.src = dir + filename;
            img.alt = i;
            btn.appendChild(img);
          } else {
            btn.textContent = i;
          }

          btn.addEventListener('click', () => {
            if (presetOn) {
              const pnum = presetNumberForButton(isInput, i);
              sendCommand(pnum + '.');
              document.getElementById('status').textContent +=
                `\n(Recalled preset ${pnum} via ${isInput ? 'input' : 'output'} ${i})`;
              presetOn = false;
              syncModeButtons();
              return;
            }

            const state = getState();
            if (isInput) {
              if (state.pendingInput === i) {
                state.pendingInput = null;
                state.pendingOutputs.clear();
              } else {
                state.pendingInput = i;
                state.pendingOutputs.clear();
                state.pendingColor = (state.pendingColor + 1) % COLORS.length;
              }
            } else {
              if (state.pendingInput === null) return;
              if (state.pendingOutputs.has(i)) {
                state.pendingOutputs.delete(i);
              } else {
                if (videoOn && audioOn) {
                  removeOutputFromCommitted(i);
                }
                state.pendingOutputs.add(i);
              }
            }
            refreshAllVisuals();
            saveAllStates();
          });

          container.appendChild(btn);
        }
      }

      make(inputsEl,  dev.numInputs,  true);
      make(outputsEl, dev.numOutputs, false);
      refreshAllVisuals();
    }

    // Device switching
    function switchDevice(name) {
      currentDevice = DEVICES.find(d => d.name === name);
      if (!currentDevice) return;
      getState();
      buildButtons();
      document.getElementById('status').textContent =
        `Active device: ${currentDevice.name} (${currentDevice.ip})`;
      try { localStorage.setItem(STORAGE_KEY + '_lastDevice', name); } catch (_) {}
    }

    // Commands
    function sendCommand(cmd) {
      const ip = currentDevice.ip;
      const url = `http://${ip}/?cmd=${encodeURIComponent(cmd)}`;
      document.querySelector('iframe[name="cmdFrame"]').src = url;
      document.getElementById('status').textContent =
        `Device: ${currentDevice.name}\nCommand sent:\n${cmd}\n\nURL: ${url}`;
    }

    document.getElementById('clearSel').addEventListener('click', () => {
      const state = getState();
      state.pendingInput = null;
      state.pendingOutputs.clear();
      refreshAllVisuals();
      saveAllStates();
      document.getElementById('status').textContent = '';
    });

    document.getElementById('execute').addEventListener('click', () => {
      if (presetOn) {
        alert('Turn off Preset mode to create ties.');
        return;
      }
      const state = getState();
      if (state.pendingInput === null || state.pendingOutputs.size === 0) {
        alert('Select one input and at least one output');
        return;
      }

      const term = tieTerminator();
      let cmd = '';
      for (const out of state.pendingOutputs) {
        cmd += `${state.pendingInput}*${out}${term}`;
      }
      sendCommand(cmd);

      if (videoOn && audioOn) {
        state.committed.delete(state.pendingInput);
        for (const out of state.pendingOutputs) removeOutputFromCommitted(out);
        state.committed.set(state.pendingInput, {
          outputs: new Set(state.pendingOutputs),
          color: state.pendingColor,
        });
      } else {
        let entry = state.committed.get(state.pendingInput);
        if (!entry) {
          entry = { outputs: new Set(), color: state.pendingColor };
          state.committed.set(state.pendingInput, entry);
        }
        state.pendingOutputs.forEach(o => entry.outputs.add(o));
      }

      state.pendingInput = null;
      state.pendingOutputs.clear();
      refreshAllVisuals();
      saveAllStates();
    });

    document.getElementById('clearAll').addEventListener('click', () => {
      sendCommand('0*!');
      const state = getState();
      state.committed.clear();
      state.pendingInput = null;
      state.pendingOutputs.clear();
      refreshAllVisuals();
      saveAllStates();
    });

    initTheme();
    loadAllStates();
    syncModeButtons();

    const select = document.getElementById('deviceSelect');
    DEVICES.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.name;
      opt.textContent = d.name;
      select.appendChild(opt);
    });

    select.addEventListener('change', () => {
      switchDevice(select.value);
    });

    let startName = DEVICES[0] ? DEVICES[0].name : null;
    try {
      const last = localStorage.getItem(STORAGE_KEY + '_lastDevice');
      if (last && DEVICES.some(d => d.name === last)) startName = last;
    } catch (_) {}

    if (startName) {
      select.value = startName;
      switchDevice(startName);
    }
