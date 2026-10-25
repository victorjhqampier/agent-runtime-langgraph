import { sleep } from "k6";
import { SharedArray } from "k6/data";
import { getConfig } from "../config/environments.js";
import { buildThresholds } from "../config/thresholds.js";
import { authHeaders } from "../shared/auth.js";
import { checkResponse, jsonBody, request } from "../shared/http-client.js";

const cfg = getConfig();

const products = new SharedArray("products", function () {
  return JSON.parse(open("../data/products.json"));
});

function readUsersFromCsv() {
  const raw = open("../data/users.csv").trim().split("\n");
  const rows = raw.slice(1);

  return rows.map((line) => {
    const [id, email] = line.split(",");
    return { id, email };
  });
}

const users = new SharedArray("users", readUsersFromCsv);

export const options = {
  scenarios: {
    create_order_rps: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RATE || 10),
      timeUnit: "1s",
      duration: __ENV.DURATION || "2m",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 80),
    },
  },
  thresholds: buildThresholds({
    "http_req_duration{name:create-order}": ["p(95)<700"],
  }),
};

export default function () {
  const user = users[Math.floor(Math.random() * users.length)];
  const product = products[Math.floor(Math.random() * products.length)];

  const payload = {
    userEmail: user.email,
    items: [{
      productId: product.id,
      quantity: product.quantity,
    }],
  };

  const response = request("POST", `${cfg.baseUrl}/orders`, jsonBody(payload), {
    headers: {
      ...authHeaders(),
    },
    tags: { name: "create-order" },
  });

  checkResponse(response, "create-order", Number(__ENV.EXPECTED_STATUS || 201));
  sleep(Number(__ENV.SLEEP || 0.2));
}
