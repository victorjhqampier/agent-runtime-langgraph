// rps/no-bian-redis.rps.js
// Tests RPS para NoBianExampleRedisController con caché
// Ejecución: k6 run rps/no-bian-redis.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s

import { group } from "k6";
import { rpsThresholds } from "../config/thresholds.js";
import { getConfig, logConfigInfo } from "../config/environments.js";
import { noBianExampleRedisCreate, validateResponse } from "../shared/request-builder.js";

const cfg = getConfig();

export const options = {
  thresholds: rpsThresholds(150), // Esperamos mejor rendimiento con caché
  stages: [
    { duration: "5s", target: 10 },
    { duration: "15s", target: 75 },
    { duration: "10s", target: 0 },
  ],
};

export function setup() {
  logConfigInfo();
  console.log("Starting NoBianExampleRedisController RPS test (with cache)");
}

export default function () {
  group("NoBianExampleRedisController - RPS Test", function () {
    const resp = noBianExampleRedisCreate();
    validateResponse(resp, "NoBianExampleRedisCreate", 200);
  });
}

export function teardown(data) {
  console.log("NoBianExampleRedisController RPS test completed");
}
