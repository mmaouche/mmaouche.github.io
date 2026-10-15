/* Apply the saved theme before the page paints, then connect the header toggle. */
(() => {
  'use strict';
  const root = document.documentElement;
  const system = window.matchMedia('(prefers-color-scheme: dark)');
  const storageKey = 'maouche-theme';
  let preference = null;
  let button;
  try {
    const saved = localStorage.getItem(storageKey);
    if (saved === 'light' || saved === 'dark') preference = saved;
  } catch (_) {
    // Theme switching still works when browser storage is unavailable.
  }

  function applyTheme() {
    const theme = preference || (system.matches ? 'dark' : 'light');
    root.dataset.theme = theme;
    if (button) {
      button.setAttribute('aria-pressed', String(theme === 'dark'));
      button.title = `Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`;
    }
  }

  applyTheme();
  system.addEventListener('change', applyTheme);
  window.addEventListener('storage', event => {
    if (event.key !== storageKey && event.key !== null) return;
    preference = ['light', 'dark'].includes(event.newValue) ? event.newValue : null;
    applyTheme();
  });
  document.addEventListener('DOMContentLoaded', () => {
    button = document.querySelector('#theme-toggle');
    button.hidden = false;
    applyTheme();
    button.addEventListener('click', () => {
      preference = root.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme();
      try {
        localStorage.setItem(storageKey, preference);
      } catch (_) {
        // Retain the choice for this page even if it cannot be saved.
      }
    });
  });
})();
