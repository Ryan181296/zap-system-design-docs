// OpenAPI and Postman Exporter
function downloadJsonFile(dataObj, filename) {
  const blob = new Blob([JSON.stringify(dataObj, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function exportOpenApiSpec() {
  const spec = {
    openapi: "3.0.0",
    info: { title: "ZAP Microservices API Spec", version: "1.0.0" },
    servers: [
      { url: "https://prod-***.zap.vn", description: "PROD Environment (zap-***-prod-****)" },
      { url: "https://uat-***.zap.vn", description: "UAT Environment (zap-***-sandbox-****)" }
    ],
    paths: {}
  };
  downloadJsonFile(spec, 'ZAP_OpenAPI_v3.0.json');
}
