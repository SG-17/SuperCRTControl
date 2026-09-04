	const COLORS = [
      '#e53935', '#1e88e5', '#43a047', '#fb8c00',
      '#8e24aa', '#00acc1', '#fdd835', '#6d4c41',
    ];

    const STORAGE_KEY = 'extronMatrixStates';
    const THEME_KEY   = 'extronMatrixTheme';

    const deviceStates = {};
    let currentDevice = null;

    // Theme
    function applyTheme(theme, refresh) {
      document.documentElement.setAttribute('data-theme', theme);
      const btn = document.getElementById('themeToggle');
      btn.textContent = theme === 'dark' ? '☀️' : '🌒';
      btn.title = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme';
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

    // Color Changing
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
                removeOutputFromCommitted(i);
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

    // Matrix switching
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
      const state = getState();
      if (state.pendingInput === null || state.pendingOutputs.size === 0) {
        alert('Select one input and at least one output');
        return;
      }

      let cmd = '';
      for (const out of state.pendingOutputs) {
        cmd += `${state.pendingInput}*${out}!`;
      }
      sendCommand(cmd);

      state.committed.delete(state.pendingInput);
      state.committed.set(state.pendingInput, {
        outputs: new Set(state.pendingOutputs),
        color: state.pendingColor,
      });

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