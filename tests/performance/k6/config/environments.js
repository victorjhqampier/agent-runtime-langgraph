// ---------------------------------------
// -- Baseline Requirements for K6 Tests --
// ------------ RAM: 1024mib -------------
// ------------ CPU: 700m ----------------
// ---------------------------------------

const defaultConfig = {
  baseUrl: "http://127.0.0.1:8000",
  // baseUrl: "http://127.0.0.1:8000", // EKS o API Gateway uri
  
  // Timeouts
  httpTimeout: "10s",
  scriptTimeout: "30s",
  
  // Ambientes disponibles
  testEnv: "local",
  
  // Headers requeridos para pruebas
  deviceIdentifier: "mobile-test-device",
  messageIdentifier: "msg-" + Date.now(),
  channelIdentifier:  "WEB",
  customerId: "12345",
};

const environments = {
  local: {
    baseUrl: defaultConfig.baseUrl,
    description: "Ambiente LOCAL - http://127.0.0.1:8000",
  }
};

export function getConfig() {
  const envName = (defaultConfig.testEnv || "local").toLowerCase();
  const selected = environments[envName] || environments.local;

  return {
    ...defaultConfig,
    ...selected,
  };
}

export function logConfigInfo() {
  const cfg = getConfig();
  console.log(`
    ==================== K6 Test Configuration ====================
    Base URL: ${cfg.baseUrl}
    Environment: ${cfg.testEnv}
    HTTP Timeout: ${cfg.httpTimeout}
    Device ID: ${cfg.deviceIdentifier}
    Channel: ${cfg.channelIdentifier}
    ================================================================
  `);
}

export { environments };
