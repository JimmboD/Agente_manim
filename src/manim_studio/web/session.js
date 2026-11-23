/**
 * SESIÓN LOCAL — token CSRF para el servidor de Manim Studio.
 *
 * El servidor exige `X-Session-Token` en toda petición mutante y rechaza
 * orígenes que no sean localhost. Este script obtiene el token de forma
 * sincrónica (servidor local) y lo inyecta en peticiones del mismo origen,
 * de modo que app.js ya puede usar endpoints protegidos desde el primer load.
 *
 * Debe cargarse antes que app.js y studio.js.
 */
(function () {
  const nativeFetch = window.fetch.bind(window);
  let token = null;
  let bootstrapData = null;

  try {
    const xhr = new XMLHttpRequest();
    xhr.open('GET', '/api/editor/bootstrap', false);
    xhr.send(null);
    if (xhr.status === 200) {
      bootstrapData = JSON.parse(xhr.responseText);
      if (bootstrapData && bootstrapData.token) {
        token = bootstrapData.token;
        try {
          sessionStorage.setItem('manim_session_token', token);
        } catch (error) {
          /* almacenamiento no disponible */
        }
      }
    }
  } catch (error) {
    bootstrapData = null;
  }

  function sameOrigin(input) {
    try {
      const url = new URL(typeof input === 'string' ? input : input.url, window.location.href);
      return url.origin === window.location.origin;
    } catch (error) {
      return false;
    }
  }

  window.fetch = function patchedFetch(input, init) {
    const options = Object.assign({}, init || {});
    if (token && sameOrigin(input)) {
      const headers = new Headers(options.headers || (input && input.headers) || {});
      if (!headers.has('X-Session-Token')) {
        headers.set('X-Session-Token', token);
      }
      options.headers = headers;
    }
    return nativeFetch(input, options);
  };

  window.manimSession = {
    bootstrap: Promise.resolve(bootstrapData),
    get token() {
      return token;
    },
    get data() {
      return bootstrapData;
    },
  };
})();
