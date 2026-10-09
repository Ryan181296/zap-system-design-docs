// Sidebar Navigation & Route Controller
function initNavigation() {
  const navItems = document.querySelectorAll('.g-nav-item');
  const docSections = document.querySelectorAll('.g-doc-section');

  function getHashForTab(target, svcId) {
    if (!target) return '#system';
    const name = target.replace(/^view-/, '');
    return (target === 'view-api' && svcId && svcId !== 'all') ? ('#api-' + svcId) : ('#' + name);
  }

  function getTabFromHash(hashStr) {
    if (!hashStr) return null;
    let h = hashStr.replace(/^#/, '').trim().toLowerCase();
    if (!h) return null;
    if (document.getElementById(h)) return { target: h, svcId: null };
    if (document.getElementById('view-' + h)) return { target: 'view-' + h, svcId: null };
    if (h.startsWith('api-')) return { target: 'view-api', svcId: h.substring(4) };
    if (h === 'api') return { target: 'view-api', svcId: 'all' };
    return null;
  }

  window.switchTab = function switchTab(target, svcId = null, saveState = true) {
    if (!target) return;
    const targetSec = document.getElementById(target);
    if (!targetSec) return;

    document.querySelectorAll('.g-nav-item').forEach(n => {
      const match = (n.dataset.target === target) && (!svcId || n.dataset.svc === svcId || n.dataset.svc === 'all');
      n.classList.toggle('active', match);
    });

    document.querySelectorAll('.g-doc-section').forEach(sec => {
      sec.classList.remove('active-section');
      sec.style.display = 'none';
    });
    targetSec.classList.add('active-section');
    targetSec.style.display = 'block';

    if (saveState) {
      const newHash = getHashForTab(target, svcId);
      if (window.location.hash !== newHash) history.pushState({ target, svcId }, '', newHash);
    }
    window.scrollTo({ top: 0, behavior: 'instant' });
  };

  navItems.forEach(item => {
    item.addEventListener('click', (e) => {
      e.preventDefault();
      window.switchTab(item.dataset.target, item.dataset.svc || null, true);
    });
  });

  window.addEventListener('hashchange', () => {
    const tabInfo = getTabFromHash(window.location.hash);
    if (tabInfo) window.switchTab(tabInfo.target, tabInfo.svcId, false);
  });

  const initialTab = getTabFromHash(window.location.hash) || { target: window.__INITIAL_TARGET__ || 'view-system', svcId: null };
  window.switchTab(initialTab.target, initialTab.svcId, false);
}
