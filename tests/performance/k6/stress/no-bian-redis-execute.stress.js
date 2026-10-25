// stress/no-bian-redis-execute.stress.js
// Prueba de carga sostenida para POST /business-api-b/v1/no-bian-redis/execute.
// Ejecutar desde tests/performance/k6:
// k6 run stress/no-bian-redis-execute.stress.js --env BASE_URL=http://127.0.0.1:8000

import http from "k6/http";
import { check } from "k6";

// Variables internas configurables a demanda.
// El endpoint se mantiene en 300 iteraciones por segundo durante la prueba.
const TARGET_RPS = 900;
// VUs preasignados. Aumentar este valor si la latencia impide sostener TARGET_RPS.
const VUS = 30;
// Duración por defecto; se puede sobrescribir con --env DURATION=60s.
const DURATION = __ENV.DURATION || "30s";
const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
const ENDPOINT = `${BASE_URL}/business-api-b/v1/no-bian-redis/execute`;

export const options = {
  scenarios: {
    no_bian_redis_execute: {
      executor: "constant-arrival-rate",
      rate: TARGET_RPS,
      timeUnit: "1s",
      duration: DURATION,
      preAllocatedVUs: VUS,
      // Mantenerlo igual a VUS para validar que 30 usuarios sostienen 300 RPS.
      // Si aparecen dropped_iterations, subir ambos valores según la latencia real.
      maxVUs: VUS,
    },
  },
  thresholds: {
    // La prueba debe alcanzar la tasa objetivo sin iteraciones descartadas.
    http_reqs: [`rate>=${TARGET_RPS}`],
    dropped_iterations: ["count==0"],
    http_req_failed: ["rate<0.01"],
    checks: ["rate>0.99"],
  },
};

const headers = {
  accept: "*/*",
  "device-identifier": "sdasdssfasdsaddfdsffd",
  "message-identifier": "dffsdfsfsdasdsfasdsaddfdsfsfasdsad",
  "channel-identifier": "sdfdfsdsdasdsfasdsad",
  "Content-Type": "application/json",
};

const payload = JSON.stringify({
  channelIdentification: "stridfdsfng",
  messageIdentification: "strindsfsdfg",
  deviceIdentifier: "striddfssfng",
  customerIdentificationNumber: "256123456",
  identificationForAccount: "123345667788",
});

export default function () {
  const response = http.post(ENDPOINT, payload, { headers });

  check(response, {
    "POST /no-bian-redis/execute returns 2xx": (res) => res.status >= 200 && res.status < 300,
  });
}
