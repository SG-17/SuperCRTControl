const COLORS = [
  '#e53935', '#1e88e5', '#43a047', '#fb8c00',
  '#8e24aa', '#00acc1', '#fdd835', '#6d4c41',
];

const STORAGE_KEY = 'extronMatrixStates';
const THEME_KEY   = 'extronMatrixTheme';

const deviceStates = {};
let currentDevice = null;

// Mode flags
let videoOn      = true;
let audioOn      = true;
let presetOn     = false;
let savePresetOn = false;

// Theme
function applyTheme(theme, refresh) {
  document.documentElement.setAttribute('data-theme', theme);
  const btn = document.getElementById('themeToggle');
  if (btn) {
    btn.textContent = theme === 'dark' ? '☀️' : '🌒';
    btn.title = theme === 'dark' ? 'Switch to Light Theme' : 'Switch to Dark Theme';
  }
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

function fullscreen() {
    var el = document.documentElement
    , rfs = // for newer Webkit and Firefox
       el.requestFullScreen
    || el.webkitRequestFullScreen
    || el.mozRequestFullScreen
    || el.msRequestFullScreen
    ;

    if(typeof rfs!="undefined" && rfs){

        rfs.call(el);

    } else if(typeof window.ActiveXObject!="undefined"){

        // for Internet Explorer
        var wscript = new ActiveXObject("WScript.Shell");

        if (wscript!=null) {
          wscript.SendKeys("{F11}");
        }
    }

}

if (window.self !== window.top) {
    document.documentElement.classList.add('in-iframe');
}
if (window.self == window.top) {
    document.documentElement.classList.add('not-in-iframe');
}

// Mode Text
function updateModeHint() {
  const el = document.getElementById('modeHint');
  if (!el) return;
  const parts = [];
  if (savePresetOn) {
    parts.push(
      'Save Preset — Click a numbered button to save current ties in that slot. ' +
      'Will overwrite any preset saved in the same slot'
    );
  } else {
    if (videoOn && audioOn) parts.push('Video + Audio');
    else if (videoOn) parts.push('Video Only');
    else if (audioOn) parts.push('Audio Only');
    parts.push(presetOn ? 'Preset On — Click an I/O button to recall' : 'Preset Off');
  }
  el.textContent = 'Mode: ' + parts.join('. ') + '.';
}

function syncModeButtons() {
  const v = document.getElementById('btnVideo');
  const a = document.getElementById('btnAudio');
  const p = document.getElementById('btnPreset');
  if (v) v.classList.toggle('on', videoOn);
  if (a) a.classList.toggle('on', audioOn);
  if (p) p.classList.toggle('preset-on', presetOn);
  updateModeHint();
  updateSavePresetButton();
}

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
  if (!currentDevice || savePresetOn) return;
  const state = getState();
  const borderDefault = getComputedStyle(document.documentElement)
    .getPropertyValue('--border').trim() || '#555';

  document.querySelectorAll('button.io').forEach(btn => {
    btn.classList.remove('blinking', 'slow-blink');
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

// Save Preset Mode
function hasActiveTies() {
  if (!currentDevice) return false;
  return getState().committed.size > 0;
}

function updateSavePresetButton() {
  const btn = document.getElementById('btnSavePreset');
  if (!btn) return;
  btn.disabled = !hasActiveTies() || presetOn;
  btn.classList.toggle('save-on', savePresetOn);
}

function exitSavePresetMode() {
  if (!savePresetOn) return;
  savePresetOn = false;
  buildButtons();
  updateSavePresetButton();
  updateModeHint();
}

function enterSavePresetMode() {
  if (!hasActiveTies()) return;
  savePresetOn = true;
  presetOn = false;
  applySavePresetButtonLabels();
  updateSavePresetButton();
  syncModeButtons();
  updateModeHint();
}

function applySavePresetButtonLabels() {
  const dev = currentDevice;
  const flashColor = '#8e24aa';

  document.querySelectorAll('#inputs button.io').forEach(btn => {
    const n = Number(btn.dataset.num);
    btn.classList.remove('blinking');
    btn.classList.add('slow-blink');
    btn.style.borderColor = flashColor;
    btn.style.background = '#ffffff';
    btn.style.color = '#000000';
    btn.innerHTML = '';
    btn.textContent = String(n);
    btn.classList.remove('img-btn');
  });

  document.querySelectorAll('#outputs button.io').forEach(btn => {
    const n = Number(btn.dataset.num);
    const presetNum = dev.numInputs + n;
    btn.classList.remove('blinking');
    btn.classList.add('slow-blink');
    btn.style.borderColor = flashColor;
    btn.style.background = '#ffffff';
    btn.style.color = '#000000';
    btn.innerHTML = '';
    btn.textContent = String(presetNum);
    btn.classList.remove('img-btn');
  });
}

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

        if (savePresetOn) {
          const n = Number(btn.dataset.num);
          const pnum = isInput ? n : (currentDevice.numInputs + n);
          sendCommand(pnum + ','); 
          setStatus(
            `Saved current ties to preset ${pnum}`
          );
          exitSavePresetMode();
          return;
        }

        if (presetOn) {
          const pnum = presetNumberForButton(isInput, i);
          sendCommand(pnum + '.');
          setStatus(
            `Recalled preset ${pnum} via ${isInput ? 'input' : 'output'} ${i}`
          );
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
  exitSavePresetMode();
  getState();
  buildButtons();
  setStatus(`Active device: ${currentDevice.name} (${currentDevice.ip})`);
  updateSavePresetButton();
  try { localStorage.setItem(STORAGE_KEY + '_lastDevice', name); } catch (_) {}
}

// Commands
function setStatus(msg) {
  const el = document.getElementById('status');
  if (el) el.textContent = msg;
}

function sendCommand(cmd) {
  if (!currentDevice) return;
  const ip = currentDevice.ip;
  const url = `http://${ip}/?cmd=${encodeURIComponent(cmd)}`;
  const frame = document.querySelector('iframe[name="cmdFrame"]');
  if (frame) frame.src = url;
  setStatus(
    `Device: ${currentDevice.name}\nCommand sent:\n${cmd}\n\nURL: ${url}`
  );
}

// Init
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  loadAllStates();

  document.getElementById('themeToggle')?.addEventListener('click', () => {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark', true);
  });

  document.getElementById('btnVideo')?.addEventListener('click', () => {
    if (videoOn && !audioOn) return;
    videoOn = !videoOn;
    syncModeButtons();
  });

  document.getElementById('btnAudio')?.addEventListener('click', () => {
    if (audioOn && !videoOn) return;
    audioOn = !audioOn;
    syncModeButtons();
  });

  document.getElementById('btnPreset')?.addEventListener('click', () => {
    if (savePresetOn) exitSavePresetMode();
    presetOn = !presetOn;
    syncModeButtons();
  });

  document.getElementById('btnSavePreset')?.addEventListener('click', () => {
    if (savePresetOn) {
      exitSavePresetMode();
      return;
    }
    if (!hasActiveTies()) return;
    enterSavePresetMode();
  });

  document.getElementById('clearSel')?.addEventListener('click', () => {
    const state = getState();
    state.pendingInput = null;
    state.pendingOutputs.clear();
    refreshAllVisuals();
    saveAllStates();
    setStatus('');
  });

  document.getElementById('execute')?.addEventListener('click', () => {
    if (presetOn) {
      alert('Turn off Preset mode to create ties.');
      return;
    }
    if (savePresetOn) {
      alert('Finish or cancel Save Preset first.');
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
    updateSavePresetButton();
  });

  document.getElementById('clearAll')?.addEventListener('click', () => {
    sendCommand('0*!');
    const state = getState();
    state.committed.clear();
    state.pendingInput = null;
    state.pendingOutputs.clear();
    exitSavePresetMode();
    refreshAllVisuals();
    saveAllStates();
    updateSavePresetButton();
  });

  const select = document.getElementById('deviceSelect');
  if (select) {
    DEVICES.forEach(d => {
      const opt = document.createElement('option');
      opt.value = d.name;
      opt.textContent = d.name;
      select.appendChild(opt);
    });
    select.addEventListener('change', () => switchDevice(select.value));

    let startName = DEVICES[0] ? DEVICES[0].name : null;
    try {
      const last = localStorage.getItem(STORAGE_KEY + '_lastDevice');
      if (last && DEVICES.some(d => d.name === last)) startName = last;
    } catch (_) {}

    if (startName) {
      select.value = startName;
      switchDevice(startName);
    }
  }

  syncModeButtons();
});