// config/thresholds.js
// Umbrales de éxito para pruebas - Adaptados a servicios locales

export const commonThresholds = {
  // Tasa de errores: máximo 1% de fallos
  http_req_failed: ["rate<0.01"],
  
  // Latencia: p95 < 700ms, p99 < 1500ms (para ambiente local)
  http_req_duration: ["p(95)<700", "p(99)<1500"],
  
  // Checks: al menos 99% de éxito
  checks: ["rate>0.99"],
};

/**
 * Thresholds para pruebas RPS
 * @param {number} targetRps - Requests por segundo esperados
 */
export function rpsThresholds(targetRps = 100) {
  return {
    ...commonThresholds,
    http_reqs: [`rate>=${targetRps}`, "rate<5000"],
    http_req_duration: ["p(95)<500", "p(99)<1000"],
  };
}

/**
 * Thresholds para pruebas SMOKE - Validaciones rápidas
 */
export function smokeThresholds() {
  return {
    ...commonThresholds,
    http_req_duration: ["p(95)<1000", "p(99)<2000"],
    checks: ["rate>0.95"],
  };
}

/**
 * Thresholds para pruebas STRESS - Encontrar límites
 */
export function stressThresholds() {
  return {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<1500", "p(99)<3000"],
    checks: ["rate>0.90"],
  };
}

/**
 * Thresholds para pruebas SOAK - Resistencia a largo plazo
 */
export function soakThresholds() {
  return {
    http_req_failed: ["rate<0.02"],
    http_req_duration: ["p(95)<800", "p(99)<1800"],
    checks: ["rate>0.98"],
  };
}

export function buildThresholds(custom = {}) {
  return {
    ...commonThresholds,
    ...custom,
  };
}
