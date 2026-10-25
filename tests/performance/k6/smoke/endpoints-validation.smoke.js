// smoke/endpoints-validation.smoke.js
// Smoke test: Validación funcional rápida de todos los endpoints
// Ejecución: k6 run smoke/endpoints-validation.smoke.js --env BASE_URL=http://127.0.0.1:8000 --vus 5 --duration 20s

import { group, check } from "k6";
import { smokeThresholds } from "../config/thresholds.js";
import { getConfig, logConfigInfo } from "../config/environments.js";
import {
  bianExampleCreate,
  bianExampleCreateSecure,
  noBianExampleCreate,
  noBianExampleRedisCreate,
  validateResponse,
} from "../shared/request-builder.js";

const cfg = getConfig();

export const options = {
  thresholds: smokeThresholds(),
  stages: [
    { duration: "5s", target: 2 },
    { duration: "10s", target: 5 },
    { duration: "5s", target: 0 },
  ],
};

export function setup() {
  logConfigInfo();
  console.log("Starting Endpoints Validation - Smoke Test");
}

export default function () {
  group("Smoke: BianExampleController", function () {
    const resp1 = bianExampleCreate();
    check(resp1, {
      "BianCreate status 200": (r) => r.status === 200,
      "BianCreate response time < 2s": (r) => r.timings.duration < 2000,
    });

    const resp2 = bianExampleCreateSecure();
    check(resp2, {
      "BianCreateSecure response": (r) => r.status === 200 || r.status === 401,
      "BianCreateSecure response time < 2s": (r) => r.timings.duration < 2000,
    });
  });

  group("Smoke: NoBianExampleController", function () {
    const resp = noBianExampleCreate();
    check(resp, {
      "NoBianCreate status 200": (r) => r.status === 200,
      "NoBianCreate response time < 2s": (r) => r.timings.duration < 2000,
    });
  });

  group("Smoke: NoBianExampleRedisController", function () {
    const resp = noBianExampleRedisCreate();
    check(resp, {
      "RedisCreate status 200": (r) => r.status === 200,
      "RedisCreate response time < 2s": (r) => r.timings.duration < 2000,
    });
  });
}

export function teardown(data) {
  console.log("Endpoints Validation - Smoke Test completed");
}
