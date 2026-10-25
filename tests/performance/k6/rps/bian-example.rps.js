// rps/bian-example.rps.js
// Tests RPS para BianExampleController endpoints
// Ejecución: k6 run rps/bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s

import { group } from "k6";
import { rpsThresholds } from "../config/thresholds.js";
import { getConfig, logConfigInfo } from "../config/environments.js";
import {
  bianExampleCreate,
  bianExampleCreateSecure,
  validateResponse,
} from "../shared/request-builder.js";

const cfg = getConfig();

export const options = {
  thresholds: rpsThresholds(100),
  stages: [
    { duration: "5s", target: 10 },   // Ramp-up a 10 VUs
    { duration: "15s", target: 50 },  // Ramp-up a 50 VUs (100+ RPS)
    { duration: "10s", target: 0 },   // Ramp-down
  ],
};

export function setup() {
  logConfigInfo();
  console.log("Starting BianExampleController RPS test");
}

export default function () {
  group("BianExampleController - RPS Test", function () {
    group("Endpoint 1: POST /{customer_id}/create", function () {
      const resp1 = bianExampleCreate();
      validateResponse(resp1, "BianExampleCreate", 200);
    });

    group("Endpoint 2: POST /new/create (Secure)", function () {
      const resp2 = bianExampleCreateSecure();
      validateResponse(resp2, "BianExampleCreateSecure", 200);
    });
  });
}

export function teardown(data) {
  console.log("BianExampleController RPS test completed");
}
