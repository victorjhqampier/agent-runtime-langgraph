import { sleep } from "k6";
import { getConfig } from "../config/environments.js";
import { buildThresholds } from "../config/thresholds.js";
import { checkResponse, request } from "../shared/http-client.js";

const cfg = getConfig();

export const options = {
  scenarios: {
    soak_test: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RATE || 8),
      timeUnit: "1s",
      duration: __ENV.DURATION || "60m",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 100),
    },
  },
  thresholds: buildThresholds({
    http_req_duration: ["p(95)<900"],
    http_req_failed: ["rate<0.02"],
  }),
};

export default function () {
  const response = request("GET", `${cfg.baseUrl}/health`, null, {
    tags: { name: "soak-health" },
  });

  checkResponse(response, "soak-health", 200);
  sleep(Number(__ENV.SLEEP || 0.1));
}
