// Dark/Light Theme and Lock Controller
function initThemeManager() {
  const themeBtn = document.getElementById('theme-toggle');
  const iconContainer = document.getElementById('theme-icon-container');
  const sunSVG = `<svg class="svg-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/></svg>`;
  const moonSVG = `<svg class="svg-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>`;

  const savedTheme = localStorage.getItem('zap_doc_theme') || 'light';
  if (savedTheme === 'dark') {
    document.body.classList.add('dark-mode');
    if (iconContainer) iconContainer.innerHTML = sunSVG;
  } else {
    if (iconContainer) iconContainer.innerHTML = moonSVG;
  }

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
      const isDark = document.body.classList.contains('dark-mode');
      if (iconContainer) iconContainer.innerHTML = isDark ? sunSVG : moonSVG;
      localStorage.setItem('zap_doc_theme', isDark ? 'dark' : 'light');
    });
  }
}

function lockDocs() {
  try {
    sessionStorage.removeItem('zap_docs_session_key');
  } catch (e) {}
  window.location.reload();
}
