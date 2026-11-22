/**
 * EDITOR DE ESCENAS — cliente del API `/api/editor/*`.
 *
 * El IR es la fuente de verdad. Guardar renormaliza y regenera el código en el
 * servidor; renderizar crea un job aislado. El asistente solo propone parches:
 * nada se aplica hasta que el usuario pulsa «Aplicar».
 */
(function () {
  'use strict';

  const state = {
    loaded: false,
    projectId: null,
    sceneId: null,
    ir: null,
    revision: 1,
    code: '',
    proposal: null,
    previousIr: null,
    jobId: null,
    pollTimer: null,
    busy: false,
    codeMirror: null,
  };

  const $ = (id) => document.getElementById(id);
  const els = {};

  function cacheElements() {
    [
      'ed-title', 'ed-revision', 'ed-format', 'ed-quality', 'ed-status',
      'ed-save', 'ed-render', 'ed-cancel', 'ed-auto-preview',
      'ed-fn-latex', 'ed-fn-latex-preview', 'ed-fn-python',
      'ed-a', 'ed-b', 'ed-tolerance', 'ed-iterations',
      'ed-domain-min', 'ed-domain-max', 'ed-hud', 'ed-accent',
      'ed-result-color', 'ed-grid', 'ed-audio-offset',
      'ed-beats', 'ed-total-duration',
      'ed-ir', 'ed-code', 'ed-diff', 'ed-copy-code',
      'ed-video', 'ed-video-frame', 'ed-video-empty', 'ed-math-placeholder',
      'ed-log', 'ed-job-badge', 'ed-render-meta', 'ed-progress',
      'ed-chat-history', 'ed-chat-log', 'ed-chat-count', 'ed-chat-form', 'ed-chat-input',
      'ed-proposal', 'ed-proposal-title', 'ed-proposal-summary',
      'ed-proposal-reply', 'ed-proposal-diff',
      'ed-apply', 'ed-discard', 'ed-undo',
    ].forEach((id) => { els[id] = $(id); });
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
    if (!els['ed-status']) return;
    els['ed-status'].textContent = text;
    els['ed-status'].dataset.kind = kind || 'info';
  }

  function setBusy(busy) {
    state.busy = busy;
    ['ed-save', 'ed-render'].forEach((id) => {
      if (els[id]) els[id].disabled = busy;
    });
  }

  function setJobBadge(status) {
    const badge = els['ed-job-badge'];
    if (!badge) return;
    badge.textContent = status;
    badge.dataset.status = status;
    els['ed-cancel'].classList.toggle('hidden', !['queued', 'running'].includes(status));
    els['ed-progress'].classList.toggle('is-running', ['queued', 'running'].includes(status));
  }

  function appendLog(lines) {
    if (!lines || !lines.length) return;
    const pre = els['ed-log'];
    pre.textContent = Array.isArray(lines) ? lines.join('\n') : String(lines);
    pre.scrollTop = pre.scrollHeight;
  }

  function appendChat(role, text) {
    const entry = document.createElement('div');
    entry.className = `ed-chat-msg ed-chat-${role}`;
    if (window.ManimMath && role === 'assistant') {
      window.ManimMath.renderMathInText(entry, text);
    } else {
      entry.textContent = text;
    }
    els['ed-chat-log'].appendChild(entry);
    els['ed-chat-log'].scrollTop = els['ed-chat-log'].scrollHeight;
    els['ed-chat-count'].textContent = `(${els['ed-chat-log'].children.length})`;
  }

  // ------------------------------------------------------------------
  // Formulario <-> IR
  // ------------------------------------------------------------------
  function fillSelect(select, items, selected) {
    select.innerHTML = '';
    (items || []).forEach((item) => {
      const option = document.createElement('option');
      option.value = item.id;
      option.textContent = item.label || item.id;
      if (item.id === selected) option.selected = true;
      select.appendChild(option);
    });
  }

  function updateMathPreview() {
    const tex = (els['ed-fn-latex'] && els['ed-fn-latex'].value.trim()) || '';
    if (window.ManimMath) {
      window.ManimMath.renderKatex(els['ed-fn-latex-preview'], tex, { displayMode: false });
      window.ManimMath.renderKatex(els['ed-math-placeholder'], tex, { displayMode: true });
    } else {
      els['ed-fn-latex-preview'].textContent = tex;
      els['ed-math-placeholder'].textContent = tex;
    }
  }

  function renderForm(ir, revision) {
    state.ir = ir;
    if (revision !== undefined) state.revision = revision;
    els['ed-title'].value = ir.title || '';
    els['ed-revision'].textContent = `r${state.revision}`;
    els['ed-format'].value = ir.format || '16:9';
    els['ed-fn-latex'].value = ir.function.latex || '';
    els['ed-fn-python'].value = ir.function.python || '';
    els['ed-a'].value = ir.params.a;
    els['ed-b'].value = ir.params.b;
    els['ed-tolerance'].value = ir.params.tolerance;
    els['ed-iterations'].value = ir.params.max_iterations;
    els['ed-domain-min'].value = ir.function.domain[0];
    els['ed-domain-max'].value = ir.function.domain[1];
    els['ed-hud'].value = (ir.layout && ir.layout.hud) || 'UR';
    els['ed-accent'].value = (ir.layout && ir.layout.accent) || '#89b4fa';
    els['ed-result-color'].value = (ir.layout && ir.layout.result_color) || '#a6e3a1';
    els['ed-grid'].checked = Boolean(ir.layout && ir.layout.show_grid);
    els['ed-audio-offset'].value = (ir.narration && ir.narration.offset) || 0;

    els['ed-video-frame'].dataset.format = ir.format || '16:9';
    els['ed-ir'].value = JSON.stringify(ir, null, 2);
    updateMathPreview();
    renderBeats();
  }

  function setCode(code) {
    state.code = code || '';
    els['ed-code'].value = state.code;
    if (state.codeMirror) state.codeMirror.setValue(state.code);
  }

  function renderBeats() {
    const container = els['ed-beats'];
    container.innerHTML = '';
    const beats = (state.ir && state.ir.beats) || [];

    beats.forEach((beat, index) => {
      const row = document.createElement('div');
      row.className = 'ed-beat-row';

      const enabled = document.createElement('input');
      enabled.type = 'checkbox';
      enabled.checked = Boolean(beat.enabled);
      enabled.title = 'Incluir este beat';
      enabled.addEventListener('change', () => {
        beat.enabled = enabled.checked;
        updateDuration();
        scheduleAutoRender();
      });

      const kind = document.createElement('span');
      kind.className = 'ed-beat-kind';
      kind.textContent = beat.kind;

      const label = document.createElement('input');
      label.type = 'text';
      label.className = 'ed-beat-label';
      label.value = beat.label || beat.id;
      label.maxLength = 120;
      label.addEventListener('input', () => {
        beat.label = label.value;
        scheduleAutoRender();
      });

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
    ir.narration = ir.narration || {};
    ir.narration.offset = Number(els['ed-audio-offset'].value) || 0;
    return ir;
  }

  // ------------------------------------------------------------------
  // Carga
  // ------------------------------------------------------------------
  async function loadScene(sceneId) {
    const payload = await api(`/api/editor/scenes/${sceneId}`);
    state.sceneId = payload.id;
    state.projectId = payload.project_id;
    renderForm(payload.ir, payload.revision);
    setCode(payload.code);
    setStatus(`Escena cargada · ${payload.title}`, 'ok');

    const history = await api(`/api/editor/scenes/${sceneId}/chat`);
    els['ed-chat-log'].innerHTML = '';
    (history.messages || []).forEach((item) => appendChat(item.role, item.content));

    if (payload.active_job) {
      pollJob(payload.active_job.id);
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
    fillSelect(els['ed-format'], bootstrap.formats, bootstrap.default_format || '16:9');
    fillSelect(els['ed-quality'], bootstrap.qualities, bootstrap.default_quality);
    if (bootstrap.llm && bootstrap.llm.mock) {
      setStatus('Asistente local (sin clave LLM). Puedes probar los comandos habituales.', 'info');
    }

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
  async function saveScene(sync) {
    if (!state.sceneId) throw new Error('Todavía no hay una escena cargada.');
    const ir = collectIr();
    const payload = await api(`/api/editor/scenes/${state.sceneId}`, {
      method: 'PUT',
      body: { ir, title: ir.title },
    });
    if (sync !== false) renderForm(payload.ir, payload.revision);
    else state.revision = payload.revision;
    setCode(payload.code);
    els['ed-revision'].textContent = `r${state.revision}`;
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
    els['ed-video-frame'].dataset.format = render.format || '16:9';
  }

  function pollJob(jobId) {
    state.jobId = jobId;
    setJobBadge('queued');
    clearInterval(state.pollTimer);
    state.pollTimer = setInterval(() => tick(jobId), 1200);
    tick(jobId);
  }

  async function tick(jobId) {
    if (!state.jobId || state.jobId !== jobId) return;
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
  const debouncedMath = window.ManimMath
    ? window.ManimMath.debounce(updateMathPreview, 120)
    : updateMathPreview;

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
        await saveScene(false);
        await renderScene();
      } catch (error) {
        setStatus(error.message, 'error');
      } finally {
        setBusy(false);
      }
    }, 1500);
  }

  // ------------------------------------------------------------------
  // Asistente: propuesta -> revisión -> aplicación
  // ------------------------------------------------------------------
  function showProposal(result) {
    state.proposal = result;
    state.previousIr = JSON.parse(JSON.stringify(state.ir));
    els['ed-proposal'].classList.remove('hidden');
    els['ed-proposal-title'].textContent = 'Propuesta del asistente';
    els['ed-proposal-summary'].textContent = (result.summary || []).join(' · ') || 'sin cambios';
    if (window.ManimMath) {
      window.ManimMath.renderMathInText(els['ed-proposal-reply'], result.reply || '');
    } else {
      els['ed-proposal-reply'].textContent = result.reply || '';
    }
    els['ed-proposal-diff'].textContent = result.code_diff || 'Sin cambios en el código.';
    els['ed-diff'].textContent = result.code_diff || 'Sin cambios en el código.';
    els['ed-undo'].classList.add('hidden');
  }

  function clearProposal() {
    state.proposal = null;
    els['ed-proposal'].classList.add('hidden');
  }

  async function sendMessage(event) {
    if (event) event.preventDefault();
    const message = els['ed-chat-input'].value.trim();
    if (!message || !state.sceneId || state.busy) return;

    appendChat('user', message);
    els['ed-chat-input'].value = '';
    setBusy(true);
    try {
      const result = await api(`/api/editor/scenes/${state.sceneId}/chat`, {
        method: 'POST',
        body: {
          message,
          focus: document.activeElement && document.activeElement.id,
        },
      });
      if (result.error) {
        appendChat('assistant', result.error);
        clearProposal();
        setStatus('El asistente no pudo preparar un cambio válido.', 'error');
        return;
      }
      appendChat('assistant', result.reply || 'Propuesta lista.');
      showProposal(result);
      setStatus(`Propuesta lista (r${result.base_revision}). Revísala antes de aplicar.`, 'info');
    } catch (error) {
      appendChat('assistant', `Error: ${error.message}`);
      setStatus(error.message, 'error');
    } finally {
      setBusy(false);
    }
  }

  async function applyProposal() {
    if (!state.proposal || state.busy) return;
    const proposal = state.proposal;
    state.previousIr = JSON.parse(JSON.stringify(state.ir));
    setBusy(true);
    try {
      const result = await api(`/api/editor/scenes/${state.sceneId}/apply`, {
        method: 'POST',
        body: {
          patch: proposal.patch,
          base_revision: proposal.base_revision,
          quality: els['ed-quality'].value,
        },
      });
      renderForm(result.scene.ir, result.scene.revision);
      setCode(result.scene.code);
      els['ed-diff'].textContent = result.code_diff || '';
      clearProposal();
      els['ed-undo'].classList.remove('hidden');
      setStatus('Cambio aplicado y render en cola.', 'ok');
      if (result.job) pollJob(result.job.id);
    } catch (error) {
      setStatus(error.message, 'error');
      if (error.message.includes('409') || error.message.includes('cambió')) clearProposal();
    } finally {
      setBusy(false);
    }
  }

  async function undoLast() {
    if (!state.previousIr || state.busy) return;
    setBusy(true);
    try {
      const result = await api(`/api/editor/scenes/${state.sceneId}/apply`, {
        method: 'POST',
        body: {
          ir: state.previousIr,
          base_revision: state.revision,
          quality: els['ed-quality'].value,
        },
      });
      renderForm(result.scene.ir, result.scene.revision);
      setCode(result.scene.code);
      state.previousIr = null;
      els['ed-undo'].classList.add('hidden');
      setStatus('Último cambio deshecho.', 'ok');
      if (result.job) pollJob(result.job.id);
    } catch (error) {
      setStatus(error.message, 'error');
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------------
  // Código generado (CodeMirror)
  // ------------------------------------------------------------------
  function initCodeMirror() {
    if (!window.CodeMirror || state.codeMirror || !els['ed-code']) return;
    state.codeMirror = window.CodeMirror.fromTextArea(els['ed-code'], {
      mode: 'python',
      theme: 'manim',
      lineNumbers: true,
      lineWrapping: false,
      readOnly: true,
      indentUnit: 4,
      matchBrackets: true,
      viewportMargin: Infinity,
    });
  }

  function switchTab(name) {
    document.querySelectorAll('[data-ed-tab]').forEach((button) => {
      button.classList.toggle('active', button.dataset.edTab === name);
    });
    document.querySelectorAll('[data-ed-pane]').forEach((pane) => {
      pane.classList.toggle('active', pane.dataset.edPane === name);
    });
    if (name === 'code' && state.codeMirror) state.codeMirror.refresh();
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
        await saveScene(false);
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

    document.querySelectorAll('.ed-chip').forEach((chip) => {
      chip.addEventListener('click', () => {
        els['ed-chat-input'].value = chip.dataset.prompt;
        els['ed-chat-input'].focus();
      });
    });

    els['ed-apply'].addEventListener('click', () => applyProposal().catch((error) => setStatus(error.message, 'error')));
    els['ed-discard'].addEventListener('click', () => {
      clearProposal();
      setStatus('Propuesta descartada; la escena sigue igual.', 'info');
    });
    els['ed-undo'].addEventListener('click', () => undoLast().catch((error) => setStatus(error.message, 'error')));

    els['ed-copy-code'].addEventListener('click', async () => {
      const code = state.codeMirror ? state.codeMirror.getValue() : els['ed-code'].value;
      try {
        await navigator.clipboard.writeText(code);
        setStatus('Código copiado.', 'ok');
      } catch (error) {
        setStatus('No se pudo copiar el código.', 'error');
      }
    });

    document.querySelectorAll('[data-ed-tab]').forEach((button) => {
      button.addEventListener('click', () => switchTab(button.dataset.edTab));
    });

    els['ed-format'].addEventListener('change', () => {
      if (state.ir) state.ir.format = els['ed-format'].value;
      els['ed-video-frame'].dataset.format = els['ed-format'].value;
      scheduleAutoRender();
    });

    els['ed-fn-latex'].addEventListener('input', debouncedMath);
    els['ed-fn-latex'].addEventListener('change', scheduleAutoRender);

    [
      'ed-title', 'ed-fn-python', 'ed-a', 'ed-b', 'ed-tolerance', 'ed-iterations',
      'ed-domain-min', 'ed-domain-max', 'ed-hud', 'ed-accent', 'ed-result-color',
      'ed-grid', 'ed-audio-offset',
    ].forEach((id) => {
      const element = els[id];
      if (!element) return;
      element.addEventListener('change', scheduleAutoRender);
      element.addEventListener('input', scheduleAutoRender);
    });
  }

  function init() {
    cacheElements();
    if (!els['ed-save']) return;
    initCodeMirror();
    bind();
    window.EditorView = { activate };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
