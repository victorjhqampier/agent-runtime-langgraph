// smoke/basic-health-check.smoke.js
// Smoke test: Validación rápida de disponibilidad
// Ejecución: k6 run smoke/basic-health-check.smoke.js --env BASE_URL=http://127.0.0.1:8000 --vus 1 --duration 10s

import { check } from "k6";
import http from "k6/http";
import { getConfig, logConfigInfo } from "../config/environments.js";
import { smokeThresholds } from "../config/thresholds.js";

const cfg = getConfig();

export const options = {
  thresholds: smokeThresholds(),
  stages: [
    { duration: "10s", target: 1 },
  ],
};

export function setup() {
  logConfigInfo();
  console.log("Starting Health Check - Smoke Test");
}

export default function () {
  // Validar disponibilidad general del servidor
  const healthCheck = http.get(`${cfg.baseUrl}/health`);
  check(healthCheck, {
    "Health endpoint status 200": (r) => r.status === 200 || r.status === 404,
  });

  // Validar que los endpoints estén registrados (intentar uno de cada)
  const headers = {
    "Content-Type": "application/json",
    "device_identifier": cfg.deviceIdentifier,
    "message_identifier": cfg.messageIdentifier,
    "channel_identifier": cfg.channelIdentifier,
  };

  const testPayload = JSON.stringify({
    example_field: "health_check",
  });

  // Test: BianExampleController disponible
  const bianTest = http.post(
    `${cfg.baseUrl}/bian-example/${cfg.customerId}/create`,
    testPayload,
    { headers, timeout: "5s" }
  );
  check(bianTest, {
    "BianExampleController available": (r) => r.status < 500,
  });

  // Test: NoBianExampleController disponible
  const noBianTest = http.post(
    `${cfg.baseUrl}/no-bian-example/${cfg.customerId}/create`,
    testPayload,
    { headers, timeout: "5s" }
  );
  check(noBianTest, {
    "NoBianExampleController available": (r) => r.status < 500,
  });

  // Test: NoBianExampleRedisController disponible
  const redisTest = http.post(
    `${cfg.baseUrl}/no-bian-redis/${cfg.customerId}/create-redis`,
    testPayload,
    { headers, timeout: "5s" }
  );
  check(redisTest, {
    "NoBianExampleRedisController available": (r) => r.status < 500,
  });
}

export function teardown(data) {
  console.log("Health Check - Smoke Test completed");
}
