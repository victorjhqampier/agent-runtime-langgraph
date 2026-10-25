// tps/idempotency-execute.tps.js
// Reutiliza los previews creados por idempotency-retrieve.tps.js.
// Ejecutar desde la raíz:
// k6 run tests/performance/k6/tps/idempotency-execute.tps.js --env DURATION=30s

import { check } from "k6";
import { SharedArray } from "k6/data";
import { jsonBody, request } from "../shared/http-client.js";
import { recordTransaction } from "../shared/metrics.js";

const identifiers = new SharedArray("idempotency-uuids", () => JSON.parse(open("../data/idempotency-uuids.json")));

// Variables configurables a demanda.
const TARGET_TPS = Number(__ENV.TPS || 900);
const VUS = Number(__ENV.VUS || 30);
const DURATION = __ENV.DURATION || "30s";
const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";
const DEVICE_IDENTIFIER = __ENV.DEVICE_IDENTIFIER || "dskfhshfusdfsb";
const CHANNEL_IDENTIFIER = __ENV.CHANNEL_IDENTIFIER || "dskfhshfusdfsb";
const ACCOUNT_ID = __ENV.ACCOUNT_ID || "1234567890";
const EXPECTED_STATUS = Number(__ENV.POST_STATUS || 200);

export const options = {
  scenarios: {
    idempotency_execute_tps: {
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
  const previewMessageIdentifier = identifierForIteration();
  // const messageIdentifier = `${previewMessageIdentifier}`;
  const response = request(
    "POST",
    `${BASE_URL}/business-api-b/v1/idempotency/execute`,
    jsonBody({
      previewMessageIdentification: previewMessageIdentifier,
      identificationForAccount: ACCOUNT_ID,
    }),
    {
      headers: {
        accept: "*/*",
        "device-identifier": DEVICE_IDENTIFIER,
        "message-identifier": previewMessageIdentifier,
        "channel-identifier": CHANNEL_IDENTIFIER,
        "Content-Type": "application/json",
      },
      tags: { name: "idempotency-execute", endpoint: "/business-api-b/v1/idempotency/execute" },
    },
  );

  const success = check(response, {
    [`POST /idempotency/execute returns ${EXPECTED_STATUS}`]: (result) => result.status === EXPECTED_STATUS,
  });
  recordTransaction("idempotency-execute", Date.now() - startedAt, success);
}
