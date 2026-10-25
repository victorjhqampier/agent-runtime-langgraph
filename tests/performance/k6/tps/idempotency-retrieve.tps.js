// tps/idempotency-retrieve.tps.js
// Genera previews para el flujo de idempotencia.
// Ejecutar desde la raíz:
// k6 run tests/performance/k6/tps/idempotency-retrieve.tps.js --env DURATION=30s

import { check } from "k6";
import { SharedArray } from "k6/data";
import { request } from "../shared/http-client.js";
import { recordTransaction } from "../shared/metrics.js";

const identifiers = new SharedArray("idempotency-uuids", () => JSON.parse(open("../data/idempotency-uuids.json")));

// Variables configurables a demanda.
const TARGET_TPS = Number(__ENV.TPS || 900);
const VUS = Number(__ENV.VUS || 30);
const DURATION = __ENV.DURATION || "30s";
const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
const DEVICE_IDENTIFIER = __ENV.DEVICE_IDENTIFIER || "dskfhshfusdfsb";
const CHANNEL_IDENTIFIER = __ENV.CHANNEL_IDENTIFIER || "dskfhshfusdfsb";
const EXPECTED_STATUS = Number(__ENV.GET_STATUS || 200);

export const options = {
  scenarios: {
    idempotency_retrieve_tps: {
      executor: "constant-arrival-rate",
      rate: TARGET_TPS,
      timeUnit: "1s",
      duration: DURATION,
      preAllocatedVUs: VUS,
      maxVUs: VUS,
    },
  },
  thresholds: {
    iterations: [`rate>=${TARGET_TPS}`],
    dropped_iterations: ["count==0"],
    http_req_failed: ["rate<0.01"],
    checks: ["rate>0.99"],
    transaction_success_rate: ["rate>0.99"],
  },
};

function identifierForIteration() {
  const index = (((__ITER * VUS) + (__VU - 1)) % identifiers.length + identifiers.length) % identifiers.length;
  return identifiers[index];
}

export default function () {
  const startedAt = Date.now();
  const messageIdentifier = identifierForIteration();
  const response = request("GET", `${BASE_URL}/business-api-b/v1/idempotency/retrieve`, null, {
    headers: {
      accept: "*/*",
      "device-identifier": DEVICE_IDENTIFIER,
      "message-identifier": messageIdentifier,
      "channel-identifier": CHANNEL_IDENTIFIER,
    },
    tags: { name: "idempotency-retrieve", endpoint: "/business-api-b/v1/idempotency/retrieve" },
  });

  const success = check(response, {
    [`GET /idempotency/retrieve returns ${EXPECTED_STATUS}`]: (result) => result.status === EXPECTED_STATUS,
  });
  recordTransaction("idempotency-retrieve", Date.now() - startedAt, success);
}
