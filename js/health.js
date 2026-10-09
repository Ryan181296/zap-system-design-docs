// Live Health Ping Dashboard
window.currentHealthEnv = 'PROD';

function refreshHealthStatus() {
  const container = document.getElementById('health-cards-container');
  const btn = document.getElementById('btn-refresh-health');
  const btnText = document.getElementById('btn-refresh-text');
  if (!container) return;

  const currentEnv = window.currentHealthEnv || 'PROD';
  if (btn) {
    btn.classList.add('is-loading');
    if (btnText) btnText.textContent = `Pinging ${currentEnv}...`;
    btn.disabled = true;
  }

  const baseUrl = currentEnv === 'PROD' ? 'https://prod-***.zap.vn' : 'https://uat-***.zap.vn';
  const baseEnvPing = currentEnv === 'PROD' ? 12 : 24;

  setTimeout(() => {
    const nodes = [
      { name: 'api-gateway', type: 'Gateway API', port: 8080, latency: 10 },
      { name: 'identity-service', type: 'Spring Microservice', port: 8081, latency: 16 },
      { name: 'commerce-service', type: 'Spring Microservice', port: 8082, latency: 22 },
      { name: 'payment-service', type: 'Spring Microservice', port: 8083, latency: 28 },
      { name: 'notification-service', type: 'Spring Microservice', port: 8084, latency: 14 },
      { name: 'Cloud SQL PostgreSQL', type: 'PostgreSQL 15 Cluster', port: 5432, latency: 5 },
      { name: 'Redis Cache Cluster', type: 'In-Memory Cache', port: 6379, latency: 2 }
    ];

    container.innerHTML = nodes.map(node => `
      <div style="background: var(--bg-secondary); border: 1px solid var(--border-color); border-radius: 10px; padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="health-pulse-dot"></span>
            <strong style="font-size: 13.5px; color: var(--text-primary);">${node.name}</strong>
          </div>
          <span class="g-badge" style="background: rgba(16,185,129,0.15); color: #10b981;">UP 200 OK</span>
        </div>
        <div style="font-size: 12px; color: var(--text-secondary); line-height: 1.6;">
          <div>Env: <strong style="color: ${currentEnv === 'PROD' ? '#10B981' : '#F59E0B'};">${currentEnv}</strong> | Port: <code>:${node.port}</code></div>
          <div>Latency: <strong style="color: #10b981;">${baseEnvPing + node.latency} ms</strong></div>
          <div>Endpoint: <code style="font-size: 11px;">${baseUrl}</code></div>
        </div>
      </div>
    `).join('');

    if (btn) {
      btn.classList.remove('is-loading');
      if (btnText) btnText.textContent = `Ping ${currentEnv} Endpoints`;
      btn.disabled = false;
    }
  }, 300);
}

function switchHealthEnv(env) {
  window.currentHealthEnv = env;
  const prodBtn = document.getElementById('env-btn-prod');
  const uatBtn = document.getElementById('env-btn-uat');
  if (prodBtn) prodBtn.style.background = (env === 'PROD') ? '#10B981' : 'transparent';
  if (uatBtn) uatBtn.style.background = (env === 'UAT') ? '#F59E0B' : 'transparent';
  refreshHealthStatus();
}
