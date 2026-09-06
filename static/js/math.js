/**
 * math.js — site-level math rendering (KaTeX).
 *
 * The theme (a pinned submodule) ships no math support, so this lives at site
 * level. It is the browser half of a pair: [markup.goldmark.extensions.passthrough]
 * in hugo.toml keeps `$...$` / `$$...$$` out of Goldmark's hands — without it,
 * `*` and `_` inside formulas were parsed as emphasis and `P^*` reached the page
 * as `P^<em>` — and this turns the surviving delimiters into rendered math.
 * The two delimiter sets must stay in sync; change one, change the other.
 *
 * Timing follows the Disqus slot (layouts/partials/slots/postView/bottom.html):
 * the theme dispatches a `slotify:slot` window CustomEvent on every slot
 * mount/ctx-update, and PostView is keyed by route, so that event is the
 * documented signal for "the SPA just swapped the article body". Listening for
 * it beats a MutationObserver — no feedback loop from our own DOM writes, and
 * no guessing at hydration timing.
 *
 * Economy mirrors the theme's Mermaid handling: nothing is fetched until a page
 * actually contains math. Unlike Disqus this may use a CDN — the theme vendors
 * its own assets, but a site is free not to — which is what makes KaTeX the
 * better pick over MathJax here: ~300 KB and an order of magnitude faster to
 * render, where self-hosting would have meant sixty font files instead of one.
 */
(function () {
  'use strict';

  // Bump version and integrity together; hashes are sha384 of the exact files
  // (openssl dgst -sha384 -binary <file> | openssl base64 -A).
  var KATEX = {
    version: '0.18.7',
    css: {
      url: 'https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/katex.min.css',
      integrity: 'sha384-JctiRyLzXCrSoOOzFlSoWLdyzQl7OrrRnhyeBmzB6ZWtcjccUyc8lCQJqIbs3uQX'
    },
    js: {
      url: 'https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/katex.min.js',
      integrity: 'sha384-+7Keh381hSkXmXqnjC0JBM/kzsN6TFj+wMKychSLjTvJ8/0ElMde2uKl8i6p6Buj'
    },
    autoRender: {
      url: 'https://cdn.jsdelivr.net/npm/katex@0.18.7/dist/contrib/auto-render.min.js',
      integrity: 'sha384-bjyGPfbij8/NDKJhSGZNP/khQVgtHUE5exjm4Ydllo42FwIgYsdLO2lXGmRBf5Mz'
    }
  };

  // The SPA's mount targets only. The crawler body (#seo-content) is deliberately
  // skipped: it is replaced once the SPA boots, so typesetting it would pull the
  // bundle on every page load to render something nobody sees.
  var SELECTORS = '#hugo-content, #about-content';

  // `$$` must precede `$`, else the opening `$$` matches as an empty inline span.
  var DELIMITERS = [
    { left: '$$', right: '$$', display: true },
    { left: '\\[', right: '\\]', display: true },
    { left: '$', right: '$', display: false },
    { left: '\\(', right: '\\)', display: false }
  ];

  var loading = null;
  var pending = null;

  function containers() {
    return Array.prototype.slice.call(document.querySelectorAll(SELECTORS));
  }

  // Cheap gate, and the idempotence guard: rendering consumes the delimiters
  // (they become .katex spans), so a repeat call finds nothing and does nothing.
  function hasMath(elements) {
    for (var i = 0; i < elements.length; i++) {
      var text = elements[i].textContent || '';
      if (text.indexOf('$') !== -1 || text.indexOf('\\(') !== -1 || text.indexOf('\\[') !== -1) {
        return true;
      }
    }
    return false;
  }

  function loadStyle(spec) {
    return new Promise(function (resolve, reject) {
      var link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = spec.url;
      link.integrity = spec.integrity;
      link.crossOrigin = 'anonymous';
      link.onload = resolve;
      link.onerror = function () { reject(new Error('failed to load ' + spec.url)); };
      document.head.appendChild(link);
    });
  }

  function loadScript(spec) {
    return new Promise(function (resolve, reject) {
      var script = document.createElement('script');
      script.src = spec.url;
      script.integrity = spec.integrity;
      script.crossOrigin = 'anonymous';
      script.onload = resolve;
      script.onerror = function () { reject(new Error('failed to load ' + spec.url)); };
      document.head.appendChild(script);
    });
  }

  // Await the stylesheet too, so formulas never flash as unstyled markup between
  // KaTeX writing its spans and the CSS arriving.
  function load() {
    if (!loading) {
      loading = Promise.all([
        loadStyle(KATEX.css),
        loadScript(KATEX.js).then(function () { return loadScript(KATEX.autoRender); })
      ]).catch(function (err) {
        loading = null; // let a later navigation retry a transient CDN failure
        throw err;
      });
    }
    return loading;
  }

  function render() {
    var elements = containers();
    if (!elements.length || !hasMath(elements)) return;

    load().then(function () {
      containers().forEach(function (el) {
        window.renderMathInElement(el, {
          delimiters: DELIMITERS,
          // Posts carry Python blocks; their `$` and `_` are not math.
          ignoredTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code', 'option'],
          // A malformed formula should render as flagged source, not abort the
          // whole page's math.
          throwOnError: false
        });
      });
    }).catch(function (err) {
      console.error('[math]', err);
    });
  }

  function schedule() {
    clearTimeout(pending);
    // Several slots mount per navigation; coalesce them into one pass, landing
    // after the v-html content patch has settled.
    pending = setTimeout(render, 50);
  }

  window.addEventListener('slotify:slot', function (event) {
    var phase = event.detail && event.detail.phase;
    if (phase === 'mount' || phase === 'ctx-update') schedule();
  });
})();
