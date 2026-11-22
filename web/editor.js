/**
 * EDITOR DE ESCENAS — cliente del API `/api/editor/*`.
 *
 * El IR es la fuente de verdad. Guardar renormaliza y regenera el código en el
 * servidor; renderizar crea un job aislado cuyo progreso se sigue por polling.
 */
(function () {
  'use strict';

  const state = {
    loaded: false,
    projectId: null,
    sceneId: null,
    ir: null,
    jobId: null,
    pollTimer: null,
    busy: false,
  };

  const $ = (id) => document.getElementById(id);

  const els = {};
  function cacheElements() {
    [
      'ed-title', 'ed-format', 'ed-quality', 'ed-status',
      'ed-save', 'ed-render', 'ed-cancel', 'ed-auto-preview',
      'ed-fn-latex', 'ed-fn-python',
      'ed-domain-min', 'ed-domain-max', 'ed-a', 'ed-b',
      'ed-tolerance', 'ed-iterations',
      'ed-hud', 'ed-accent', 'ed-result-color', 'ed-grid',
      'ed-beats', 'ed-total-duration',
      'ed-video', 'ed-video-empty', 'ed-log', 'ed-job-badge', 'ed-render-meta',
      'ed-chat-log', 'ed-chat-form', 'ed-chat-input', 'ed-auto-render',
    ].forEach((id) => {
      els[id] = $(id);
    });
  }

  // ------------------------------------------------------------------
  // HTTP
  // ------------------------------------------------------------------
  async function api(path, options) {
    const config = Object.assign({ cache: 'no-store' }, options || {});
    if (config.body && typeof config.body !== 'string') {
      config.headers = Object.assign({ 'Content-Type': 'application/json' }, config.headers || {});
      config.body = JSON.stringify(config.body);
    }
    const response = await fetch(path, config);
    const text = await response.text();
    let data = null;
    try {
      data = text ? JSON.parse(text) : null;
    } catch (error) {
      data = { error: text };
    }
    if (!response.ok) {
      throw new Error((data && data.error) || `Error ${response.status}`);
    }
    return data;
  }

  // ------------------------------------------------------------------
  // Estado visual
  // ------------------------------------------------------------------
  function setStatus(text, kind) {
    els['ed-status'].textContent = text;
    els['ed-status'].dataset.kind = kind || 'info';
  }

  function setBusy(busy) {
    state.busy = busy;
    els['ed-save'].disabled = busy;
    els['ed-render'].disabled = busy;
  }

  function setJobBadge(status) {
    const badge = els['ed-job-badge'];
    badge.textContent = status;
    badge.dataset.status = status;
    els['ed-cancel'].classList.toggle('hidden', !['queued', 'running'].includes(status));
  }

  function appendLog(lines) {
    if (!lines || !lines.length) return;
    const pre = els['ed-log'];
    const text = Array.isArray(lines) ? lines.join('\n') : String(lines);
    pre.textContent = text;
    pre.scrollTop = pre.scrollHeight;
  }

  function appendChat(role, text) {
    const entry = document.createElement('div');
    entry.className = `ed-chat-msg ed-chat-${role}`;
    entry.textContent = text;
    els['ed-chat-log'].appendChild(entry);
    els['ed-chat-log'].scrollTop = els['ed-chat-log'].scrollHeight;
  }

  // ------------------------------------------------------------------
  // Formulario <-> IR
  // ------------------------------------------------------------------
  function fillSelect(select, items, selected) {
    select.innerHTML = '';
    items.forEach((item) => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = item.label;
      if (item.id === selected) option.selected = true;
      select.appendChild(option);
    });
  }

  function renderForm(ir) {
    state.ir = ir;
    els['ed-title'].value = ir.title || '';
    els['ed-format'].value = ir.format || '16:9';
    els['ed-fn-latex'].value = ir.function.latex || '';
    els['ed-fn-python'].value = ir.function.python || '';
    els['ed-domain-min'].value = ir.function.domain[0];
    els['ed-domain-max'].value = ir.function.domain[1];
    els['ed-a'].value = ir.params.a;
    els['ed-b'].value = ir.params.b;
    els['ed-tolerance'].value = ir.params.tolerance;
    els['ed-iterations'].value = ir.params.max_iterations;
    els['ed-hud'].value = (ir.layout && ir.layout.hud) || 'UR';
    els['ed-accent'].value = (ir.layout && ir.layout.accent) || '#89b4fa';
    els['ed-result-color'].value = (ir.layout && ir.layout.result_color) || '#a6e3a1';
    els['ed-grid'].checked = Boolean(ir.layout && ir.layout.show_grid);
    renderBeats();
  }

  function renderBeats() {
    const container = els['ed-beats'];
    container.innerHTML = '';
    const beats = (state.ir && state.ir.beats) || [];

    beats.forEach((beat, index) => {
      const row = document.createElement('div');
      row.className = 'ed-beat-row';
      row.dataset.index = String(index);

      const enabled = document.createElement('input');
      enabled.type = 'checkbox';
      enabled.checked = Boolean(beat.enabled);
      enabled.title = 'Incluir este beat';
      enabled.addEventListener('change', () => {
        beat.enabled = enabled.checked;
        updateDuration();
        scheduleAutoRender();
      });

      const label = document.createElement('input');
      label.type = 'text';
      label.className = 'ed-beat-label';
      label.value = beat.label || beat.id;
      label.maxLength = 120;
      label.addEventListener('input', () => {
        beat.label = label.value;
        scheduleAutoRender();
      });

      const kind = document.createElement('span');
      kind.className = 'ed-beat-kind';
      kind.textContent = beat.kind;

      const anim = document.createElement('input');
      anim.type = 'number';
      anim.min = '0.1';
      anim.max = '10';
      anim.step = '0.1';
      anim.value = beat.t_anim;
      anim.title = 'Segundos de animación';
      anim.addEventListener('input', () => {
        beat.t_anim = Number(anim.value);
        updateDuration();
        scheduleAutoRender();
      });

      const wait = document.createElement('input');
      wait.type = 'number';
      wait.min = '0';
      wait.max = '10';
      wait.step = '0.1';
      wait.value = beat.t_wait;
      wait.title = 'Segundos en pantalla';
      wait.addEventListener('input', () => {
        beat.t_wait = Number(wait.value);
        updateDuration();
        scheduleAutoRender();
      });

      row.append(enabled, kind, label, anim, wait);
      container.appendChild(row);
    });

    const header = document.createElement('div');
    header.className = 'ed-beat-row ed-beat-head';
    header.innerHTML = '<span></span><span>tipo</span><span>etiqueta</span><span>anim</span><span>espera</span>';
    container.prepend(header);
    updateDuration();
  }

  function updateDuration() {
    const beats = (state.ir && state.ir.beats) || [];
    const total = beats.reduce(
      (sum, beat) => sum + (beat.enabled ? (Number(beat.t_anim) || 0) + (Number(beat.t_wait) || 0) : 0),
      0,
    );
    els['ed-total-duration'].textContent = `${total.toFixed(1)} s en pantalla`;
  }

  function collectIr() {
    const ir = JSON.parse(JSON.stringify(state.ir));
    ir.title = els['ed-title'].value.trim() || 'Escena';
    ir.format = els['ed-format'].value;
    ir.function.latex = els['ed-fn-latex'].value.trim();
    ir.function.python = els['ed-fn-python'].value.trim();
    ir.function.domain = [Number(els['ed-domain-min'].value), Number(els['ed-domain-max'].value)];
    ir.params.a = Number(els['ed-a'].value);
    ir.params.b = Number(els['ed-b'].value);
    ir.params.tolerance = Number(els['ed-tolerance'].value);
    ir.params.max_iterations = Number(els['ed-iterations'].value);
    ir.layout = ir.layout || {};
    ir.layout.hud = els['ed-hud'].value;
    ir.layout.accent = els['ed-accent'].value;
    ir.layout.result_color = els['ed-result-color'].value;
    ir.layout.show_grid = els['ed-grid'].checked;
    return ir;
  }

  // ------------------------------------------------------------------
  // Carga
  // ------------------------------------------------------------------
  async function loadScene(sceneId) {
    const payload = await api(`/api/editor/scenes/${sceneId}`);
    state.sceneId = payload.id;
    state.projectId = payload.project_id;
    renderForm(payload.ir);
    setStatus(`Escena cargada · ${payload.title}`, 'ok');

    if (payload.active_job) {
      pollJob(payload.active_job);
    } else if (payload.latest_render && payload.latest_render.video_url) {
      showVideo(payload.latest_render);
      setJobBadge('listo');
    } else {
      setJobBadge('inactivo');
    }
    return payload;
  }

  async function loadWorkspace() {
    const bootstrap = (await window.manimSession.bootstrap) || (await api('/api/editor/bootstrap'));
    fillSelect(els['ed-format'], bootstrap.formats, '16:9');
    fillSelect(els['ed-quality'], bootstrap.qualities, bootstrap.default_quality);

    let project = (bootstrap.projects || [])[0];
    if (!project) {
      const created = await api('/api/editor/projects', { method: 'POST', body: { name: 'Mi primer proyecto' } });
      project = created.project;
    }

    const detail = await api(`/api/editor/projects/${project.id}`);
    let scene = (detail.scenes || [])[0];
    if (!scene) {
      const created = await api(`/api/editor/projects/${project.id}/scenes`, {
        method: 'POST',
        body: { title: 'Bisección' },
      });
      scene = created.scene;
    }

    await loadScene(scene.id);
    state.loaded = true;
  }

  async function activate() {
    if (!state.loaded) {
      try {
        await loadWorkspace();
      } catch (error) {
        setStatus(`No se pudo cargar el editor: ${error.message}`, 'error');
      }
    }
  }

  // ------------------------------------------------------------------
  // Guardar / renderizar
  // ------------------------------------------------------------------
  async function saveScene() {
    if (!state.sceneId) throw new Error('Todavía no hay una escena cargada.');
    const ir = collectIr();
    const payload = await api(`/api/editor/scenes/${state.sceneId}`, {
      method: 'PUT',
      body: { ir, title: ir.title },
    });
    renderForm(payload.ir);
    setStatus('Escena guardada y código regenerado.', 'ok');
    return payload;
  }

  async function renderScene() {
    const format = els['ed-format'].value;
    const quality = els['ed-quality'].value;
    const job = await api(`/api/editor/scenes/${state.sceneId}/render`, {
      method: 'POST',
      body: { format, quality },
    });
    appendLog([`> Render ${format} · ${quality}`]);
    pollJob(job.job.id);
    return job.job;
  }

  function showVideo(render) {
    if (!render || !render.video_url) return;
    els['ed-video'].src = render.video_url;
    els['ed-video'].classList.add('has-video');
    els['ed-video-empty'].classList.add('hidden');
    els['ed-render-meta'].textContent = `${render.format} · ${render.quality}`;
  }

  function pollJob(jobId) {
    state.jobId = jobId;
    setJobBadge('queued');
    clearInterval(state.pollTimer);
    state.pollTimer = setInterval(() => tick(jobId), 1200);
    tick(jobId);
  }

  async function tick(jobId) {
    if (!state.jobId) return;
    let payload;
    try {
      payload = await api(`/api/editor/jobs/${jobId}`);
    } catch (error) {
      clearInterval(state.pollTimer);
      setJobBadge('error');
      setStatus(`No se pudo consultar el job: ${error.message}`, 'error');
      return;
    }

    const job = payload.job;
    setJobBadge(job.status);
    appendLog(job.logs || []);

    if (job.status === 'success') {
      clearInterval(state.pollTimer);
      showVideo(job);
      setStatus('Render completado.', 'ok');
      setJobBadge('listo');
    } else if (['error', 'cancelled'].includes(job.status)) {
      clearInterval(state.pollTimer);
      setStatus(job.error || `Render ${job.status}.`, 'error');
    } else {
      setStatus(`Render ${job.status}…`, 'info');
    }
  }

  async function cancelJob() {
    if (!state.jobId) return;
    await api(`/api/editor/jobs/${state.jobId}/cancel`, { method: 'POST', body: {} });
    setStatus('Render cancelado.', 'info');
    setJobBadge('cancelled');
    clearInterval(state.pollTimer);
  }

  // ------------------------------------------------------------------
  // Auto-render con debounce
  // ------------------------------------------------------------------
  let autoTimer = null;

  function scheduleAutoRender() {
    if (!state.sceneId || !els['ed-auto-preview'].checked) return;
    clearTimeout(autoTimer);
    setStatus('Cambios pendientes…', 'info');
    autoTimer = setTimeout(async () => {
      if (state.busy) {
        scheduleAutoRender();
        return;
      }
      setBusy(true);
      try {
        await saveScene();
        await renderScene();
      } catch (error) {
        setStatus(error.message, 'error');
      } finally {
        setBusy(false);
      }
    }, 1500);
  }

  // ------------------------------------------------------------------
  // Asistente
  // ------------------------------------------------------------------
  async function sendMessage(event) {
    event.preventDefault();
    const message = els['ed-chat-input'].value.trim();
    if (!message || !state.sceneId) return;

    appendChat('user', message);
    els['ed-chat-input'].value = '';
    setBusy(true);
    try {
      const result = await api(`/api/editor/scenes/${state.sceneId}/chat`, {
        method: 'POST',
        body: {
          message,
          auto_render: els['ed-auto-render'].checked,
          quality: els['ed-quality'].value,
        },
      });
      appendChat('assistant', result.reply || 'Sin respuesta.');
      renderForm(result.ir);
      if (result.job) {
        pollJob(result.job.id);
      }
      setStatus('Cambios aplicados por el asistente.', 'ok');
    } catch (error) {
      appendChat('assistant', `Error: ${error.message}`);
      setStatus(error.message, 'error');
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------------
  // Eventos
  // ------------------------------------------------------------------
  function bind() {
    els['ed-save'].addEventListener('click', async () => {
      setBusy(true);
      try {
        await saveScene();
      } catch (error) {
        setStatus(error.message, 'error');
      } finally {
        setBusy(false);
      }
    });

    els['ed-render'].addEventListener('click', async () => {
      setBusy(true);
      try {
        await saveScene();
        await renderScene();
      } catch (error) {
        setStatus(error.message, 'error');
      } finally {
        setBusy(false);
      }
    });

    els['ed-cancel'].addEventListener('click', () => {
      cancelJob().catch((error) => setStatus(error.message, 'error'));
    });

    els['ed-chat-form'].addEventListener('submit', sendMessage);

    els['ed-chat-input'].addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
        event.preventDefault();
        els['ed-chat-form'].requestSubmit();
      }
    });

    els['ed-format'].addEventListener('change', () => {
      if (state.ir) state.ir.format = els['ed-format'].value;
      scheduleAutoRender();
    });

    const autoFields = [
      'ed-title', 'ed-fn-latex', 'ed-fn-python',
      'ed-domain-min', 'ed-domain-max', 'ed-a', 'ed-b',
      'ed-tolerance', 'ed-iterations', 'ed-hud',
      'ed-accent', 'ed-result-color', 'ed-grid',
    ];
    autoFields.forEach((id) => {
      const element = els[id];
      if (!element) return;
      element.addEventListener('change', scheduleAutoRender);
      element.addEventListener('input', scheduleAutoRender);
    });
  }

  function init() {
    cacheElements();
    if (!els['ed-save']) return;
    bind();
    window.EditorView = { activate };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
