/**
 * MANIM STUDIO — WORKFLOW INTEGRADO
 * - Animación manual con main.py ajustada a pantalla sin scroll inicial (consola abajo)
 * - Constructor de funciones estilo Scratch con renderizado en vivo
 * - Panel lateral izquierdo desplegable con acordeones colapsables por click
 * - Visualizador de documentación técnica (READMI.md)
 * - Cargador de plantillas matemáticas y selector de temas de alto contraste
 */

const state = {
  activeView: 'view-manual',
  activeFile: 'main.py',
  isRendering: false,
  isDirty: false,
  theme: localStorage.getItem('manim_theme') || 'blanco',
  quality: localStorage.getItem('manim_quality') || 'low_quality',
  scratchBlocks: [],
  docsLoaded: false,
  audio: {
    file: null,
    url: null,
    name: '',
    duration: 0,
    startOffset: 0.0,
    autoSync: true,
    isPlaying: false,
    isMuted: false,
    volume: 1.0
  }
};

// ==========================================================================
// 1. GESTIÓN DE PLANTILLAS
// El código de las plantillas se carga dinámicamente desde las carpetas del
// proyecto (Plantillas/Análisis numérico, Plantillas/Cálculo diferencial, etc.)
// a través del endpoint /api/get_template, asegurando sincronización con el disco.
// ==========================================================================
const TEMPLATES = {};

// ==========================================================================
// 2. INICIALIZACIÓN
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  initQuality();
  initEditor();
  initNavigation();
  initCollapsibleAccordions();
  initScratchSystem();
  initTemplatesModal();
  initAudioModule();
  initShortCreator();
  initEventListeners();
  initSSE();
  fetchLatestVideo();
  loadMainPy();
});

// ==========================================================================
// 3. SISTEMA DE TEMAS Y CALIDAD
// ==========================================================================
function initTheme() {
  const savedTheme = localStorage.getItem('manim_theme') || 'blanco';
  setTheme(savedTheme, false);
}

function setTheme(themeVal, notify = true) {
  state.theme = themeVal;
  localStorage.setItem('manim_theme', themeVal);
  document.body.setAttribute('data-theme', themeVal);

  document.querySelectorAll('.theme-card').forEach(card => {
    if (card.getAttribute('data-theme-val') === themeVal) {
      card.classList.add('active');
    } else {
      card.classList.remove('active');
    }
  });

  if (notify) {
    appendTerminalLine('system', `Tema activo: ${themeVal.toUpperCase()} (Lienzo negro de alto contraste)`);
  }
}

function initQuality() {
  const savedQuality = localStorage.getItem('manim_quality') || 'low_quality';
  state.quality = savedQuality;
  document.querySelectorAll(`input[name="manim-quality"], input[name="manim-quality-full"]`).forEach(radio => {
    if (radio.value === savedQuality) {
      radio.checked = true;
    }
  });
}

function setQuality(qualityVal) {
  state.quality = qualityVal;
  localStorage.setItem('manim_quality', qualityVal);
  document.querySelectorAll(`input[name="manim-quality"], input[name="manim-quality-full"]`).forEach(radio => {
    if (radio.value === qualityVal) {
      radio.checked = true;
    }
  });
  appendTerminalLine('system', `Calidad de render configurada a: ${qualityVal}`);
}

// ==========================================================================
// 4. NAVEGACIÓN Y VISTAS
// ==========================================================================
function initNavigation() {
  // Conectar botones del menú lateral
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const viewId = btn.getAttribute('data-view');
      switchView(viewId);
      closeLeftMenu();
    });
  });

  // Drawer izquierdo
  const btnToggle = document.getElementById('btn-toggle-left-menu');
  const btnClose = document.getElementById('btn-close-left-menu');
  const backdrop = document.getElementById('drawer-backdrop');

  if (btnToggle) btnToggle.addEventListener('click', toggleLeftMenu);
  if (btnClose) btnClose.addEventListener('click', closeLeftMenu);
  if (backdrop) backdrop.addEventListener('click', closeLeftMenu);
}

function toggleLeftMenu() {
  const drawer = document.getElementById('left-sidebar');
  const backdrop = document.getElementById('drawer-backdrop');
  const isOpen = drawer.classList.contains('open');
  if (isOpen) {
    closeLeftMenu();
  } else {
    drawer.classList.add('open');
    backdrop.classList.remove('hidden');
    backdrop.classList.add('active');
  }
}

function closeLeftMenu() {
  const drawer = document.getElementById('left-sidebar');
  const backdrop = document.getElementById('drawer-backdrop');
  if (drawer) drawer.classList.remove('open');
  if (backdrop) {
    backdrop.classList.remove('active');
    backdrop.classList.add('hidden');
  }
}

function switchView(viewId) {
  state.activeView = viewId;

  // Actualizar clases activas en views
  document.querySelectorAll('.app-view').forEach(view => {
    view.classList.remove('active');
  });
  const targetView = document.getElementById(viewId);
  if (targetView) targetView.classList.add('active');

  // Actualizar nav items
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.getAttribute('data-view') === viewId) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  // Actualizar etiqueta del header
  const tabLabel = document.getElementById('active-tab-label');
  const titles = {
    'view-manual': 'Animación manual',
    'view-scratch': 'Insertar funciones',
    'view-short': 'Creador de Shorts',
    'view-settings': 'Ajustes',
    'view-docs': 'Documentación'
  };
  if (tabLabel && titles[viewId]) {
    tabLabel.textContent = titles[viewId];
  }

  // Activar inicializador o refresco al entrar a view-short
  if (viewId === 'view-short') {
    onEnterShortView();
  }

  // Cargar documentación si se entra en view-docs
  if (viewId === 'view-docs' && !state.docsLoaded) {
    loadDocs();
  }
}

// ==========================================================================
// 5. ACORDEONES COLAPSABLES POR CLICK (LABELS EXPANDIBLES / CONTRAÍBLES)
// ==========================================================================
function initCollapsibleAccordions() {
  const btnToggleAll = document.getElementById('btn-toggle-all-sections');

  const updateToggleAllButton = () => {
    if (!btnToggleAll) return;
    const contents = document.querySelectorAll('.drawer-body .collapsible-content');
    const allExpanded = Array.from(contents).every(c => !c.classList.contains('collapsed'));
    btnToggleAll.textContent = allExpanded ? 'Contraer todo' : 'Expandir todo';
  };

  document.querySelectorAll('.collapsible-header').forEach(header => {
    header.addEventListener('click', () => {
      const parent = header.closest('.collapsible-section');
      const content = parent.querySelector('.collapsible-content');
      const arrow = header.querySelector('.collapsible-arrow');
      
      if (!content) return;

      const isCollapsed = content.classList.contains('collapsed');
      if (isCollapsed) {
        content.classList.remove('collapsed');
        if (parent) parent.classList.add('expanded');
        if (arrow) arrow.innerHTML = '&blacktriangledown;';
      } else {
        content.classList.add('collapsed');
        if (parent) parent.classList.remove('expanded');
        if (arrow) arrow.innerHTML = '&blacktriangleright;';
      }
      updateToggleAllButton();
    });
  });

  if (btnToggleAll) {
    btnToggleAll.addEventListener('click', () => {
      const contents = document.querySelectorAll('.drawer-body .collapsible-content');
      const anyCollapsed = Array.from(contents).some(c => c.classList.contains('collapsed'));

      contents.forEach(content => {
        const parent = content.closest('.collapsible-section');
        const arrow = parent.querySelector('.collapsible-arrow');
        if (anyCollapsed) {
          // Si alguno está cerrado, abrir todos
          content.classList.remove('collapsed');
          if (parent) parent.classList.add('expanded');
          if (arrow) arrow.innerHTML = '&blacktriangledown;';
        } else {
          // Si todos están abiertos, cerrar todos
          content.classList.add('collapsed');
          if (parent) parent.classList.remove('expanded');
          if (arrow) arrow.innerHTML = '&blacktriangleright;';
        }
      });
      updateToggleAllButton();
    });
  }

  // Asegurar estado inicial del botón
  updateToggleAllButton();
}

// ==========================================================================
// 6. EDITOR DE CÓDIGO (MAIN.PY AJUSTADO A PANTALLA)
// ==========================================================================
function initEditor() {
  const editor = document.getElementById('code-editor');
  const lineNumbers = document.getElementById('line-numbers');
  const cursorLabel = document.getElementById('editor-cursor-pos');
  const unsavedBadge = document.getElementById('unsaved-badge');

  editor.addEventListener('input', () => {
    updateLineNumbers();
    state.isDirty = true;
    unsavedBadge.classList.remove('hidden');
  });

  editor.addEventListener('scroll', () => {
    lineNumbers.scrollTop = editor.scrollTop;
  });

  const updateCursor = () => {
    const selStart = editor.selectionStart;
    const textBefore = editor.value.substring(0, selStart);
    const lines = textBefore.split('\n');
    const lineNum = lines.length;
    const colNum = lines[lines.length - 1].length + 1;
    cursorLabel.textContent = `Línea ${lineNum}, Col ${colNum}`;
  };

  editor.addEventListener('keyup', updateCursor);
  editor.addEventListener('click', updateCursor);

  editor.addEventListener('keydown', (e) => {
    if (e.key === 'Tab') {
      e.preventDefault();
      const start = editor.selectionStart;
      const end = editor.selectionEnd;
      editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
      editor.selectionStart = editor.selectionEnd = start + 4;
      updateLineNumbers();
      state.isDirty = true;
      unsavedBadge.classList.remove('hidden');
    }

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 's') {
      e.preventDefault();
      saveMainPy();
    }

    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleRunMain();
    }
  });
}

function updateLineNumbers() {
  const editor = document.getElementById('code-editor');
  const lineNumbers = document.getElementById('line-numbers');
  const lineCount = editor.value.split('\n').length;
  let html = '';
  for (let i = 1; i <= lineCount; i++) {
    html += i + '<br>';
  }
  lineNumbers.innerHTML = html;
}

function updateActiveFileUI(fileName) {
  state.activeFile = fileName;
  const fileNameEl = document.getElementById('editor-file-name');
  if (fileNameEl) fileNameEl.textContent = fileName;
  const indicatorEl = document.getElementById('active-file-indicator');
  if (indicatorEl) indicatorEl.textContent = fileName;
  const btnRunText = document.getElementById('btn-run-text');
  if (btnRunText) {
    btnRunText.textContent = fileName === 'pasos_algebraicos.txt' ? 'Ejecutar Pasos algebráicos' : 'Ejecutar main.py';
  }
}

async function loadMainPy(targetFile = null) {
  const fileToLoad = targetFile || state.activeFile || 'main.py';
  state.activeFile = fileToLoad;
  try {
    const res = await fetch(`/api/get_main?file=${encodeURIComponent(fileToLoad)}`);
    if (!res.ok) throw new Error(`Error al leer ${fileToLoad}`);
    const data = await res.json();
    const editor = document.getElementById('code-editor');
    editor.value = data.code;
    updateLineNumbers();
    state.isDirty = false;
    document.getElementById('unsaved-badge').classList.add('hidden');
    updateActiveFileUI(fileToLoad);
    appendTerminalLine('system', `${fileToLoad} cargado desde disco (${editor.value.split('\n').length} líneas).`);
  } catch (err) {
    appendTerminalLine('error', `Error cargando ${fileToLoad}: ${err.message}`);
  }
}

