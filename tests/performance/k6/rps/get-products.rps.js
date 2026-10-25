import { sleep } from "k6";
import { SharedArray } from "k6/data";
import { getConfig } from "../config/environments.js";
import { buildThresholds } from "../config/thresholds.js";
import { authHeaders } from "../shared/auth.js";
import { checkResponse, request } from "../shared/http-client.js";

const cfg = getConfig();

const products = new SharedArray("products", function () {
  return JSON.parse(open("../data/products.json"));
});

export const options = {
  scenarios: {
    get_products_rps: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.RATE || 15),
      timeUnit: "1s",
      duration: __ENV.DURATION || "2m",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 8),
      maxVUs: Number(__ENV.MAX_VUS || 50),
    },
  },
  thresholds: buildThresholds({
    "http_req_duration{name:get-products}": ["p(95)<500"],
  }),
};

export default function () {
  const idx = Math.floor(Math.random() * products.length);
  const product = products[idx];

  const response = request("GET", `${cfg.baseUrl}/products/${product.id}`, null, {
    headers: {
      ...authHeaders(),
    },
    tags: { name: "get-products" },
  });

  checkResponse(response, "get-products", 200);
  sleep(Number(__ENV.SLEEP || 0.1));
}
