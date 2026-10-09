// Main Bootstrap Entry Point
document.addEventListener('DOMContentLoaded', () => {
  initThemeManager();
  initNavigation();
  refreshHealthStatus();

  const prodBtn = document.getElementById('env-btn-prod');
  const uatBtn = document.getElementById('env-btn-uat');
  const refreshBtn = document.getElementById('btn-refresh-health');

  if (prodBtn) prodBtn.addEventListener('click', () => switchHealthEnv('PROD'));
  if (uatBtn) uatBtn.addEventListener('click', () => switchHealthEnv('UAT'));
  if (refreshBtn) refreshBtn.addEventListener('click', () => refreshHealthStatus());
});