async function saveMainPy() {
  const editor = document.getElementById('code-editor');
  const fileToSave = state.activeFile || 'main.py';
  try {
    const res = await fetch('/api/save_main', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: editor.value, file: fileToSave })
    });
    if (!res.ok) throw new Error(`Error al guardar ${fileToSave}`);
    state.isDirty = false;
    document.getElementById('unsaved-badge').classList.add('hidden');
    appendTerminalLine('system', `${fileToSave} guardado en disco exitosamente.`);
  } catch (err) {
    appendTerminalLine('error', `Error guardando ${fileToSave}: ${err.message}`);
  }
}

// ==========================================================================
// 7. EJECUCIÓN DEL MOTOR MANIM
// ==========================================================================
async function handleRunMain(customCode = null) {
  if (state.isRendering) return;

  const editor = document.getElementById('code-editor');
  const codeToRun = customCode !== null ? customCode : editor.value;
  const activeFile = state.activeFile || 'main.py';

  appendTerminalLine('info', '==========================================================');
  appendTerminalLine('info', `Iniciando ejecución de ${activeFile} (Calidad: ${state.quality})...`);

  try {
    const res = await fetch('/api/run_main', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: codeToRun, file: activeFile, quality: state.quality })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Fallo al iniciar ejecución');
    }

    state.isDirty = false;
    document.getElementById('unsaved-badge').classList.add('hidden');
  } catch (err) {
    appendTerminalLine('error', `Error al ejecutar: ${err.message}`);
    handleServerStatusUpdate({ state: 'error' });
  }
}

// ==========================================================================
// 8. EVENTOS SSE Y CONSOLA EN TIEMPO REAL
// ==========================================================================
function initSSE() {
  const eventSource = new EventSource('/api/events');

  eventSource.addEventListener('connected', () => {
    appendTerminalLine('system', 'Conexión SSE activa con Manim Studio.');
  });

  eventSource.addEventListener('log', (e) => {
    const data = JSON.parse(e.data);
    appendTerminalLine(data.level || 'info', data.text);
    if (typeof appendShortTerminalLine === 'function') {
      appendShortTerminalLine(data.level || 'info', data.text);
    }
  });

  eventSource.addEventListener('status', (e) => {
    const data = JSON.parse(e.data);
    handleServerStatusUpdate(data);
    if (typeof handleShortStatusUpdate === 'function') {
      handleShortStatusUpdate(data);
    }
  });

  eventSource.addEventListener('video', (e) => {
    const data = JSON.parse(e.data);
    if (data.video_url) {
      loadVideoPlayer(data.video_url);
      if (typeof loadShortVideoPlayer === 'function') {
        loadShortVideoPlayer(data.video_url);
      }
    }
  });
}

function handleServerStatusUpdate(data) {
  const statusPill = document.getElementById('engine-status-pill');
  const overlay = document.getElementById('render-overlay');
  const btnRun = document.getElementById('btn-run');
  const btnRunText = document.getElementById('btn-run-text');

  if (data.state === 'rendering') {
    state.isRendering = true;
    statusPill.className = 'status-indicator rendering';
    statusPill.textContent = 'Ejecutando';
    btnRun.disabled = true;
    btnRunText.textContent = 'Compilando...';
    overlay.classList.remove('hidden');
  } else if (data.state === 'success') {
    state.isRendering = false;
    statusPill.className = 'status-indicator ready';
    statusPill.textContent = 'Listo';
    btnRun.disabled = false;
    btnRunText.textContent = 'Ejecutar main.py';
    overlay.classList.add('hidden');

    if (data.video_url) {
      loadVideoPlayer(data.video_url);
    }
  } else if (data.state === 'error') {
    state.isRendering = false;
    statusPill.className = 'status-indicator error';
    statusPill.textContent = 'Error';
    btnRun.disabled = false;
    btnRunText.textContent = 'Reintentar Ejecución';
    overlay.classList.add('hidden');
  }
}

function appendTerminalLine(level, text) {
  const terminal = document.getElementById('terminal-screen');
  const line = document.createElement('div');
  line.className = `term-line term-${level}`;

  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0];
  line.innerHTML = `<span class="term-timestamp">[${timeStr}]</span> ${escapeHtml(text)}`;

  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

function clearTerminal() {
  const terminal = document.getElementById('terminal-screen');
  terminal.innerHTML = '<div class="term-line term-system"><span class="term-timestamp">[00:00:00]</span> Consola limpiada por el usuario.</div>';
}

