// stress/concurrent-load.stress.js
// Stress test: Encuentra los límites del sistema con carga gradual
// Ejecución: k6 run stress/concurrent-load.stress.js --env BASE_URL=http://127.0.0.1:8000 --vus 200 --duration 60s

import { group } from "k6";
import { stressThresholds } from "../config/thresholds.js";
import { getConfig, logConfigInfo } from "../config/environments.js";
import {
  bianExampleCreate,
  noBianExampleCreate,
  noBianExampleRedisCreate,
  validateResponse,
} from "../shared/request-builder.js";

const cfg = getConfig();

export const options = {
  thresholds: stressThresholds(),
  stages: [
    // Ramp-up gradual
    { duration: "10s", target: 50 },
    { duration: "10s", target: 100 },
    { duration: "10s", target: 150 },
    { duration: "15s", target: 200 }, // Carga máxima
    
    // Mantener carga máxima
    { duration: "10s", target: 200 },
    
    // Ramp-down
    { duration: "5s", target: 0 },
  ],
};

export function setup() {
  logConfigInfo();
  console.log("Starting Stress Test - Finding system limits");
}

export default function () {
  group("Stress: Mixed Endpoints Load", function () {
    // Distribuir carga entre los 3 endpoints
    const random = Math.random();
    
    if (random < 0.33) {
      const resp1 = bianExampleCreate();
      validateResponse(resp1, "BianExampleCreate", 200);
    } else if (random < 0.66) {
      const resp2 = noBianExampleCreate();
      validateResponse(resp2, "NoBianExampleCreate", 200);
    } else {
      const resp3 = noBianExampleRedisCreate();
      validateResponse(resp3, "NoBianExampleRedisCreate", 200);
    }
  });
}

export function teardown(data) {
  console.log("Stress Test completed - Check metrics to identify breaking points");
}
