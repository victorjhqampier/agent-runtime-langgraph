// soak/long-running.soak.js
// Soak test: Valida estabilidad y resistencia a largo plazo
// Ejecución: k6 run soak/long-running.soak.js --env BASE_URL=http://127.0.0.1:8000 --vus 30 --duration 300s

import { group, sleep } from "k6";
import { soakThresholds } from "../config/thresholds.js";
import { getConfig, logConfigInfo } from "../config/environments.js";
import {
  bianExampleCreate,
  noBianExampleCreate,
  noBianExampleRedisCreate,
  validateResponse,
} from "../shared/request-builder.js";

const cfg = getConfig();

export const options = {
  thresholds: soakThresholds(),
  stages: [
    // Ramp-up lento
    { duration: "30s", target: 15 },
    { duration: "30s", target: 30 },
    
    // Mantener carga constante por 3+ minutos
    { duration: "180s", target: 30 },
    
    // Ramp-down lento
    { duration: "30s", target: 0 },
  ],
};

export function setup() {
  logConfigInfo();
  console.log("Starting Soak Test - Long-running stability check");
  console.log("Duration: 300s (5 minutes) at 30 VUs");
}

export default function () {
  group("Soak: Steady Load Test", function () {
    // Rotar entre endpoints uniformemente
    const iteration = __VU * __ITER; // Identificador único por VU e iteración
    const endpoint = iteration % 3;
    
    if (endpoint === 0) {
      const resp1 = bianExampleCreate();
      validateResponse(resp1, "BianExampleCreate", 200);
    } else if (endpoint === 1) {
      const resp2 = noBianExampleCreate();
      validateResponse(resp2, "NoBianExampleCreate", 200);
    } else {
      const resp3 = noBianExampleRedisCreate();
      validateResponse(resp3, "NoBianExampleRedisCreate", 200);
    }
    
    // Pequeña pausa entre requests
    sleep(0.5);
  });
}

export function teardown(data) {
  console.log("Soak Test completed - Check for memory leaks, connection pool issues, etc.");
}
