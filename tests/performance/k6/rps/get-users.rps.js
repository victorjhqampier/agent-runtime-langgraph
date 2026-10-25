import { sleep } from "k6";
import { getConfig } from "../config/environments.js";
import { buildThresholds } from "../config/thresholds.js";
import { authHeaders } from "../shared/auth.js";
import { checkResponse, request } from "../shared/http-client.js";

const cfg = getConfig();

export const options = {
  scenarios: {
    get_users_rps: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RATE || 20),
      timeUnit: "1s",
      duration: __ENV.DURATION || "2m",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 60),
    },
  },
  thresholds: buildThresholds({
    "http_req_duration{name:get-users}": ["p(95)<500"],
  }),
};

export default function () {
  const response = request("GET", `${cfg.baseUrl}/users`, null, {
    headers: {
      ...authHeaders(),
    },
    tags: { name: "get-users" },
  });

  checkResponse(response, "get-users", 200);
  sleep(Number(__ENV.SLEEP || 0.1));
}
