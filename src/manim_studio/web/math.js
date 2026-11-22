/**
 * Utilidades matemáticas compartidas: KaTeX vivo, texto con fórmulas y
 * conversión de expresiones Python a LaTeX.
 */
(function () {
  'use strict';

  function debounce(fn, ms) {
    const delay = Math.max(0, Number(ms) || 0);
    let timer = null;
    function wrapped(...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    }
    wrapped.cancel = () => clearTimeout(timer);
    return wrapped;
  }

  function stripDelimiters(tex) {
    let text = String(tex == null ? '' : tex).trim();
    if (text.startsWith('$$') && text.endsWith('$$')) {
      return text.slice(2, -2).trim();
    }
    if (text.startsWith('$') && text.endsWith('$')) {
      return text.slice(1, -1).trim();
    }
    return text;
  }

  function renderKatex(element, tex, options) {
    if (!element) return;
    const config = Object.assign({ throwOnError: false, errorColor: '#E8A0A0' }, options || {});
    const expression = stripDelimiters(tex);
    element.classList.remove('has-error');
    if (!expression) {
      element.textContent = 'Escribe una fórmula para verla aquí.';
      return;
    }
    if (!window.katex) {
      element.textContent = expression;
      return;
    }
    try {
      window.katex.render(expression, element, config);
    } catch (error) {
      element.classList.add('has-error');
      element.textContent = error && error.message ? error.message : 'LaTeX no válido';
    }
  }

  function escapeHtml(text) {
    return String(text == null ? '' : text)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  /** Renderiza $$...$$ y $...$ dentro de un texto, escapando el resto. */
  function renderMathInText(element, text) {
    if (!element) return;
    const source = String(text == null ? '' : text);
    const pattern = /\$\$([\s\S]+?)\$\$|\$([^$\n]+?)\$/g;
    let html = '';
    let lastIndex = 0;
    let match;

    while ((match = pattern.exec(source)) !== null) {
      html += escapeHtml(source.slice(lastIndex, match.index));
      const display = match[1] !== undefined;
      const expression = display ? match[1] : match[2];
      if (window.katex) {
        try {
          html += window.katex.renderToString(expression, {
            displayMode: display,
            throwOnError: false,
            errorColor: '#E8A0A0',
          });
        } catch (error) {
          html += escapeHtml(expression);
        }
      } else {
        html += escapeHtml(expression);
      }
      lastIndex = match.index + match[0].length;
    }
    html += escapeHtml(source.slice(lastIndex));
    element.innerHTML = html;
  }

  /** Conversión práctica de Python matemático a LaTeX para Short y Scratch. */
  function pythonToTex(expression) {
    let tex = String(expression == null ? '' : expression).trim();
    tex = tex.replace(/\*\*/g, '^');
    tex = tex.replace(/\bmath\./g, '');
    tex = tex.replace(/\bexp\s*\(\s*([^()]+)\s*\)/g, 'e^{$1}');
    tex = tex.replace(/\bsqrt\s*\(\s*([^()]+)\s*\)/g, '\\sqrt{$1}');
    tex = tex.replace(/\babs\s*\(\s*([^()]+)\s*\)/g, '|{$1}|');
    tex = tex.replace(/\bsin\s*\(/g, '\\sin(');
    tex = tex.replace(/\bcos\s*\(/g, '\\cos(');
    tex = tex.replace(/\btan\s*\(/g, '\\tan(');
    tex = tex.replace(/\bln\s*\(/g, '\\ln(');
    tex = tex.replace(/\blog\s*\(/g, '\\log(');
    tex = tex.replace(/\bpi\b/g, '\\pi');
    tex = tex.replace(/\*/g, '\\cdot ');
    tex = tex.replace(/(?<=\d)(?=[a-zA-Z\\(])/g, ' ');
    return tex;
  }

  window.ManimMath = {
    renderKatex,
    renderMathInText,
    pythonToTex,
    stripDelimiters,
    escapeHtml,
    debounce,
  };
})();