function copyTerminalLogs() {
  const terminal = document.getElementById('terminal-screen');
  navigator.clipboard.writeText(terminal.innerText).then(() => {
    alert('Registros copiados al portapapeles.');
  });
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ==========================================================================
// 9. REPRODUCTOR DE VIDEO
// ==========================================================================
async function fetchLatestVideo() {
  try {
    const res = await fetch('/api/latest_video');
    if (res.ok) {
      const data = await res.json();
      if (data.video_url) {
        loadVideoPlayer(data.video_url);
      }
    }
  } catch (err) {}
}

function loadVideoPlayer(videoUrl) {
  // 1. Reproductor en Animación Manual
  const video = document.getElementById('manim-video-player');
  const source = document.getElementById('video-source');
  const placeholder = document.getElementById('video-placeholder');
  const metaBadge = document.getElementById('video-meta');
  const btnDownload = document.getElementById('btn-download-video');
  const btnRestart = document.getElementById('btn-restart-video');

  source.src = videoUrl;
  video.load();

  state.currentVideoUrl = videoUrl;
  video.onloadeddata = () => {
    placeholder.style.display = 'none';
    metaBadge.textContent = `${video.videoWidth}x${video.videoHeight} &bull; ${video.duration.toFixed(1)}s`;
    btnDownload.href = videoUrl;
    btnDownload.classList.remove('disabled');
    btnRestart.disabled = false;
    updateDownloadButtonUI();
    
    // Si hay audio activo, posicionar en el offset inicial configurado
    if (state.audio.url && state.audio.autoSync) {
      const audio = document.getElementById('manim-audio-player');
      if (audio) {
        audio.currentTime = state.audio.startOffset;
      }
    }
    video.play().catch(() => {});
  };

  // 2. Reproductor en Insertar Funciones (Scratch)
  const scratchVideo = document.getElementById('scratch-video-player');
  const scratchSource = document.getElementById('scratch-video-source');
  const scratchPlaceholder = document.getElementById('scratch-video-placeholder');

  if (scratchVideo && scratchSource) {
    scratchSource.src = videoUrl;
    scratchVideo.load();
    scratchVideo.onloadeddata = () => {
      if (scratchPlaceholder) scratchPlaceholder.style.display = 'none';
      scratchVideo.play().catch(() => {});
    };
  }
}

// ==========================================================================
// 10. CONSTRUCTOR DE FUNCIONES ESTILO SCRATCH
// ==========================================================================
const BLOCK_DEFS = {
  punto: {
    name: 'agregar_punto',
    category: 'geo',
    badge: '⊙',
    fields: [
      { key: 'x', label: 'X', type: 'number', default: 1.0, step: 0.5 },
      { key: 'y', label: 'Y (f(x) o número)', type: 'text', default: 'f_objetivo(1.0)' },
      { key: 'color', label: 'Color', type: 'color', default: '#FF0000' },
      { key: 'label', label: 'Mostrar Etiqueta', type: 'select', default: 'True', options: ['True', 'False'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.agregar_punto(${v.x}, ${v.y}, color="${v.color}", label=${v.label}, tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  punto_curva: {
    name: 'animar_punto_sobre_curva',
    category: 'geo',
    badge: '●→',
    fields: [
      { key: 'x_ini', label: 'X Inicio', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x_fin', label: 'X Fin', type: 'number', default: 3.5, step: 0.5 },
      { key: 'color', label: 'Color', type: 'color', default: '#00FF00' },
      { key: 'id', label: 'ID (Opcional p/ Memoria)', type: 'text', default: '' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => {
      const idParam = v.id ? `, id="${v.id}"` : '';
      return `    escena.animar_punto_sobre_curva(x_inicio=${v.x_ini}, x_fin=${v.x_fin}, funcion=f_objetivo, color="${v.color}"${idParam}, tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`;
    }
  },

  fade_in_plano: {
    name: 'fade_in_plano',
    category: 'geo',
    badge: '⊞',
    fields: [
      { key: 'x_min', label: 'X Mínimo', type: 'number', default: -5.0, step: 0.5 },
      { key: 'x_max', label: 'X Máximo', type: 'number', default: 5.0, step: 0.5 },
      { key: 'color', label: 'Color Cuadrícula', type: 'color', default: '#2563EB' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.fade_in_plano(x_min=${v.x_min}, x_max=${v.x_max}, color="${v.color}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  funcion: {
    name: 'agregar_funcion',
    category: 'func',
    badge: 'ƒ(x)',
    fields: [
      { key: 'color', label: 'Color Curva', type: 'color', default: '#00FFCC' },
      { key: 'id', label: 'ID del Objeto', type: 'text', default: 'curva_auxiliar' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.agregar_funcion(f_objetivo, color="${v.color}", id="${v.id}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  secante: {
    name: 'animar_secante',
    category: 'func',
    badge: '⊿',
    fields: [
      { key: 'x1_ini', label: 'X1 Inicio', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x1_fin', label: 'X1 Fin', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x2_ini', label: 'X2 Inicio', type: 'number', default: 3.5, step: 0.5 },
      { key: 'x2_fin', label: 'X2 Fin (1.00001 -> Tangente)', type: 'number', default: 1.00001, step: 0.0001 },
      { key: 'color', label: 'Color Recta', type: 'color', default: '#FFFF00' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 3.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.animar_secante(x1_ini=${v.x1_ini}, x1_fin=${v.x1_fin}, x2_ini=${v.x2_ini}, x2_fin=${v.x2_fin}, funcion=f_objetivo, color="${v.color}", tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`
  },

  convergencia_parametrica: {
    name: 'animar_convergencia_parametrica',
    category: 'func',
    badge: '⟳',
    fields: [
      { key: 'x_fijo', label: 'X Fijo (Ancla)', type: 'number', default: 0.0, step: 0.25 },
      { key: 'x_movil_ini', label: 'X Móvil Inicio', type: 'number', default: 1.5, step: 0.25 },
      { key: 'x_movil_fin', label: 'X Móvil Fin (C)', type: 'number', default: 0.8, step: 0.05 },
      { key: 'id_secante', label: 'ID Secante', type: 'text', default: 'secante' },
      { key: 'id_punto_curva', label: 'ID Punto Curva', type: 'text', default: 'punto_B' },
      { key: 'id_punto_raiz', label: 'ID Punto Raíz', type: 'text', default: 'punto_raiz' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.animar_convergencia_parametrica(funcion=f_objetivo, x_fijo=${v.x_fijo}, x_movil_ini=${v.x_movil_ini}, x_movil_fin=${v.x_movil_fin}, id_secante="${v.id_secante}", id_punto_curva="${v.id_punto_curva}", id_punto_raiz="${v.id_punto_raiz}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  integral: {
    name: 'animar_integral',
    category: 'func',
    badge: '∫',
    fields: [
      { key: 'x_min', label: 'X Mínimo', type: 'number', default: 0.0, step: 0.5 },
      { key: 'x_max', label: 'X Máximo', type: 'number', default: 2.0, step: 0.5 },
      { key: 'dx', label: 'dx Riemann (vacío = continua)', type: 'text', default: '0.2' },
      { key: 'color', label: 'Color', type: 'color', default: '#00FFFF' },
      { key: 'opacidad', label: 'Opacidad (0 a 1)', type: 'number', default: 0.5, step: 0.1 },
      { key: 'id', label: 'ID', type: 'text', default: 'area_1' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => {
      const dxParam = (v.dx && v.dx.trim() && v.dx.trim().toLowerCase() !== 'none') ? `dx=${v.dx.trim()}` : `dx=None`;
      const idParam = v.id ? `, id_area="${v.id}"` : '';
      return `    escena.animar_integral(f_objetivo, x_min=${v.x_min}, x_max=${v.x_max}, ${dxParam}, color="${v.color}", opacidad=${v.opacidad}${idParam}, tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`;
    }
  },

  linea_punteada: {
    name: 'animar_linea_punteada',
    category: 'dim',
    badge: '┊',
    fields: [
      { key: 'x', label: 'Coordenada X', type: 'number', default: 3.5, step: 0.5 },
      { key: 'color', label: 'Color', type: 'color', default: '#00FFFF' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.animar_linea_punteada(x1_ini=${v.x}, x1_fin=${v.x}, x2_ini=${v.x}, x2_fin=${v.x}, y1_ini=f_objetivo, y2_ini=0, color="${v.color}", tiempo_animacion=${v.t_anim}, tiempo_espera=0.5)`
  },

  llave: {
    name: 'animar_llave',
    category: 'dim',
    badge: '{ }',
    fields: [
      { key: 'x1', label: 'X Inicio', type: 'number', default: 1.0, step: 0.5 },
      { key: 'x2', label: 'X Fin', type: 'number', default: 3.5, step: 0.5 },
      { key: 'texto', label: 'Etiqueta LaTeX', type: 'latex', default: '\\Delta x' },
      { key: 'color', label: 'Color', type: 'color', default: '#FF00FF' },
      { key: 'dir', label: 'Dirección', type: 'select', default: 'DOWN', options: ['DOWN', 'UP', 'LEFT', 'RIGHT'] }
    ],
    toCode: (v) => `    escena.animar_llave(x1_ini=${v.x1}, x1_fin=${v.x1}, x2_ini=${v.x2}, x2_fin=${v.x2}, y1_ini=0, y2_ini=0, texto=r"${v.texto}", direccion=${v.dir}, color="${v.color}", tiempo_animacion=1.0, tiempo_espera=1.0)`
  },

  algebra_flotante: {
    name: 'agregar_algebra_flotante',
    category: 'tex',
    badge: '∑',
    fields: [
      { key: 'pos', label: 'Posición Viewport', type: 'select', default: 'UL', options: ['UL', 'UR', 'DL', 'DR'] },
      { key: 'id', label: 'ID para Purga', type: 'text', default: 'hud_limite' },
      { key: 'formula', label: 'Fórmula en LaTeX', type: 'latex', default: 'm = \\frac{f(x+\\Delta x) - f(x)}{\\Delta x}' }
    ],
    toCode: (v) => `    escena.agregar_algebra_flotante(r"""$$${v.formula}$$""", posicion="${v.pos}", id="${v.id}", tiempo_animacion=1.0, tiempo_espera=1.0)`
  },

  transformar_texto: {
    name: 'transformar_a_texto',
    category: 'tex',
    badge: 'Tx',
    fields: [
      { key: 'formula', label: 'Ecuación Final', type: 'latex', default: 'f\'(x) = \\lim_{\\Delta x \\to 0} \\frac{f(x+\\Delta x) - f(x)}{\\Delta x}' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 2.0, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 2.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.transformar_a_texto(texto_latex=r"${v.formula}", tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  transformar_objeto: {
    name: 'transformar_objeto',
    category: 'tex',
    badge: '⇄',
    fields: [
      { key: 'origen', label: 'ID Origen (vacío = último)', type: 'text', default: '' },
      { key: 'tipo_dest', label: 'Tipo Destino', type: 'select', default: 'funcion', options: ['funcion', 'punto', 'label'] },
      { key: 'dest_valor', label: 'Valor / Fórmula / Coord (X, Y)', type: 'latex', default: 'x**2 - 1' },
      { key: 'color', label: 'Color Destino', type: 'color', default: '#FFFF00' },
      { key: 'id_dest', label: 'ID Destino (opcional)', type: 'text', default: '' },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => {
      const origArg = v.origen ? `origen="${v.origen}", ` : '';
      const idDestArg = v.id_dest ? `, id_destino="${v.id_dest}"` : '';
      if (v.tipo_dest === 'funcion') {
        const expr = v.dest_valor.replace(/^f\(x\)\s*=\s*/, '');
        return `    escena.transformar_objeto(${origArg}tipo_destino="funcion", funcion=lambda x: ${expr}, color="${v.color}"${idDestArg}, tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`;
      } else if (v.tipo_dest === 'punto') {
        const parts = v.dest_valor.split(',').map(s => parseFloat(s.trim())).filter(n => !isNaN(n));
        const px = parts[0] !== undefined ? parts[0] : 1.0;
        const py = parts[1] !== undefined ? parts[1] : 1.0;
        return `    escena.transformar_objeto(${origArg}tipo_destino="punto", x=${px}, y=${py}, color="${v.color}", label=True${idDestArg}, tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`;
      } else {
        return `    escena.transformar_objeto(${origArg}tipo_destino="label", texto=r"""${v.dest_valor}""", color="${v.color}", posicion="center"${idDestArg}, tiempo_animacion=${v.t_anim}, tiempo_espera=1.0)`;
      }
    }
  },

  transformar_plano: {
    name: 'transformar_a_plano',
    category: 'tex',
    badge: 'ℝ²',
    fields: [
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 },
      { key: 't_wait', label: 'T. Espera (s)', type: 'number', default: 0.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.transformar_a_plano(tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  },

  eliminar_objeto: {
    name: 'eliminar_objeto',
    category: 'purge',
    badge: '⊖',
    fields: [
      { key: 'id', label: 'ID del Objeto a Purgar', type: 'text', default: 'hud_limite' },
      { key: 'anim', label: 'Animación de Salida', type: 'select', default: 'FadeOut', options: ['FadeOut', 'Uncreate', 'ShrinkToCenter'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.eliminar_objeto(id="${v.id}", animacion="${v.anim}", tiempo_animacion=${v.t_anim}, tiempo_espera=0.5)`
  },

  fade_out_plano: {
    name: 'fade_out_plano',
    category: 'purge',
    badge: '⊞⁻',
    fields: [
      { key: 'anim', label: 'Animación de Salida', type: 'select', default: 'FadeOut', options: ['FadeOut', 'Uncreate', 'ShrinkToCenter'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.fade_out_plano(animacion="${v.anim}", tiempo_animacion=${v.t_anim}, tiempo_espera=0.5)`
  },

  desvanecer_todo: {
    name: 'desvanecer_todo',
    category: 'purge',
    badge: '∅',
    fields: [
      { key: 'anim', label: 'Efecto de Salida', type: 'select', default: 'FadeOut', options: ['FadeOut', 'ShrinkToCenter'] },
      { key: 't_anim', label: 'T. Anim (s)', type: 'number', default: 1.5, step: 0.25 }
    ],
    toCode: (v) => `    escena.desvanecer_todo(animacion="${v.anim}", tiempo_animacion=${v.t_anim})`
  },

  iniciar_bloque_paralelo: {
    name: 'iniciar_bloque_paralelo',
    category: 'parallel',
    badge: '⫘',
    fields: [],
    toCode: () => `    escena.iniciar_bloque_paralelo()`
  },

  cerrar_bloque_paralelo: {
    name: 'cerrar_bloque_paralelo',
    category: 'parallel',
    badge: '⫙',
    fields: [
      { key: 't_anim', label: 'T. Anim Simultánea (s)', type: 'number', default: 1.5, step: 0.25 },
      { key: 't_wait', label: 'T. Espera Posterior (s)', type: 'number', default: 1.0, step: 0.25 }
    ],
    toCode: (v) => `    escena.cerrar_bloque_paralelo(tiempo_animacion=${v.t_anim}, tiempo_espera=${v.t_wait})`
  }
};

function initScratchSystem() {
  // Click en bloques de la paleta
  document.querySelectorAll('[data-add-block]').forEach(el => {
    el.addEventListener('click', () => {
      const blockKey = el.getAttribute('data-add-block');
      addScratchBlock(blockKey);
    });
  });

  // Botones de acción del Scratch Stack
  document.getElementById('btn-scratch-render').addEventListener('click', handleScratchRender);
  document.getElementById('btn-scratch-to-main').addEventListener('click', handleScratchExportToMain);
  document.getElementById('btn-scratch-clear').addEventListener('click', () => {
    state.scratchBlocks = [];
    renderScratchStack();
  });

  // Cargar bloques iniciales por defecto
  state.scratchBlocks = [
    createBlockInstance('punto', { x: 1.0, y: 'f_objetivo(1.0)', color: '#FF0000', label: 'True', t_anim: 1.0, t_wait: 0.5 }),
    createBlockInstance('punto_curva', { x_ini: 1.0, x_fin: 3.5, color: '#00FF00', t_anim: 2.0, t_wait: 0.5 }),
    createBlockInstance('llave', { x1: 1.0, x2: 3.5, texto: '\\Delta x', color: '#FF00FF', dir: 'DOWN' }),
    createBlockInstance('desvanecer_todo', { anim: 'FadeOut', t_anim: 1.5 })
  ];

  renderScratchStack();
}

function createBlockInstance(type, customValues = {}) {
  const def = BLOCK_DEFS[type];
  if (!def) return null;
  const values = {};
  def.fields.forEach(f => {
    values[f.key] = customValues[f.key] !== undefined ? customValues[f.key] : f.default;
  });
  return {
    id: 'block_' + Math.random().toString(36).substring(2, 9),
    type,
    values
  };
}

function addScratchBlock(type) {
  const inst = createBlockInstance(type);
  if (inst) {
    state.scratchBlocks.push(inst);
    renderScratchStack();
  }
}

function renderScratchStack() {
  const container = document.getElementById('scratch-stack-list');
  if (!container) return;

  if (state.scratchBlocks.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:3rem 1rem; color:var(--color-subtle);">
        <p style="font-size:1.1rem; margin-bottom:0.5rem; color:var(--color-primary);">La secuencia está vacía</p>
        <p style="font-size:0.8rem;">Haz click en cualquier bloque de la paleta izquierda para agregarlo a la animación.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = '';
  state.scratchBlocks.forEach((block, idx) => {
    const def = BLOCK_DEFS[block.type];
    if (!def) return;

    const el = document.createElement('div');
    el.className = `scratch-stack-item block-${def.category}`;
    el.setAttribute('data-block-id', block.id);

    // Cabecera del bloque
    let fieldsHtml = '';
    def.fields.forEach(f => {
      const val = block.values[f.key];
      if (f.type === 'select') {
        const opts = f.options.map(o => `<option value="${o}" ${o == val ? 'selected' : ''}>${o}</option>`).join('');
        fieldsHtml += `
          <div class="block-field">
            <label>${f.label}</label>
            <select data-field-key="${f.key}">${opts}</select>
          </div>
        `;
      } else if (f.type === 'latex') {
        fieldsHtml += `
          <div class="block-field" style="grid-column: span 2;">
            <label>${f.label}</label>
            <input type="text" data-field-key="${f.key}" value="${escapeHtml(val)}" class="code-font latex-input">
            <div class="block-latex-preview" id="prev-${block.id}-${f.key}"></div>
          </div>
        `;
      } else {
        const stepAttr = f.step ? `step="${f.step}"` : '';
        fieldsHtml += `
          <div class="block-field">
            <label>${f.label}</label>
            <input type="${f.type}" data-field-key="${f.key}" value="${escapeHtml(val)}" ${stepAttr}>
          </div>
        `;
      }
    });

    el.innerHTML = `
      <div class="stack-item-top">
        <div class="stack-item-info">
          <span class="block-badge">${def.badge}</span>
          <span>${idx + 1}. ${def.name}()</span>
        </div>
        <div class="stack-item-tools">
          <button class="btn-block-tool btn-move-up" title="Mover arriba" ${idx === 0 ? 'disabled' : ''}>▲</button>
          <button class="btn-block-tool btn-move-down" title="Mover abajo" ${idx === state.scratchBlocks.length - 1 ? 'disabled' : ''}>▼</button>
          <button class="btn-block-tool btn-block-delete" title="Eliminar bloque">&times;</button>
        </div>
      </div>
      <div class="stack-params-grid">
        ${fieldsHtml}
      </div>
    `;

    // Conectar eventos de cambio
    el.querySelectorAll('input, select').forEach(input => {
      const key = input.getAttribute('data-field-key');
      input.addEventListener('input', () => {
        block.values[key] = input.value;
        if (input.classList.contains('latex-input')) {
          renderLatexPreview(document.getElementById(`prev-${block.id}-${key}`), input.value);
        }
      });
    });

    // Reordenar y eliminar
    el.querySelector('.btn-move-up').addEventListener('click', () => {
      if (idx > 0) {
        const temp = state.scratchBlocks[idx];
        state.scratchBlocks[idx] = state.scratchBlocks[idx - 1];
        state.scratchBlocks[idx - 1] = temp;
        renderScratchStack();
      }
    });

    el.querySelector('.btn-move-down').addEventListener('click', () => {
      if (idx < state.scratchBlocks.length - 1) {
        const temp = state.scratchBlocks[idx];
        state.scratchBlocks[idx] = state.scratchBlocks[idx + 1];
        state.scratchBlocks[idx + 1] = temp;
        renderScratchStack();
      }
    });

    el.querySelector('.btn-block-delete').addEventListener('click', () => {
      state.scratchBlocks.splice(idx, 1);
      renderScratchStack();
    });

    container.appendChild(el);

    // Renderizar KaTeX previews iniciales
    def.fields.filter(f => f.type === 'latex').forEach(f => {
      const prevEl = document.getElementById(`prev-${block.id}-${f.key}`);
      renderLatexPreview(prevEl, block.values[f.key]);
    });
  });
}

function renderLatexPreview(element, texString) {
  if (!element) return;
  const cleanTex = (texString || '').trim();
  if (!cleanTex) {
    element.innerHTML = '<span class="preview-placeholder">Escribe una fórmula LaTeX</span>';
    return;
  }
  let formula = cleanTex;
  if (formula.startsWith('$$') && formula.endsWith('$$')) formula = formula.slice(2, -2).trim();
  else if (formula.startsWith('$') && formula.endsWith('$')) formula = formula.slice(1, -1).trim();

  if (window.katex) {
    try {
      katex.render(formula, element, { throwOnError: false, displayMode: true });
    } catch {
      element.textContent = formula;
    }
  } else {
    element.textContent = formula;
  }
}

function generatePythonFromScratch() {
  const codeLines = state.scratchBlocks.map(b => {
    const def = BLOCK_DEFS[b.type];
    return def ? def.toCode(b.values) : '';
  }).filter(Boolean);

  return `import math
from manim import DOWN, UP, LEFT, RIGHT
from Planos.generar_plano import AnimadorGrafico

# Definición Funcional
def f_objetivo(x: float) -> float:
    return 0.5 * x**2 + 1

if __name__ == "__main__":
    escena = AnimadorGrafico(f_objetivo, x_min=-1.0, x_max=4.0)
    
${codeLines.join('\n\n')}
    
    escena.render(previsualizar=True)
`;
}

async function handleScratchRender() {
  const pyCode = generatePythonFromScratch();
  const editor = document.getElementById('code-editor');
  editor.value = pyCode;
  updateLineNumbers();
  appendTerminalLine('info', 'Compilando secuencia de bloques visuales en Manim...');
  await handleRunMain(pyCode);
}

function handleScratchExportToMain() {
  const pyCode = generatePythonFromScratch();
  const editor = document.getElementById('code-editor');
  editor.value = pyCode;
  updateLineNumbers();
  saveMainPy();
  switchView('view-manual');
  appendTerminalLine('system', 'Bloques exportados a main.py con éxito.');
}

// ==========================================================================
// 11. VISUALIZADOR DE DOCUMENTACIÓN (READMI.MD)
// ==========================================================================
async function loadDocs() {
  const docsContainer = document.getElementById('docs-content');
  try {
    const res = await fetch('/api/get_readme');
    if (!res.ok) throw new Error('No se pudo acceder a READMI.md');
    const data = await res.json();
    
    if (window.marked) {
      docsContainer.innerHTML = marked.parse(data.content);
      // Procesar fórmulas matemáticas si hay KaTeX
      if (window.katex) {
        docsContainer.querySelectorAll('p, li').forEach(el => {
          if (el.textContent.includes('$')) {
            // Reemplazo básico de delimitadores matemáticos
            el.innerHTML = el.innerHTML.replace(/\$\$([^$]+)\$\$/g, (m, tex) => {
              try { return katex.renderToString(tex, { displayMode: true }); } catch { return m; }
            }).replace(/\$([^$]+)\$/g, (m, tex) => {
              try { return katex.renderToString(tex, { displayMode: false }); } catch { return m; }
            });
          }
        });
      }
    } else {
      docsContainer.innerHTML = `<pre><code>${escapeHtml(data.content)}</code></pre>`;
    }
    state.docsLoaded = true;
  } catch (err) {
    docsContainer.innerHTML = `<p class="term-error">Error al cargar documentación: ${err.message}</p>`;
  }
}

// ==========================================================================
// 12. CARGADOR DE PLANTILLAS
// ==========================================================================
function initTemplatesModal() {
  const btnOpen = document.getElementById('btn-load-template');
  const btnClose = document.getElementById('btn-close-templates-modal');
  const btnCancel = document.getElementById('btn-cancel-template');
  const modal = document.getElementById('modal-templates');

  const openModal = () => modal.classList.remove('hidden');
  const closeModal = () => modal.classList.add('hidden');

  if (btnOpen) btnOpen.addEventListener('click', openModal);
  if (btnClose) btnClose.addEventListener('click', closeModal);
  if (btnCancel) btnCancel.addEventListener('click', closeModal);

  document.querySelectorAll('.template-item').forEach(item => {
    item.addEventListener('click', async () => {
      const templateId = item.getAttribute('data-template-id');
      if (!templateId) return;

      try {
        appendTerminalLine('info', `Cargando plantilla "${templateId}" desde la carpeta de Plantillas...`);
        const res = await fetch(`/api/get_template?id=${encodeURIComponent(templateId)}`);
        if (!res.ok) {
          const errData = await res.json().catch(() => ({}));
          throw new Error(errData.error || `HTTP error ${res.status}`);
        }
        const data = await res.json();
        if (data.status !== 'success' || !data.code) {
          throw new Error(data.error || 'No se recibió código de la plantilla');
        }

        if (templateId === 'pasos_algebraicos') {
          state.activeFile = 'pasos_algebraicos.txt';
          updateActiveFileUI('pasos_algebraicos.txt');
          const editor = document.getElementById('code-editor');
          if (editor) editor.value = data.code;
          updateLineNumbers();
          await saveMainPy();
          closeModal();
          switchView('view-manual');
          appendTerminalLine('system', `Plantilla especial "Pasos algebráicos" cargada desde ${data.path}. Editando pasos_algebraicos.txt.`);
          return;
        }

        state.activeFile = 'main.py';
        updateActiveFileUI('main.py');
        const editor = document.getElementById('code-editor');
        if (editor) editor.value = data.code;
        updateLineNumbers();
        await saveMainPy();
        closeModal();
        switchView('view-manual');
        appendTerminalLine('system', `Plantilla "${templateId}" cargada con éxito desde ${data.path} en main.py.`);
      } catch (err) {
        appendTerminalLine('error', `Error al cargar plantilla "${templateId}": ${err.message}`);
        alert(`Error al cargar plantilla: ${err.message}`);
      }
    });
  });
}

// ==========================================================================
// 12b. MÓDULO DE AUDIO SINCRONIZADO
// ==========================================================================
function formatSeconds(sec) {
  if (isNaN(sec) || sec < 0) sec = 0;
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

function parseTimeStr(str) {
  if (!str) return 0;
  str = str.trim();
  if (str.includes(':')) {
    const parts = str.split(':');
    const m = parseFloat(parts[0]) || 0;
    const s = parseFloat(parts[1]) || 0;
    return Math.max(0, m * 60 + s);
  }
  const val = parseFloat(str);
  return isNaN(val) ? 0 : Math.max(0, val);
}

function updateDownloadButtonUI() {
  const btnDownload = document.getElementById('btn-download-video');
  if (!btnDownload) return;
  const hasAudio = !!(state.audio.url && state.audio.name);
  const downloadText = hasAudio ? 'Descargar Video MP4 (Con Audio)' : 'Descargar Video MP4';

  if (!btnDownload.dataset.downloading) {
    btnDownload.innerHTML = `
      <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
        <polyline points="7 10 12 15 17 10"></polyline>
        <line x1="12" y1="15" x2="12" y2="3"></line>
      </svg>
      <span>${downloadText}</span>
    `;
    btnDownload.title = hasAudio
      ? `Descargar animación con el audio integrado desde ${formatSeconds(state.audio.startOffset)}`
      : 'Descargar archivo de video MP4';
  }
}

function initAudioModule() {
  const audioEl = document.getElementById('manim-audio-player');
  const videoEl = document.getElementById('manim-video-player');
  const fileInput = document.getElementById('audio-file-input');
  const dropzone = document.getElementById('audio-dropzone');
  const btnBrowse = document.getElementById('btn-browse-audio');
  const controlsPanel = document.getElementById('audio-controls-panel');
  const statusBadge = document.getElementById('audio-status-badge');
  const statusText = document.getElementById('audio-status-text');
  const equalizer = document.getElementById('audio-equalizer');
  const fileNameLabel = document.getElementById('audio-file-name');
  const fileDurationLabel = document.getElementById('audio-file-duration');
  const btnChange = document.getElementById('btn-change-audio');
  const btnRemove = document.getElementById('btn-remove-audio');
  const curTimeLabel = document.getElementById('audio-cur-time');
  const totalTimeLabel = document.getElementById('audio-total-time');
  const progressBar = document.getElementById('audio-progress-bar');
  const btnPlay = document.getElementById('btn-audio-play');
  const playLabel = document.getElementById('audio-play-label');
  const playIcon = document.getElementById('audio-play-icon');
  const btnStop = document.getElementById('btn-audio-stop');
  const btnMute = document.getElementById('btn-audio-mute');
  const volIcon = document.getElementById('audio-vol-icon');
  const volSlider = document.getElementById('audio-volume-slider');
  const volLabel = document.getElementById('audio-vol-label');
  const startInput = document.getElementById('audio-start-input');
  const startSecInput = document.getElementById('audio-start-seconds');
  const btnSetCurrentStart = document.getElementById('btn-set-current-as-start');
  const btnResetOffset = document.getElementById('btn-reset-offset');
  const checkAutoSync = document.getElementById('check-auto-sync');

  function updateOffset(newSec, notify = false) {
    const maxDur = state.audio.duration || 3600;
    newSec = Math.max(0, Math.min(newSec, maxDur));
    state.audio.startOffset = Math.round(newSec * 10) / 10;
    if (startSecInput) startSecInput.value = state.audio.startOffset.toFixed(1);
    if (startInput) startInput.value = formatSeconds(state.audio.startOffset);
    updateDownloadButtonUI();

    // Si el video está en 0 y pausado, posicionamos el audio en el offset
    if (videoEl && videoEl.currentTime < 0.1 && videoEl.paused && !state.audio.isPlaying) {
      audioEl.currentTime = state.audio.startOffset;
      if (curTimeLabel) curTimeLabel.textContent = formatSeconds(audioEl.currentTime);
      if (progressBar) progressBar.value = audioEl.currentTime;
    }

    if (notify) {
      appendTerminalLine('system', `Punto de inicio del audio configurado en: ${formatSeconds(state.audio.startOffset)} (${state.audio.startOffset.toFixed(1)}s)`);
    }
  }

  // Carga de archivo de audio
  function handleAudioFile(file) {
    if (!file) return;
    if (!file.type.startsWith('audio/') && !file.name.match(/\.(mp3|wav|ogg|aac|flac|m4a)$/i)) {
      appendTerminalLine('error', 'El archivo seleccionado no es un formato de audio compatible.');
      return;
    }

    const objectUrl = URL.createObjectURL(file);
    state.audio.file = file;
    state.audio.name = file.name;
    state.audio.url = objectUrl;

    audioEl.src = objectUrl;
    audioEl.load();

    if (fileNameLabel) fileNameLabel.textContent = file.name;
    if (dropzone) dropzone.style.display = 'none';
    if (controlsPanel) controlsPanel.classList.remove('hidden');

    if (statusBadge) statusBadge.className = 'audio-status-badge linked';
    if (statusText) statusText.textContent = 'Audio vinculado';

    appendTerminalLine('system', `Audio cargado: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`);
    updateDownloadButtonUI();

    // Subir en segundo plano al servidor para persistencia local en /audios/
    fetch('/api/upload_audio', {
      method: 'POST',
      headers: { 'X-Filename': file.name },
      body: file
    }).catch(() => {});
  }

  // Evento metadata de audio
  audioEl.addEventListener('loadedmetadata', () => {
    state.audio.duration = audioEl.duration;
    const durStr = formatSeconds(audioEl.duration);
    if (fileDurationLabel) fileDurationLabel.textContent = durStr;
    if (totalTimeLabel) totalTimeLabel.textContent = durStr;
    if (progressBar) progressBar.max = audioEl.duration;
    if (startSecInput) startSecInput.max = audioEl.duration;

    // Colocar en el segundo de inicio configurado
    audioEl.currentTime = state.audio.startOffset;
    if (curTimeLabel) curTimeLabel.textContent = formatSeconds(audioEl.currentTime);
    if (progressBar) progressBar.value = audioEl.currentTime;
    updateDownloadButtonUI();

    // Si el video ya está reproduciéndose, sincronizar de inmediato
    if (videoEl && !videoEl.paused && state.audio.autoSync) {
      const targetTime = videoEl.currentTime + state.audio.startOffset;
      if (targetTime < audioEl.duration) {
        audioEl.currentTime = targetTime;
        audioEl.play().catch(() => {});
      }
    }
  });

  // Selector de archivos y Drag & Drop
  if (btnBrowse) {
    btnBrowse.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  if (dropzone) {
    dropzone.addEventListener('click', () => fileInput.click());

    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files && e.dataTransfer.files[0]) {
        handleAudioFile(e.dataTransfer.files[0]);
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener('change', () => {
      if (fileInput.files && fileInput.files[0]) {
        handleAudioFile(fileInput.files[0]);
      }
    });
  }

  if (btnChange) {
    btnChange.addEventListener('click', () => fileInput.click());
  }

  if (btnRemove) {
    btnRemove.addEventListener('click', () => {
      audioEl.pause();
      audioEl.removeAttribute('src');
      audioEl.load();
      state.audio.file = null;
      state.audio.url = null;
      state.audio.name = '';
      state.audio.duration = 0;
      state.audio.isPlaying = false;

      if (controlsPanel) controlsPanel.classList.add('hidden');
      if (dropzone) dropzone.style.display = 'flex';
      if (statusBadge) statusBadge.className = 'audio-status-badge';
      if (statusText) statusText.textContent = 'Sin audio';
      if (equalizer) equalizer.classList.remove('playing');

      updateDownloadButtonUI();
      appendTerminalLine('system', 'Audio desvinculado de la animación.');
    });
  }

  // Controles independientes de reproducción
  function updatePlayButtonUI(isPlaying) {
    state.audio.isPlaying = isPlaying;
    if (isPlaying) {
      if (playLabel) playLabel.textContent = 'Pausa';
      if (playIcon) playIcon.innerHTML = '<rect x="6" y="4" width="4" height="16"></rect><rect x="14" y="4" width="4" height="16"></rect>';
      if (equalizer) equalizer.classList.add('playing');
      if (statusBadge) statusBadge.className = 'audio-status-badge playing';
      if (statusText) statusText.textContent = 'Reproduciendo';
    } else {
      if (playLabel) playLabel.textContent = 'Play';
      if (playIcon) playIcon.innerHTML = '<polygon points="5 3 19 12 5 21 5 3"></polygon>';
      if (equalizer) equalizer.classList.remove('playing');
      if (statusBadge) statusBadge.className = 'audio-status-badge linked';
      if (statusText) statusText.textContent = 'Audio vinculado';
    }
  }

  if (btnPlay) {
    btnPlay.addEventListener('click', () => {
      if (!state.audio.url) return;
      if (audioEl.paused) {
        audioEl.play().catch(() => {});
      } else {
        audioEl.pause();
      }
    });
  }

  if (btnStop) {
    btnStop.addEventListener('click', () => {
      if (!state.audio.url) return;
      audioEl.pause();
      audioEl.currentTime = state.audio.startOffset;
      if (progressBar) progressBar.value = state.audio.startOffset;
      if (curTimeLabel) curTimeLabel.textContent = formatSeconds(state.audio.startOffset);
    });
  }

  // Scrubbing de barra de progreso del audio
  if (progressBar) {
    progressBar.addEventListener('input', () => {
      if (!state.audio.url) return;
      const targetSec = parseFloat(progressBar.value);
      audioEl.currentTime = targetSec;
      if (curTimeLabel) curTimeLabel.textContent = formatSeconds(targetSec);
    });
  }

  audioEl.addEventListener('timeupdate', () => {
    if (!state.audio.url) return;
    if (curTimeLabel) curTimeLabel.textContent = formatSeconds(audioEl.currentTime);
    if (progressBar) progressBar.value = audioEl.currentTime;
  });

  audioEl.addEventListener('play', () => updatePlayButtonUI(true));
  audioEl.addEventListener('pause', () => updatePlayButtonUI(false));
  audioEl.addEventListener('ended', () => {
    updatePlayButtonUI(false);
    audioEl.currentTime = state.audio.startOffset;
    if (progressBar) progressBar.value = state.audio.startOffset;
    if (curTimeLabel) curTimeLabel.textContent = formatSeconds(state.audio.startOffset);
  });

  // Volumen y Silencio
  if (volSlider) {
    volSlider.addEventListener('input', () => {
      const vol = parseFloat(volSlider.value);
      audioEl.volume = vol;
      audioEl.muted = false;
      state.audio.volume = vol;
      state.audio.isMuted = false;
      if (volLabel) volLabel.textContent = `${Math.round(vol * 100)}%`;
      updateVolumeIcon(vol, false);
    });
  }

  if (btnMute) {
    btnMute.addEventListener('click', () => {
      audioEl.muted = !audioEl.muted;
      state.audio.isMuted = audioEl.muted;
      updateVolumeIcon(audioEl.volume, audioEl.muted);
      if (volLabel) volLabel.textContent = audioEl.muted ? '0%' : `${Math.round(audioEl.volume * 100)}%`;
    });
  }

  function updateVolumeIcon(vol, muted) {
    if (!volIcon) return;
    if (muted || vol === 0) {
      volIcon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line>';
    } else if (vol < 0.5) {
      volIcon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M15.54 8.46a5 5 0 0 1 0 7.07"></path>';
    } else {
      volIcon.innerHTML = '<polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>';
    }
  }

  // Controles del Segundo de Inicio (Offset)
  if (startInput) {
    startInput.addEventListener('change', () => {
      const sec = parseTimeStr(startInput.value);
      updateOffset(sec, true);
    });
  }

  if (startSecInput) {
    startSecInput.addEventListener('input', () => {
      const sec = parseFloat(startSecInput.value) || 0;
      updateOffset(sec, false);
    });
    startSecInput.addEventListener('change', () => {
      const sec = parseFloat(startSecInput.value) || 0;
      updateOffset(sec, true);
    });
  }

  if (btnSetCurrentStart) {
    btnSetCurrentStart.addEventListener('click', () => {
      if (!state.audio.url) return;
      updateOffset(audioEl.currentTime, true);
    });
  }

  if (btnResetOffset) {
    btnResetOffset.addEventListener('click', () => {
      updateOffset(0, true);
    });
  }

  document.querySelectorAll('.btn-nudge[data-nudge]').forEach(btn => {
    btn.addEventListener('click', () => {
      const delta = parseFloat(btn.getAttribute('data-nudge')) || 0;
      updateOffset(state.audio.startOffset + delta, true);
    });
  });

  if (checkAutoSync) {
    checkAutoSync.addEventListener('change', () => {
      state.audio.autoSync = checkAutoSync.checked;
      appendTerminalLine('system', `Auto-sincronización de audio ${state.audio.autoSync ? 'ACTIVADA' : 'DESACTIVADA'}.`);
    });
  }

  // ========================================================================
  // SINCRONIZACIÓN ACOPLADA CON EL REPRODUCTOR DE VIDEO MANIM
  // ========================================================================
  if (videoEl) {
    // Al reproducir la animación
    videoEl.addEventListener('play', () => {
      if (!state.audio.url || !state.audio.autoSync) return;
      const targetTime = videoEl.currentTime + state.audio.startOffset;
      if (targetTime < (state.audio.duration || Infinity)) {
        audioEl.currentTime = targetTime;
        audioEl.play().catch(() => {});
      }
    });

    // Al pausar la animación
    videoEl.addEventListener('pause', () => {
      if (!state.audio.url || !state.audio.autoSync) return;
      audioEl.pause();
    });

    // Al desplazar la barra del video (seeking/seeked)
    const handleVideoSeek = () => {
      if (!state.audio.url || !state.audio.autoSync) return;
      const targetTime = videoEl.currentTime + state.audio.startOffset;
      if (targetTime >= 0 && targetTime <= (state.audio.duration || Infinity)) {
        audioEl.currentTime = targetTime;
      }
    };
    videoEl.addEventListener('seeking', handleVideoSeek);
    videoEl.addEventListener('seeked', handleVideoSeek);

    // Si cambia la velocidad de reproducción del video
    videoEl.addEventListener('ratechange', () => {
      if (state.audio.url) {
        audioEl.playbackRate = videoEl.playbackRate;
      }
    });

    // Al finalizar la animación
    videoEl.addEventListener('ended', () => {
      if (state.audio.url) {
        audioEl.pause();
        audioEl.currentTime = state.audio.startOffset;
      }
    });

    // Sincronización continua de deriva (Anti-drift)
    videoEl.addEventListener('timeupdate', () => {
      if (!state.audio.url || !state.audio.autoSync || videoEl.paused) return;
      const expectedTime = videoEl.currentTime + state.audio.startOffset;
      if (expectedTime < (state.audio.duration || Infinity)) {
        // Si hay una diferencia perceptible mayor a 180ms entre video y audio, corregir
        if (Math.abs(audioEl.currentTime - expectedTime) > 0.18) {
          audioEl.currentTime = expectedTime;
        }
        if (audioEl.paused) {
          audioEl.play().catch(() => {});
        }
      } else {
        if (!audioEl.paused) {
          audioEl.pause();
        }
      }
    });
  }
}

// ==========================================================================
// 13. EVENT LISTENERS GENERALES
// ==========================================================================
function initEventListeners() {
  // Botón Ejecutar del Header
  document.getElementById('btn-run').addEventListener('click', () => handleRunMain());

  // Botones de la Consola
  document.getElementById('btn-clear-console').addEventListener('click', clearTerminal);
  document.getElementById('btn-copy-console').addEventListener('click', copyTerminalLogs);

  // Descarga inteligente de video (con audio integrado si existe, o directo si no)
  const btnDownload = document.getElementById('btn-download-video');
  if (btnDownload) {
    btnDownload.addEventListener('click', async (e) => {
      // Si NO hay audio activo, se permite la descarga estándar del enlace <a>
      if (!state.audio.url || !state.audio.name) {
        return;
      }

      // Si HAY audio activo, se intercepta para multiplexar mediante FFmpeg
      e.preventDefault();
      if (btnDownload.classList.contains('disabled') || btnDownload.dataset.downloading === 'true') {
        return;
      }

      btnDownload.dataset.downloading = 'true';
      btnDownload.innerHTML = `
        <span class="spinner-sm" style="display:inline-block; width:12px; height:12px; border:2px solid rgba(255,255,255,0.3); border-top-color:#fff; border-radius:50%; animation:spin 1s infinite linear; margin-right:5px; vertical-align:middle;"></span>
        <span>Integrando audio...</span>
      `;

      appendTerminalLine('info', `Iniciando multiplexación: Seccionando audio desde ${formatSeconds(state.audio.startOffset)} para la duración exacta del video...`);

      try {
        // Garantizar que el archivo esté subido en el servidor
        if (state.audio.file) {
          await fetch('/api/upload_audio', {
            method: 'POST',
            headers: { 'X-Filename': state.audio.name },
            body: state.audio.file
          });
        }

        const res = await fetch('/api/merge_audio_video', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            audio_name: state.audio.name,
            start_offset: state.audio.startOffset,
            video_url: state.currentVideoUrl || ''
          })
        });

        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || 'Error al integrar audio y video');
        }

        const data = await res.json();
        appendTerminalLine('success', `Audio integrado exitosamente en ${data.filename} (${data.duration.toFixed(1)}s). Iniciando descarga.`);

        // Iniciar descarga del video con audio incrustado
        const tempLink = document.createElement('a');
        tempLink.href = data.download_url;
        tempLink.download = data.filename || 'EscenaAutomatica_con_audio.mp4';
        document.body.appendChild(tempLink);
        tempLink.click();
        document.body.removeChild(tempLink);
      } catch (err) {
        appendTerminalLine('error', `Error al integrar audio en el video: ${err.message}`);
      } finally {
        delete btnDownload.dataset.downloading;
        updateDownloadButtonUI();
      }
    });
  }

  // Reiniciar video y sincronizar audio
  document.getElementById('btn-restart-video').addEventListener('click', () => {
    const video = document.getElementById('manim-video-player');
    video.currentTime = 0;
    const audio = document.getElementById('manim-audio-player');
    if (audio && state.audio.url) {
      audio.currentTime = state.audio.startOffset;
      if (state.audio.autoSync) {
        audio.play().catch(() => {});
      }
    }
    video.play();
  });

  // Recargar documentación
  const btnReloadDocs = document.getElementById('btn-reload-docs');
  if (btnReloadDocs) btnReloadDocs.addEventListener('click', loadDocs);

  // Selector de temas (en drawer y en view-settings)
  document.querySelectorAll('.theme-card').forEach(card => {
    card.addEventListener('click', () => {
      const themeVal = card.getAttribute('data-theme-val');
      setTheme(themeVal);
    });
  });

  // Selector de calidad (en drawer y en view-settings)
  document.querySelectorAll('input[name="manim-quality"], input[name="manim-quality-full"]').forEach(radio => {
    radio.addEventListener('change', () => {
      setQuality(radio.value);
    });
  });

  // Atajo de teclado Escape
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      closeLeftMenu();
      const modal = document.getElementById('modal-templates');
      if (modal) modal.classList.add('hidden');
    }
  });
}

// ==========================================================================
// 17. MÓDULO: CREADOR DE SHORTS (SISTEMA DE CADENCIA MATEMÁTICA Y EJECUCIÓN)
// ==========================================================================

const shortState = {
  metodo: 'biseccion',
  tiempo_deseado: 60.0,
  max_iteraciones: 4,
  funcion: 'exp(x) - 3*(x**2)',
  a: 0.0,
  b: 1.5,
  x0: 1.5,
  x_min: -0.5,
  x_max: 2.0,
  tolerancia: 0.0001,
  codigo_generado: '',
  timerDebounce: null,
  inicializado: false
};

function onEnterShortView() {
  if (!shortState.inicializado) {
    initShortCreator();
  } else {
    recalcularShort();
  }
  renderMethodCardFormulas();
}

function renderMethodCardFormulas() {
  if (window.katex) {
    const formulas = {
      'method-card-biseccion': 'c = \\frac{a+b}{2}',
      'method-card-regla-falsa': 'c = b - f(b)\\frac{b-a}{f(b)-f(a)}',
      'method-card-newton-raphson': 'x_{n+1} = x_n - \\frac{f(x_n)}{f\'(x_n)}',
      'method-card-taylor': 'T_n(x) = \\sum_{k=0}^n \\frac{f^{(k)}(x_0)}{k!}(x-x_0)^k'
    };
    for (const [cardId, tex] of Object.entries(formulas)) {
      const card = document.getElementById(cardId);
      if (card) {
        const formulaEl = card.querySelector('.method-formula');
        if (formulaEl) {
          try {
            katex.render(tex, formulaEl, { displayMode: true, throwOnError: false });
          } catch (e) {
            formulaEl.textContent = tex;
          }
        }
      }
    }
  }
}

function selectShortMethod(selected, triggerRecalc = true) {
  if (!selected) return;

  shortState.metodo = selected;
  const methodCards = document.querySelectorAll('.short-method-card');
  methodCards.forEach(c => {
    if (c.getAttribute('data-method') === selected) {
      c.classList.add('active');
    } else {
      c.classList.remove('active');
    }
  });

  const nombres = {
    biseccion: 'Bisección',
    regla_falsa: 'Regla Falsa',
    newton_raphson: 'Newton-Raphson',
    serie_taylor: 'Serie de Taylor'
  };

  const nombreMetodo = nombres[selected] || selected;

  // Actualizar resumen en panel de estado
  const summaryMetodo = document.getElementById('short-summary-metodo');
  if (summaryMetodo) {
    summaryMetodo.textContent = nombreMetodo;
  }

  // Actualizar texto dinámico en el botón de función aleatoria para este método
  const btnCurText = document.getElementById('btn-short-random-current-text');
  if (btnCurText) {
    btnCurText.textContent = `Función Aleatoria (${nombreMetodo})`;
  }

  // Alternar visibilidad de parámetros: intervalo [a, b] vs punto inicial/centro x0
  const grpIntervalo = document.getElementById('param-group-intervalo');
  const grpPunto = document.getElementById('param-group-punto');
  const lblPunto = document.getElementById('short-label-x0');
  const iterHeading = document.getElementById('short-iter-heading');
  const iterDesc = document.getElementById('short-iter-desc');
  const iterUnit = document.getElementById('short-iter-unit');
  const iterSummaryLbl = document.getElementById('short-summary-iter-label');

  if (selected === 'serie_taylor') {
    if (grpIntervalo) grpIntervalo.classList.add('hidden');
    if (grpPunto) grpPunto.classList.remove('hidden');
    if (lblPunto) lblPunto.textContent = 'Centro de Expansión (x₀):';
    if (iterHeading) iterHeading.textContent = 'Grado del Polinomio (n)';
    if (iterDesc) iterDesc.textContent = 'Grado máximo de la aproximación polinómica';
    if (iterUnit) iterUnit.textContent = 'grados';
    if (iterSummaryLbl) iterSummaryLbl.textContent = 'Grado:';
  } else if (selected === 'newton_raphson') {
    if (grpIntervalo) grpIntervalo.classList.add('hidden');
    if (grpPunto) grpPunto.classList.remove('hidden');
    if (lblPunto) lblPunto.textContent = 'Punto Inicial (x₀):';
    if (iterHeading) iterHeading.textContent = 'Número de Iteraciones';
    if (iterDesc) iterDesc.textContent = 'Pasos sucesivos del algoritmo a animar';
    if (iterUnit) iterUnit.textContent = 'iteraciones';
    if (iterSummaryLbl) iterSummaryLbl.textContent = 'Iteraciones:';
  } else {
    if (grpIntervalo) grpIntervalo.classList.remove('hidden');
    if (grpPunto) grpPunto.classList.add('hidden');
    if (iterHeading) iterHeading.textContent = 'Número de Iteraciones';
    if (iterDesc) iterDesc.textContent = 'Pasos sucesivos del algoritmo a animar';
    if (iterUnit) iterUnit.textContent = 'iteraciones';
    if (iterSummaryLbl) iterSummaryLbl.textContent = 'Iteraciones:';
  }

  if (triggerRecalc) {
    scheduleShortRecalc();
  }
}

async function generarEjercicioAleatorio(soloMetodoActual = false) {
  const btnAll = document.getElementById('btn-short-random-all');
  const btnCur = document.getElementById('btn-short-random-current');
  const statusBadge = document.getElementById('auto-gen-status-badge');
  const statusText = document.getElementById('auto-gen-status-text');
  const summaryRow = document.getElementById('auto-gen-summary-row');
  const chipMethod = document.getElementById('auto-chip-method');
  const chipRoot = document.getElementById('auto-chip-root');
  const chipParam = document.getElementById('auto-chip-param');

  if (btnAll) btnAll.disabled = true;
  if (btnCur) btnCur.disabled = true;
  if (statusBadge) {
    statusBadge.classList.remove('hidden');
    if (statusText) statusText.textContent = 'Generando...';
  }

  try {
    let url = '/api/short/random_exercise';
    if (soloMetodoActual && shortState.metodo) {
      url += `?metodo=${encodeURIComponent(shortState.metodo)}`;
    }

    const res = await fetch(url);
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || 'Error al conectar con el generador de ejercicios');
    }

    const data = await res.json();
    if (data.status !== 'success') {
      throw new Error(data.error || 'Respuesta no exitosa del generador');
    }

    // 1. Activar el método si se ejecutó la ruleta completa
    if (!soloMetodoActual && data.metodo_id) {
      selectShortMethod(data.metodo_id, false);
    }

    // 2. Asignar los valores matemáticos generados
    shortState.funcion = data.funcion;
    shortState.a = data.a;
    shortState.b = data.b;
    shortState.x0 = data.x0;
    shortState.x_min = data.x_min;
    shortState.x_max = data.x_max;

    // 3. Reflejar en los campos del DOM
    const inputFunc = document.getElementById('short-input-func');
    if (inputFunc) inputFunc.value = data.funcion;

    const inpA = document.getElementById('short-param-a');
    if (inpA) inpA.value = data.a;

    const inpB = document.getElementById('short-param-b');
    if (inpB) inpB.value = data.b;

    const inpX0 = document.getElementById('short-param-x0');
    if (inpX0) inpX0.value = data.x0;

    const inpXmin = document.getElementById('short-param-xmin');
    if (inpXmin) inpXmin.value = data.x_min;

    const inpXmax = document.getElementById('short-param-xmax');
    if (inpXmax) inpXmax.value = data.x_max;

    // 4. Previsualización KaTeX inmediata
    if (data.latex && window.katex) {
      const target = document.getElementById('short-katex-target');
      if (target) {
        try {
          katex.render(`f(x) = ${data.latex}`, target, { displayMode: true, throwOnError: false });
        } catch {
          renderMathPreviewQuick(data.funcion);
        }
      }
    } else {
      renderMathPreviewQuick(data.funcion);
    }

    // 5. Actualizar barra de estado y resumen
    if (statusText) statusText.textContent = '¡Ejercicio generado!';
    if (summaryRow) summaryRow.classList.remove('hidden');
    if (chipMethod) chipMethod.textContent = data.metodo_nombre || data.metodo_id;
    if (chipRoot) chipRoot.innerHTML = `Raíz objetivo: <strong>${data.raiz_objetiva}</strong>`;
    if (chipParam) {
      if (data.metodo_id === 'newton_raphson') {
        chipParam.innerHTML = `Semilla x₀: <strong>${data.x0}</strong>`;
      } else if (data.metodo_id === 'serie_taylor') {
        chipParam.innerHTML = `Centro x₀: <strong>${data.x0}</strong>`;
      } else {
        chipParam.innerHTML = `Intervalo: <strong>[${data.a}, ${data.b}]</strong>`;
      }
    }

    appendTerminalLine('info', `[Modo Automático] Generado para ${data.metodo_nombre}: ${data.funcion}`);

    // 6. Recalcular parámetros de cadencia
    scheduleShortRecalc(80);

  } catch (err) {
    appendTerminalLine('error', `Error al generar ejercicio aleatorio: ${err.message}`);
    if (statusText) statusText.textContent = 'Error';
    alert('Error al generar ejercicio aleatorio: ' + err.message);
  } finally {
    if (btnAll) btnAll.disabled = false;
    if (btnCur) btnCur.disabled = false;
    setTimeout(() => {
      if (statusText && statusText.textContent === '¡Ejercicio generado!') {
        statusText.textContent = 'Listo';
      }
    }, 3000);
  }
}

function initShortCreator() {
  if (shortState.inicializado) return;

  // Renderizar KaTeX de las tarjetas de métodos
  renderMethodCardFormulas();

  // 1. Selector de Método Numérico (Cards)
  const methodCards = document.querySelectorAll('.short-method-card');
  methodCards.forEach(card => {
    card.addEventListener('click', () => {
      const selected = card.getAttribute('data-method');
      selectShortMethod(selected);
    });
  });

  // Inicializar texto del botón de método actual
  selectShortMethod(shortState.metodo, false);

  // Botones de Modo Automático / Generador de Ejercicios
  const btnRandomAll = document.getElementById('btn-short-random-all');
  if (btnRandomAll) {
    btnRandomAll.addEventListener('click', () => {
      generarEjercicioAleatorio(false);
    });
  }

  const btnRandomCurrent = document.getElementById('btn-short-random-current');
  if (btnRandomCurrent) {
    btnRandomCurrent.addEventListener('click', () => {
      generarEjercicioAleatorio(true);
    });
  }

  // 2. Chips de Presets de Tiempo (15s, 30s, 45s, 60s)
  const presetChips = document.querySelectorAll('.preset-chip');
  const sliderTiempo = document.getElementById('short-time-slider');
  const dispTiempo = document.getElementById('short-time-display-val');

  presetChips.forEach(chip => {
    chip.addEventListener('click', () => {
      presetChips.forEach(c => c.classList.remove('active'));
      chip.classList.add('active');

      const val = parseFloat(chip.getAttribute('data-time'));
      shortState.tiempo_deseado = val;

      if (sliderTiempo) sliderTiempo.value = val;
      if (dispTiempo) dispTiempo.textContent = val;

      const summaryTiempo = document.getElementById('short-summary-tiempo');
      if (summaryTiempo) summaryTiempo.textContent = `${val} s`;

      scheduleShortRecalc();
    });
  });

  // 3. Slider de Tiempo Objetivo
  if (sliderTiempo) {
    sliderTiempo.addEventListener('input', () => {
      const val = parseFloat(sliderTiempo.value);
      shortState.tiempo_deseado = val;
      if (dispTiempo) dispTiempo.textContent = val;

      const summaryTiempo = document.getElementById('short-summary-tiempo');
      if (summaryTiempo) summaryTiempo.textContent = `${val} s`;

      // Actualizar chips activos
      presetChips.forEach(chip => {
        if (parseFloat(chip.getAttribute('data-time')) === val) {
          chip.classList.add('active');
        } else {
          chip.classList.remove('active');
        }
      });

      scheduleShortRecalc(150);
    });
  }

  // 4. Input de Expresión Matemática y Ejemplos Rápidos
  const inputFunc = document.getElementById('short-input-func');
  if (inputFunc) {
    inputFunc.addEventListener('input', () => {
      shortState.funcion = inputFunc.value.trim() || 'exp(x) - 3*(x**2)';
      renderMathPreviewQuick(shortState.funcion);
      scheduleShortRecalc(350);
    });
  }

  // Chips de Ejemplos de Funciones (1-click)
  document.querySelectorAll('.func-chip').forEach(btn => {
    btn.addEventListener('click', () => {
      const fn = btn.getAttribute('data-fn');
      const a = btn.getAttribute('data-a');
      const b = btn.getAttribute('data-b');
      const x0 = btn.getAttribute('data-x0');
      const xmin = btn.getAttribute('data-xmin');
      const xmax = btn.getAttribute('data-xmax');

      if (fn && inputFunc) {
        inputFunc.value = fn;
        shortState.funcion = fn;
      }
      if (a) {
        const inpA = document.getElementById('short-param-a');
        if (inpA) inpA.value = a;
        shortState.a = parseFloat(a);
      }
      if (b) {
        const inpB = document.getElementById('short-param-b');
        if (inpB) inpB.value = b;
        shortState.b = parseFloat(b);
      }
      if (x0) {
        const inpX0 = document.getElementById('short-param-x0');
        if (inpX0) inpX0.value = x0;
        shortState.x0 = parseFloat(x0);
      }
      if (xmin) {
        const inpXmin = document.getElementById('short-param-xmin');
        if (inpXmin) inpXmin.value = xmin;
        shortState.x_min = parseFloat(xmin);
      }
      if (xmax) {
        const inpXmax = document.getElementById('short-param-xmax');
        if (inpXmax) inpXmax.value = xmax;
        shortState.x_max = parseFloat(xmax);
      }

      renderMathPreviewQuick(shortState.funcion);
      scheduleShortRecalc(50);
    });
  });

  // 5. Parámetros Numéricos Contextuales
  const inpA = document.getElementById('short-param-a');
  const inpB = document.getElementById('short-param-b');
  const inpX0 = document.getElementById('short-param-x0');
  const inpXmin = document.getElementById('short-param-xmin');
  const inpXmax = document.getElementById('short-param-xmax');

  [inpA, inpB, inpX0, inpXmin, inpXmax].forEach(inp => {
    if (inp) {
      inp.addEventListener('input', () => {
        if (inpA) shortState.a = parseFloat(inpA.value) || 0.0;
        if (inpB) shortState.b = parseFloat(inpB.value) || 1.5;
        if (inpX0) shortState.x0 = parseFloat(inpX0.value) || 1.5;
        if (inpXmin) shortState.x_min = parseFloat(inpXmin.value) || -0.5;
        if (inpXmax) shortState.x_max = parseFloat(inpXmax.value) || 2.0;
        scheduleShortRecalc(250);
      });
    }
  });

  // 6. Slider de Número de Iteraciones
  const sliderIter = document.getElementById('short-iter-slider');
  const dispIter = document.getElementById('short-iter-display-val');
  if (sliderIter) {
    sliderIter.addEventListener('input', () => {
      const val = parseInt(sliderIter.value, 10);
      shortState.max_iteraciones = val;
      if (dispIter) dispIter.textContent = val;

      const summaryIter = document.getElementById('short-summary-iter');
      if (summaryIter) summaryIter.textContent = val;

      scheduleShortRecalc(150);
    });
  }

  // 7. Botón: Generar Video (Ejecución en segundo plano con Consola y Spinner)
  const btnGenerateVideo = document.getElementById('btn-short-generate-video');
  if (btnGenerateVideo) {
    btnGenerateVideo.addEventListener('click', async () => {
      if (state.isRendering) return;

      handleShortStatusUpdate({ state: 'rendering' });

      appendShortTerminalLine('info', '==========================================================');
      appendShortTerminalLine('progress', `Compilando animación Manim para el método ${shortState.metodo.toUpperCase()} (${shortState.tiempo_deseado}s)...`);

      try {
        // 1. Generar código y guardarlo en main.py
        const genRes = await fetch('/api/short/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...shortState, save_to_main: true })
        });
        const genData = await genRes.json();
        if (genData.status !== 'success') {
          throw new Error(genData.error || 'Fallo al generar código');
        }

        shortState.codigo_generado = genData.codigo;
        appendShortTerminalLine('success', `Código generado con cadencia temporal calibrada (${genData.tiempo_estimado}s).`);
        appendShortTerminalLine('info', `Iniciando proceso Manim (Calidad: ${state.quality})...`);

        // 2. Ejecutar main.py en backend
        const runRes = await fetch('/api/run_main', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: genData.codigo, file: 'main.py', quality: state.quality })
        });
        if (!runRes.ok) {
          const runErr = await runRes.json();
          throw new Error(runErr.error || 'Fallo al iniciar el motor Manim');
        }

      } catch (err) {
        appendShortTerminalLine('error', `Error en la generación: ${err.message}`);
        handleShortStatusUpdate({ state: 'error' });
      }
    });
  }

  // 8. Botón: Cargar en Editor (main.py)
  const btnToEditor = document.getElementById('btn-short-to-editor');
  if (btnToEditor) {
    btnToEditor.addEventListener('click', async () => {
      btnToEditor.disabled = true;
      const originalText = btnToEditor.innerHTML;
      btnToEditor.innerHTML = '<span>Guardando...</span>';

      try {
        const res = await fetch('/api/short/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...shortState, save_to_main: true })
        });
        const data = await res.json();
        if (data.status === 'success') {
          appendTerminalLine('success', `Código de Short (${data.metodo.toUpperCase()}) guardado en main.py.`);
          await loadMainPy();
          switchView('view-manual');
        } else {
          alert('Error al generar código: ' + (data.error || 'Desconocido'));
        }
      } catch (err) {
        alert('Error de conexión: ' + err.message);
      } finally {
        btnToEditor.disabled = false;
        btnToEditor.innerHTML = originalText;
      }
    });
  }

  // 9. Controles de la Consola de la Vista Short
  const btnClearConsole = document.getElementById('btn-short-clear-console');
  if (btnClearConsole) {
    btnClearConsole.addEventListener('click', () => {
      const term = document.getElementById('short-terminal-screen');
      if (term) {
        term.innerHTML = '<div class="term-line term-system"><span class="term-timestamp">[00:00:00]</span> Consola limpiada por el usuario.</div>';
      }
    });
  }

  const btnCopyConsole = document.getElementById('btn-short-copy-console');
  if (btnCopyConsole) {
    btnCopyConsole.addEventListener('click', () => {
      const term = document.getElementById('short-terminal-screen');
      if (term) {
        navigator.clipboard.writeText(term.innerText).then(() => {
          const orig = btnCopyConsole.textContent;
          btnCopyConsole.textContent = 'Copiado';
          setTimeout(() => { btnCopyConsole.textContent = orig; }, 1500);
        });
      }
    });
  }

  // 10. Botón Reiniciar Reproducción de Video Short
  const btnRestartShort = document.getElementById('short-btn-restart-video');
  if (btnRestartShort) {
    btnRestartShort.addEventListener('click', () => {
      const player = document.getElementById('short-video-player');
      if (player) {
        player.currentTime = 0;
        player.play().catch(() => {});
      }
    });
  }

  shortState.inicializado = true;
  recalcularShort();
}

function scheduleShortRecalc(delayMs = 250) {
  if (shortState.timerDebounce) {
    clearTimeout(shortState.timerDebounce);
  }
  shortState.timerDebounce = setTimeout(() => {
    recalcularShort();
  }, delayMs);
}

function renderMathPreviewQuick(formulaStr) {
  const target = document.getElementById('short-katex-target');
  if (!target) return;

  if (window.katex) {
    try {
      let clean = formulaStr.trim()
        .replace(/\*\*/g, '^')
        .replace(/\*/g, ' \\cdot ')
        .replace(/exp\(([^)]+)\)/g, 'e^{$1}')
        .replace(/math\./g, '')
        .replace(/sin\(/g, '\\sin(')
        .replace(/cos\(/g, '\\cos(')
        .replace(/tan\(/g, '\\tan(')
        .replace(/sqrt\(([^)]+)\)/g, '\\sqrt{$1}');
      katex.render(`f(x) = ${clean}`, target, { displayMode: true, throwOnError: false });
    } catch {
      target.textContent = `f(x) = ${formulaStr}`;
    }
  } else {
    target.textContent = `f(x) = ${formulaStr}`;
  }
}

async function recalcularShort() {
  try {
    const res = await fetch('/api/short/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...shortState, save_to_main: false })
    });

    if (!res.ok) return;
    const data = await res.json();
    if (data.status !== 'success') return;

    shortState.codigo_generado = data.codigo;

    // Actualizar encabezados y métricas clave
    const quickCompat = document.getElementById('short-quick-compat-pill');
    if (quickCompat) quickCompat.textContent = `${Number(data.tiempo_objetivo).toFixed(0)} s`;

    const quickFactor = document.getElementById('short-quick-factor-val');
    if (quickFactor) {
      const escala = data.escala_tiempo !== undefined ? data.escala_tiempo : data.factor_escalado;
      quickFactor.textContent = `${Number(escala).toFixed(2)}x`;
    }

    // Actualizar resumen en panel de estado
    const summaryMetodo = document.getElementById('short-summary-metodo');
    if (summaryMetodo) {
      const nombres = {
        biseccion: 'Bisección',
        regla_falsa: 'Regla Falsa',
        newton_raphson: 'Newton-Raphson',
        serie_taylor: 'Serie de Taylor'
      };
      summaryMetodo.textContent = nombres[shortState.metodo] || shortState.metodo;
    }

    const summaryTiempo = document.getElementById('short-summary-tiempo');
    if (summaryTiempo) summaryTiempo.textContent = `${Number(shortState.tiempo_deseado).toFixed(0)} s`;

    const summaryIter = document.getElementById('short-summary-iter');
    if (summaryIter) summaryIter.textContent = shortState.max_iteraciones;

    // Renderizado KaTeX de la Función y su Derivada
    if (window.katex && data.info_funcion) {
      const targetMain = document.getElementById('short-katex-target');
      if (targetMain && data.info_funcion.latex_func) {
        try {
          katex.render(data.info_funcion.latex_func, targetMain, { displayMode: true, throwOnError: false });
        } catch {
          targetMain.textContent = data.info_funcion.latex_func;
        }
      }

      const targetDeriv = document.getElementById('short-katex-deriv-target');
      if (targetDeriv) {
        if (shortState.metodo === 'newton_raphson' && data.info_funcion.latex_deriv) {
          targetDeriv.classList.remove('hidden');
          try {
            katex.render(data.info_funcion.latex_deriv, targetDeriv, { displayMode: true, throwOnError: false });
          } catch {
            targetDeriv.textContent = data.info_funcion.latex_deriv;
          }
        } else {
          targetDeriv.classList.add('hidden');
          targetDeriv.innerHTML = '';
        }
      }
    }

  } catch (err) {
    console.error('Error al recalcular Short:', err);
  }
}

function appendShortTerminalLine(level, text) {
  const terminal = document.getElementById('short-terminal-screen');
  if (!terminal) return;
  const line = document.createElement('div');
  line.className = `term-line term-${level}`;

  const now = new Date();
  const timeStr = now.toTimeString().split(' ')[0];
  line.innerHTML = `<span class="term-timestamp">[${timeStr}]</span> ${escapeHtml(text)}`;

  terminal.appendChild(line);
  terminal.scrollTop = terminal.scrollHeight;
}

function handleShortStatusUpdate(data) {
  const heading = document.getElementById('short-status-heading');
  const dot = document.getElementById('short-status-indicator-dot');
  const stateIdle = document.getElementById('short-state-idle');
  const stateLoading = document.getElementById('short-state-loading');
  const statePlayer = document.getElementById('short-state-player');
  const btnGen = document.getElementById('btn-short-generate-video');
  const btnGenText = document.getElementById('btn-short-generate-text');

  if (data.state === 'rendering') {
    if (heading) heading.textContent = 'Generando Video...';
    if (dot) dot.className = 'short-status-indicator-dot pulsating';
    if (stateIdle) stateIdle.classList.add('hidden');
    if (statePlayer) statePlayer.classList.add('hidden');
    if (stateLoading) stateLoading.classList.remove('hidden');
    if (btnGen) btnGen.disabled = true;
    if (btnGenText) btnGenText.textContent = 'Compilando...';
  } else if (data.state === 'success') {
    if (heading) heading.textContent = 'Video Generado con Éxito';
    if (dot) dot.className = 'short-status-indicator-dot ready';
    if (stateLoading) stateLoading.classList.add('hidden');
    if (stateIdle) stateIdle.classList.add('hidden');
    if (statePlayer) statePlayer.classList.remove('hidden');
    if (btnGen) btnGen.disabled = false;
    if (btnGenText) btnGenText.textContent = 'Generar Video';
    if (data.video_url) {
      loadShortVideoPlayer(data.video_url);
    }
  } else if (data.state === 'error') {
    if (heading) heading.textContent = 'Error en la Generación';
    if (dot) dot.className = 'short-status-indicator-dot error';
    if (stateLoading) stateLoading.classList.add('hidden');
    if (stateIdle) stateIdle.classList.remove('hidden');
    if (statePlayer) statePlayer.classList.add('hidden');
    if (btnGen) btnGen.disabled = false;
    if (btnGenText) btnGenText.textContent = 'Reintentar Generación';
  }
}

function loadShortVideoPlayer(videoUrl) {
  const player = document.getElementById('short-video-player');
  const source = document.getElementById('short-video-source');
  const dlBtn = document.getElementById('short-btn-download-video');
  const btnRestart = document.getElementById('short-btn-restart-video');
  const metaBadge = document.getElementById('short-video-meta');
  const statePlayer = document.getElementById('short-state-player');
  const stateIdle = document.getElementById('short-state-idle');
  const stateLoading = document.getElementById('short-state-loading');

  if (stateIdle) stateIdle.classList.add('hidden');
  if (stateLoading) stateLoading.classList.add('hidden');
  if (statePlayer) statePlayer.classList.remove('hidden');

  if (source && player) {
    source.src = videoUrl;
    player.load();
    player.onloadeddata = () => {
      if (metaBadge) {
        metaBadge.textContent = `${player.videoWidth}x${player.videoHeight} • ${player.duration.toFixed(1)}s`;
      }
      if (dlBtn) {
        dlBtn.href = videoUrl;
        dlBtn.classList.remove('disabled');
      }
      if (btnRestart) {
        btnRestart.disabled = false;
      }
      player.play().catch(() => {});
    };
  }
}

