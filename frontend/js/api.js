/**
 * API configuration for Smart Criminal Judgment Analysis System
 * Point to your backend (e.g. FastAPI) when running locally or in production.
 */
(function () {
  // Use backend URL from env or default to same-origin / common dev port
  var API_BASE = window.API_BASE_URL || 'http://127.0.0.1:8000';
  if (!API_BASE && window.location.port === '5173') {
    API_BASE = 'http://127.0.0.1:8000';  // Vite dev; backend often on 8000
  }
  if (!API_BASE && window.location.port === '3000') {
    API_BASE = 'http://127.0.0.1:8000';
  }

  window.API_BASE = API_BASE;
  window.API_ANALYZE = API_BASE + '/api/v1/analyze';
  window.API_ARGUMENTS = API_BASE + '/api/v1/arguments';
  window.API_TRANSCRIBE = API_BASE + '/transcribe';
  window.API_EXTRACT = API_BASE + '/extract';
  window.API_HEALTH = API_BASE + '/health';
})();
