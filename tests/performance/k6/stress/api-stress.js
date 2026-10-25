import { sleep } from "k6";
import { getConfig } from "../config/environments.js";
import { buildThresholds } from "../config/thresholds.js";
import { checkResponse, request } from "../shared/http-client.js";

const cfg = getConfig();

export const options = {
  scenarios: {
    stress_test: {
      executor: "ramping-arrival-rate",
      startRate: Number(__ENV.START_RATE || 10),
      timeUnit: "1s",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 20),
      maxVUs: Number(__ENV.MAX_VUS || 200),
      stages: [
        { target: Number(__ENV.STAGE1_RATE || 30), duration: __ENV.STAGE1_DURATION || "2m" },
        { target: Number(__ENV.STAGE2_RATE || 80), duration: __ENV.STAGE2_DURATION || "3m" },
        { target: Number(__ENV.STAGE3_RATE || 120), duration: __ENV.STAGE3_DURATION || "3m" },
        { target: 0, duration: __ENV.COOLDOWN_DURATION || "1m" },
      ],
    },
  },
  thresholds: buildThresholds({
    http_req_failed: ["rate<0.03"],
  }),
};

export default function () {
  const response = request("GET", `${cfg.baseUrl}/health`, null, {
    tags: { name: "stress-health" },
  });

  checkResponse(response, "stress-health", 200);
  sleep(Number(__ENV.SLEEP || 0.05));
}
