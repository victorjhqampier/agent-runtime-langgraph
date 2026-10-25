// rps/no-bian-example.rps.js
// Tests RPS para NoBianExampleController
// Ejecución: k6 run rps/no-bian-example.rps.js --env BASE_URL=http://127.0.0.1:8000 --vus 50 --duration 30s

import { group } from "k6";
import { rpsThresholds } from "../config/thresholds.js";
import { getConfig, logConfigInfo } from "../config/environments.js";
import { noBianExampleCreate, validateResponse } from "../shared/request-builder.js";

const cfg = getConfig();

export const options = {
  thresholds: rpsThresholds(100),
  stages: [
    { duration: "5s", target: 10 },
    { duration: "15s", target: 50 },
    { duration: "10s", target: 0 },
  ],
};

export function setup() {
  logConfigInfo();
  console.log("Starting NoBianExampleController RPS test");
}

export default function () {
  group("NoBianExampleController - RPS Test", function () {
    const resp = noBianExampleCreate();
    validateResponse(resp, "NoBianExampleCreate", 200);
  });
}

export function teardown(data) {
  console.log("NoBianExampleController RPS test completed");
}
