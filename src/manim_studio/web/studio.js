/**
 * MANIM STUDIO — MODO ESTUDIO
 * Coordina el árbol de archivos, el editor, las plantillas, el chat de código
 * y la franja de guardado. El archivo .py abierto es la fuente de verdad:
 * nada se guarda sin Ctrl+S, «Aplicar» o una ejecución explícita.
 */
(function () {
  'use strict';

  const API = '/api/workspace';
  const FAVORITES_KEY = 'manim_favorite_templates';

  let currentPath = 'escenas/main.py';
  let currentSha = null;
  let dirty = false;
  let selectedPath = 'escenas/main.py';
  let tree = [];
  let nodeIndex = {};
  let templatesList = [];
  let pendingProposal = null;
  let savingPromise = null;
  let chatHistory = [];
  let favorites = loadFavorites();
  let dom = {};

  function $(id) {
    return document.getElementById(id);
  }

  function make(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
  }

  function basename(path) {
    return String(path || '').split('/').pop() || 'main.py';
  }

  function loadFavorites() {
    try {
      const raw = JSON.parse(localStorage.getItem(FAVORITES_KEY) || '[]');
      return new Set(Array.isArray(raw) ? raw.map(String) : []);
    } catch (error) {
      return new Set();
    }
  }

  function saveFavorites() {
    try {
      localStorage.setItem(FAVORITES_KEY, JSON.stringify(Array.from(favorites)));
    } catch (error) {
      /* almacenamiento no disponible */
    }
  }

  function log(level, text) {
    if (typeof appendTerminalLine === 'function') appendTerminalLine(level, text);
  }

  async function api(method, url, payload) {
    const options = { method, headers: {} };
    if (payload !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(payload);
    }
    let response;
    try {
      response = await fetch(url, options);
    } catch (error) {
      throw new Error(`No se pudo conectar con el servidor: ${error.message}`);
    }
    let data = {};
    try {
      data = await response.json();
    } catch (error) {
      data = {};
    }
    if (!response.ok) {
      const error = new Error(data.error || `HTTP ${response.status}`);
      error.status = response.status;
      error.data = data;
      throw error;
    }
    return data;
  }

  function setSaveStatus(stateName, text, sha) {
    if (!dom.saveStrip) return;
    dom.saveStrip.dataset.state = stateName;
    if (dom.saveText) dom.saveText.textContent = text;
    if (dom.saveFile) dom.saveFile.textContent = basename(currentPath);
    if (sha !== undefined) currentSha = sha;
  }

  function markDirty() {
    dirty = true;
    if (typeof state !== 'undefined') state.isDirty = true;
    if (dom.unsaved) dom.unsaved.classList.remove('hidden');
    setSaveStatus('unsaved', 'Cambios sin guardar');
  }

  function markSaved(sha) {
    dirty = false;
    if (typeof state !== 'undefined') state.isDirty = false;
    if (dom.unsaved) dom.unsaved.classList.add('hidden');
    setSaveStatus('saved', 'Cambios guardados', sha);
  }

  function markError(message) {
    setSaveStatus('error', message || 'Error al guardar');
  }

  function syncActiveFile(path) {
    if (typeof state !== 'undefined') {
      state.activeFile = basename(path);
      if (typeof updateActiveFileUI === 'function') updateActiveFileUI(state.activeFile);
    }
  }

  function confirmDiscard(path) {
    if (!dirty || currentPath === path) return true;
    return window.confirm('Tienes cambios sin guardar. ¿Descartarlos y abrir otro archivo?');
  }

  async function loadFile(path, options) {
    const opts = options || {};
    if (!confirmDiscard(path)) return false;
    try {
      const data = await api('GET', `${API}/files/read?path=${encodeURIComponent(path)}`);
      currentPath = data.path;
      currentSha = data.sha256;
      selectedPath = data.path;
      dirty = false;
      if (typeof setCodeValue === 'function') setCodeValue(data.code);
      syncActiveFile(data.path);
      markSaved(data.sha256);
      if (!opts.silent) {
        log('system', `${data.path} cargado (${data.size} bytes).`);
      }
      highlightSelected();
      return true;
    } catch (error) {
      log('error', `No se pudo abrir ${basename(path)}: ${error.message}`);
      markError('No se pudo abrir el archivo');
      return false;
    }
  }

  function loadTemplateCode(code, path) {
    if (!confirmDiscard(path)) return false;
    currentPath = path;
    currentSha = null;
    selectedPath = path;
    if (typeof setCodeValue === 'function') setCodeValue(code);
    syncActiveFile(path);
    markDirty();
    log('system', `Plantilla cargada en ${path}. Guárdala con Ctrl+S si quieres conservarla.`);
    highlightSelected();
    return true;
  }

  function saveActiveFile() {
    if (savingPromise) return savingPromise;
    savingPromise = performSave().finally(() => {
      savingPromise = null;
    });
    return savingPromise;
  }

  async function performSave() {
    const code = typeof getCode === 'function' ? getCode() : '';
    try {
      const data = await api('POST', `${API}/files/write`, {
        path: currentPath,
        code,
        sha256: currentSha || undefined,
      });
      currentSha = data.sha256;
      markSaved(data.sha256);
      log('success', `${basename(currentPath)} guardado en disco (${data.size} bytes).`);
      refreshTree();
      return data;
    } catch (error) {
      if (error.status === 409) {
        log('error', `${basename(currentPath)} cambió en disco. Se recargó la versión guardada.`);
        await loadFile(currentPath, { force: true });
        throw error;
      }
      markError('Error al guardar');
      log('error', `No se pudo guardar ${basename(currentPath)}: ${error.message}`);
      throw error;
    }
  }

  // ------------------------------------------------------------------------
  // ÁRBOL DE ARCHIVOS
  // ------------------------------------------------------------------------
  function renderNode(node, depth) {
    const wrapper = make('div', 'tree-node-wrapper');
    const row = make('button', `tree-node tree-${node.type}`);
    row.type = 'button';
    row.dataset.path = node.path;
    row.dataset.type = node.type;
    row.dataset.writable = node.writable ? '1' : '0';
    row.style.paddingLeft = `${8 + depth * 14}px`;
    row.title = node.writable ? node.path : `${node.path} (solo lectura)`;

    const arrow = make('span', 'tree-arrow', node.type === 'folder' ? '▸' : '·');
    const icon = make('span', 'tree-icon', node.type === 'folder' ? '▣' : node.path.endsWith('.py') ? '⟨/⟩' : '•');
    const label = make('span', 'tree-label', node.name);
    row.append(arrow, icon, label);
    if (!node.writable) row.appendChild(make('span', 'tree-lock', '🔒'));
    wrapper.appendChild(row);

    nodeIndex[node.path] = node;
    if (node.type === 'folder') {
      const children = make('div', 'tree-children hidden');
      (node.children || []).forEach((child) => children.appendChild(renderNode(child, depth + 1)));
      wrapper.appendChild(children);
      row.addEventListener('click', (event) => {
        event.stopPropagation();
        selectedPath = node.path;
        highlightSelected();
        const hidden = children.classList.toggle('hidden');
        arrow.textContent = hidden ? '▸' : '▾';
      });
    } else {
      row.addEventListener('click', (event) => {
        event.stopPropagation();
        selectedPath = node.path;
        highlightSelected();
        openNode(node);
      });
    }
    return wrapper;
  }

  function openNode(node) {
    const lower = node.path.toLowerCase();
    if (lower.endsWith('.mp4') || lower.endsWith('.webm')) {
      if (typeof loadVideoPlayer === 'function') loadVideoPlayer(`/media/${basename(node.path)}`);
      log('system', `Reproduciendo ${basename(node.path)}.`);
      return;
    }
    if (lower.endsWith('.mp3') || lower.endsWith('.wav') || lower.endsWith('.m4a') || lower.endsWith('.ogg') || lower.endsWith('.flac') || lower.endsWith('.aac')) {
      log('system', `${basename(node.path)} está en la carpeta de audios. Úsalo desde el panel de audio.`);
      return;
    }
    loadFile(node.path);
  }

  function renderTree(data) {
    if (!dom.treeList) return;
    tree = data.roots || [];
    nodeIndex = {};
    dom.treeList.replaceChildren();
    tree.forEach((root) => {
      const section = make('section', 'tree-root');
      const head = make('div', 'tree-root-head');
      head.appendChild(make('span', 'tree-root-title', root.name));
      if (!root.writable) head.appendChild(make('span', 'tree-lock', 'solo lectura'));
      const children = make('div', 'tree-children');
      if (!root.children.length) children.appendChild(make('p', 'tree-empty', 'Sin archivos'));
      root.children.forEach((child) => children.appendChild(renderNode(child, 0)));
      section.append(head, children);
      dom.treeList.appendChild(section);
    });
    highlightSelected();
  }

  function highlightSelected() {
    if (!dom.treeList) return;
    dom.treeList.querySelectorAll('.tree-node').forEach((node) => {
      node.classList.toggle('selected', node.dataset.path === selectedPath);
    });
  }

  async function refreshTree() {
    try {
      const data = await api('GET', `${API}/files/tree`);
      renderTree(data);
      return data;
    } catch (error) {
      log('error', `No se pudo actualizar el árbol de archivos: ${error.message}`);
      return null;
    }
  }

  function basePathForSelection() {
    const node = nodeIndex[selectedPath];
    if (node && node.type === 'folder') return selectedPath;
    if (node && node.type === 'file') return selectedPath.split('/').slice(0, -1).join('/') || 'escenas';
    return 'escenas';
  }

  async function createNode(kind) {
    const base = basePathForSelection();
    const raw = window.prompt(kind === 'folder' ? 'Nombre de la carpeta:' : 'Nombre del archivo:', '');
    if (!raw) return;
    let name = raw.trim().replace(/[\\/]/g, '_');
    if (kind === 'file' && !/\.[A-Za-z0-9]+$/.test(name)) name += '.py';
    const path = `${base}/${name}`;
    try {
      const node = await api('POST', `${API}/files/create`, { path, kind });
      selectedPath = node.path;
      await refreshTree();
      log('success', `Creado ${node.path}.`);
      if (kind === 'file') loadFile(node.path);
    } catch (error) {
      log('error', `No se pudo crear: ${error.message}`);
    }
  }

  async function moveSelected() {
    if (!selectedPath) return;
    const target = window.prompt('Mover o renombrar a esta ruta:', selectedPath);
    if (!target || target === selectedPath) return;
    try {
      const node = await api('POST', `${API}/files/move`, { from: selectedPath, to: target });
      if (currentPath === selectedPath) currentPath = node.path;
      selectedPath = node.path;
      await refreshTree();
      log('success', `Movido a ${node.path}.`);
    } catch (error) {
      log('error', `No se pudo mover: ${error.message}`);
    }
  }

  async function deleteSelected() {
    if (!selectedPath) return;
    const node = nodeIndex[selectedPath];
    if (node && !node.writable) {
      log('error', 'Esa carpeta es de solo lectura.');
      return;
    }
    if (!window.confirm(`¿Eliminar ${selectedPath}? Esta acción no se puede deshacer.`)) return;
    try {
      const data = await api('POST', `${API}/files/delete`, { path: selectedPath });
      log('warning', `Eliminado ${data.deleted}.`);
      if (currentPath === data.deleted) {
        currentPath = 'escenas/main.py';
        currentSha = null;
        selectedPath = currentPath;
        await loadFile(currentPath, { force: true });
      }
      await refreshTree();
    } catch (error) {
      log('error', `No se pudo eliminar: ${error.message}`);
    }
  }

  function uploadAudio(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const raw = String(reader.result || '');
      const data = raw.includes(',') ? raw.split(',')[1] : '';
      try {
        const node = await api('POST', `${API}/files/upload`, { name: file.name, data });
        await refreshTree();
        log('success', `Audio subido a ${node.path}.`);
      } catch (error) {
        log('error', `No se pudo subir el audio: ${error.message}`);
      }
    };
    reader.onerror = () => log('error', 'No se pudo leer el archivo de audio.');
    reader.readAsDataURL(file);
  }

  // ------------------------------------------------------------------------
  // PLANTILLAS
  // ------------------------------------------------------------------------
  async function refreshTemplates() {
    try {
      const data = await api('GET', `${API}/templates`);
      templatesList = data.templates || [];
      renderTemplates();
      return templatesList;
    } catch (error) {
      log('error', `No se pudieron cargar las plantillas: ${error.message}`);
      return [];
    }
  }

  function templateRow(template) {
    const row = make('div', 'tpl-item');
    row.dataset.id = template.id;
    const star = make('button', `tpl-star${favorites.has(template.id) ? ' active' : ''}`, favorites.has(template.id) ? '★' : '☆');
    star.type = 'button';
    star.title = favorites.has(template.id) ? 'Quitar de favoritas' : 'Marcar como favorita';
    star.addEventListener('click', (event) => {
      event.stopPropagation();
      if (favorites.has(template.id)) favorites.delete(template.id);
      else favorites.add(template.id);
      saveFavorites();
      renderTemplates();
    });
    const name = make('span', 'tpl-name', template.name);
    const meta = make('span', 'tpl-meta', template.category);
    const body = make('span', 'tpl-body');
    body.append(name, meta);
    row.append(star, body);
    row.addEventListener('click', () => loadTemplate(template));
    return row;
  }

  function renderTemplates() {
    if (!dom.tplList) return;
    const query = (dom.tplSearch ? dom.tplSearch.value : '').trim().toLowerCase();
    const sorted = templatesList.slice().sort((a, b) => {
      const favoriteDiff = Number(favorites.has(b.id)) - Number(favorites.has(a.id));
      if (favoriteDiff) return favoriteDiff;
      return String(a.name).localeCompare(String(b.name), 'es');
    });
    const filtered = sorted.filter((item) => `${item.name} ${item.category}`.toLowerCase().includes(query));
    dom.tplList.replaceChildren();
    if (!filtered.length) {
      dom.tplList.appendChild(make('p', 'rail-hint', query ? 'No hay plantillas que coincidan.' : 'No hay plantillas disponibles.'));
      return;
    }
    const suggested = filtered.filter((item) => favorites.has(item.id));
    if (suggested.length) {
      const section = make('div', 'tpl-section');
      section.appendChild(make('p', 'tpl-section-title', 'Sugeridas para ti'));
      suggested.slice(0, 5).forEach((item) => section.appendChild(templateRow(item)));
      dom.tplList.appendChild(section);
    }
    const rest = suggested.length ? filtered.filter((item) => !favorites.has(item.id)) : filtered;
    if (rest.length) {
      const section = make('div', 'tpl-section');
      section.appendChild(make('p', 'tpl-section-title', suggested.length ? 'Todas las plantillas' : 'Plantillas disponibles'));
      rest.forEach((item) => section.appendChild(templateRow(item)));
      dom.tplList.appendChild(section);
    }
  }

  async function loadTemplate(template) {
    try {
      const response = await fetch(template.source);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const code = data.code;
      if (typeof code !== 'string' || !code.trim()) throw new Error('La plantilla está vacía.');
      const target = template.origin === 'user' ? template.path : 'escenas/main.py';
      loadTemplateCode(code, target);
      log('system', `Plantilla «${template.name}» lista para revisar en ${target}.`);
    } catch (error) {
      log('error', `No se pudo cargar «${template.name}»: ${error.message}`);
    }
  }

  async function createTemplateFromEditor(name) {
    const code = typeof getCode === 'function' ? getCode() : '';
    try {
      const data = await api('POST', `${API}/templates`, { name, code });
      favorites.add(data.template.id);
      saveFavorites();
      await refreshTemplates();
      log('success', `Plantilla «${data.template.name}» creada en ${data.template.path}.`);
    } catch (error) {
      log('error', `No se pudo crear la plantilla: ${error.message}`);
    }
  }

  // ------------------------------------------------------------------------
  // CHAT DE PROPUESTAS DE CÓDIGO
  // ------------------------------------------------------------------------
  function appendChat(role, text, extraClass) {
    if (!dom.chatLog) return;
    const message = make('div', `chat-msg chat-${role}${extraClass ? ` ${extraClass}` : ''}`);
    message.appendChild(make('span', 'chat-role', role === 'user' ? 'Tú' : 'Asistente'));
    message.appendChild(make('span', 'chat-text', text));
    dom.chatLog.appendChild(message);
    dom.chatLog.scrollTop = dom.chatLog.scrollHeight;
  }

  function showProposal(data) {
    pendingProposal = {
      path: data.path || currentPath,
      code: data.code,
      sha256: currentSha,
      baseCode: typeof getCode === 'function' ? getCode() : '',
    };
    if (!dom.chatProposal) return;
    dom.chatProposal.classList.remove('hidden');
    dom.chatProposalTitle.textContent = 'Propuesta lista para revisar';
    dom.chatProposalSummary.textContent = (data.summary || []).join(' · ');
    dom.chatProposalDiff.textContent = data.code_diff || 'Sin cambios en el código.';
    if (dom.chatProvider) dom.chatProvider.textContent = data.provider || 'local';
    dom.chatApply.disabled = false;
  }

  function clearProposal() {
    pendingProposal = null;
    if (!dom.chatProposal) return;
    dom.chatProposal.classList.add('hidden');
    dom.chatProposalDiff.textContent = '';
    dom.chatProposalSummary.textContent = '';
  }

  async function sendChat(event) {
    if (event) event.preventDefault();
    const message = (dom.chatInput ? dom.chatInput.value : '').trim();
    if (!message) return;
    if (dom.chatSubmit) dom.chatSubmit.disabled = true;
    appendChat('user', message);
    chatHistory.push({ role: 'user', content: message });
    if (dom.chatInput) dom.chatInput.value = '';

    try {
      const data = await api('POST', `${API}/code/propose`, {
        message,
        path: currentPath,
        code: typeof getCode === 'function' ? getCode() : '',
        history: chatHistory.slice(-6),
      });
      appendChat('assistant', data.reply, data.fallback ? 'chat-fallback' : '');
      if (data.fallback) appendChat('assistant', data.fallback, 'chat-fallback');
      chatHistory.push({ role: 'assistant', content: data.reply });
      if (data.code && data.code_diff) showProposal(data);
      else clearProposal();
    } catch (error) {
      appendChat('assistant', error.message, 'chat-error');
    } finally {
      if (dom.chatSubmit) dom.chatSubmit.disabled = false;
    }
  }

  async function applyProposal() {
    if (!pendingProposal) return;
    if (typeof getCode === 'function' && getCode() !== pendingProposal.baseCode) {
      if (!window.confirm('El código cambió desde la propuesta. ¿Sobrescribirlo con la propuesta?')) return;
    }
    if (dom.chatApply) dom.chatApply.disabled = true;
    try {
      const data = await api('POST', `${API}/code/apply`, {
        path: pendingProposal.path,
        code: pendingProposal.code,
        sha256: pendingProposal.sha256,
      });
      currentPath = data.path;
      currentSha = data.sha256;
      selectedPath = data.path;
      if (typeof setCodeValue === 'function') setCodeValue(pendingProposal.code);
      syncActiveFile(data.path);
      markSaved(data.sha256);
      appendChat('assistant', `Propuesta aplicada y guardada en ${data.path}.`, 'chat-applied');
      clearProposal();
      refreshTree();
    } catch (error) {
      appendChat('assistant', `No se pudo aplicar: ${error.message}`, 'chat-error');
      if (error.status === 409) await loadFile(pendingProposal.path, { force: true });
    } finally {
      if (dom.chatApply) dom.chatApply.disabled = false;
    }
  }

  // ------------------------------------------------------------------------
  // INICIALIZACIÓN
  // ------------------------------------------------------------------------
  function bind() {
    if (dom.refreshTree) dom.refreshTree.addEventListener('click', () => refreshTree());
    if (dom.newFile) dom.newFile.addEventListener('click', () => createNode('file'));
    if (dom.newFolder) dom.newFolder.addEventListener('click', () => createNode('folder'));
    if (dom.moveFile) dom.moveFile.addEventListener('click', moveSelected);
    if (dom.deleteFile) dom.deleteFile.addEventListener('click', deleteSelected);
    if (dom.uploadFile && dom.uploadInput) {
      dom.uploadFile.addEventListener('click', () => dom.uploadInput.click());
      dom.uploadInput.addEventListener('change', (event) => {
        uploadAudio(event.target.files[0]);
        event.target.value = '';
      });
    }
    if (dom.saveNow) dom.saveNow.addEventListener('click', () => {
      saveActiveFile().catch(() => {});
    });
    if (dom.tplSearch) dom.tplSearch.addEventListener('input', renderTemplates);
    if (dom.tplCreateForm) {
      dom.tplCreateForm.addEventListener('submit', (event) => {
        event.preventDefault();
        const name = (dom.tplCreateName ? dom.tplCreateName.value : '').trim();
        if (!name) return;
        createTemplateFromEditor(name);
        dom.tplCreateName.value = '';
      });
    }
    if (dom.chatForm) dom.chatForm.addEventListener('submit', sendChat);
    if (dom.chatInput) {
      dom.chatInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
          event.preventDefault();
          sendChat();
        }
      });
    }
    document.querySelectorAll('[data-chat-prompt]').forEach((chip) => {
      chip.addEventListener('click', () => {
        if (!dom.chatInput) return;
        dom.chatInput.value = chip.dataset.chatPrompt || '';
        dom.chatInput.focus();
      });
    });
    if (dom.chatApply) dom.chatApply.addEventListener('click', applyProposal);
    if (dom.chatDiscard) dom.chatDiscard.addEventListener('click', clearProposal);
  }

  function init() {
    dom = {
      treeList: $('file-tree-list'),
      refreshTree: $('btn-refresh-tree'),
      newFile: $('btn-new-file'),
      newFolder: $('btn-new-folder'),
      moveFile: $('btn-move-file'),
      deleteFile: $('btn-delete-file'),
      uploadFile: $('btn-upload-file'),
      uploadInput: $('file-upload-input'),
      unsaved: $('unsaved-badge'),
      saveStrip: $('save-status-strip'),
      saveText: $('save-status-text'),
      saveFile: $('save-status-file'),
      saveNow: $('btn-save-now'),
      tplList: $('tpl-list'),
      tplSearch: $('tpl-search'),
      tplCreateForm: $('tpl-create-form'),
      tplCreateName: $('tpl-create-name'),
      chatLog: $('chat-log'),
      chatInput: $('chat-input'),
      chatForm: $('chat-form'),
      chatSubmit: $('chat-form') ? $('chat-form').querySelector('button[type="submit"]') : null,
      chatProposal: $('chat-proposal'),
      chatProposalTitle: $('chat-proposal-title'),
      chatProposalSummary: $('chat-proposal-summary'),
      chatProposalDiff: $('chat-proposal-diff'),
      chatApply: $('chat-apply'),
      chatDiscard: $('chat-discard'),
      chatProvider: $('chat-provider-badge'),
    };
    if (!dom.treeList) return;
    bind();
    markSaved();
    refreshTree();
    refreshTemplates();
    loadFile(currentPath, { silent: true }).catch(() => {});
  }

  window.Studio = {
    currentPath: () => currentPath,
    currentSha: () => currentSha,
    isDirty: () => dirty,
    loadFile,
    loadTemplateCode,
    saveActiveFile,
    markDirty,
    markSaved,
    refreshTree,
    refreshTemplates,
  };

  // Los scripts se cargan al final del body: el DOM ya existe.
  init();
})();
