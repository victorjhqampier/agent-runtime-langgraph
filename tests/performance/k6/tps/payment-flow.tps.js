import { sleep } from "k6";
import { getConfig } from "../config/environments.js";
import { tpsThresholds } from "../config/thresholds.js";
import { authHeaders } from "../shared/auth.js";
import { checkResponse, jsonBody, request } from "../shared/http-client.js";
import { recordTransaction } from "../shared/metrics.js";

const cfg = getConfig();

export const options = {
  scenarios: {
    payment_tps: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.TPS || 4),
      timeUnit: "1s",
      duration: __ENV.DURATION || "3m",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 8),
      maxVUs: Number(__ENV.MAX_VUS || 70),
    },
  },
  thresholds: tpsThresholds(Number(__ENV.TPS || 4)),
};

export default function () {
  const startedAt = Date.now();
  const headers = { ...authHeaders() };

  const intentResponse = request("POST", `${cfg.baseUrl}/payments/intents`, jsonBody({
    amount: Number(__ENV.PAYMENT_AMOUNT || 149.99),
    currency: __ENV.PAYMENT_CURRENCY || "USD",
  }), {
    headers,
    tags: { name: "payment-create-intent" },
  });

  const intentOk = checkResponse(intentResponse, "payment-create-intent", Number(__ENV.INTENT_STATUS || 201));
  const intentId = intentResponse.json("id") || intentResponse.json("intentId") || "mock-intent-id";

  const confirmResponse = request("POST", `${cfg.baseUrl}/payments/confirm`, jsonBody({
    intentId,
  }), {
    headers,
    tags: { name: "payment-confirm" },
  });

  const confirmOk = checkResponse(confirmResponse, "payment-confirm", Number(__ENV.CONFIRM_STATUS || 200));

  recordTransaction("payment-flow", Date.now() - startedAt, intentOk && confirmOk);
  sleep(Number(__ENV.SLEEP || 0.2));
}
