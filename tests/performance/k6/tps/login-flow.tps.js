import { sleep } from "k6";
import { SharedArray } from "k6/data";
import { getConfig } from "../config/environments.js";
import { tpsThresholds } from "../config/thresholds.js";
import { checkResponse, jsonBody, request } from "../shared/http-client.js";
import { recordTransaction } from "../shared/metrics.js";

const cfg = getConfig();

function readUsersFromCsv() {
  const raw = open("../data/users.csv").trim().split("\n");
  const rows = raw.slice(1);

  return rows.map((line) => {
    const [, email, password] = line.split(",");
    return { email, password };
  });
}

const users = new SharedArray("users-for-login", readUsersFromCsv);

export const options = {
  scenarios: {
    login_tps: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.TPS || 8),
      timeUnit: "1s",
      duration: __ENV.DURATION || "2m",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 60),
    },
  },
  thresholds: tpsThresholds(Number(__ENV.TPS || 8)),
};

export default function () {
  const user = users[Math.floor(Math.random() * users.length)];
  const startedAt = Date.now();

  const response = request("POST", `${cfg.baseUrl}/auth/login`, jsonBody({ username: user.email, password: user.password }), {
    tags: { name: "login-flow" },
  });

  const success = checkResponse(response, "login-flow", 200);
  recordTransaction("login-flow", Date.now() - startedAt, success);
  sleep(Number(__ENV.SLEEP || 0.1));
}
