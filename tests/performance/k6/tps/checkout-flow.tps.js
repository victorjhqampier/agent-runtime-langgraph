import { sleep } from "k6";
import { SharedArray } from "k6/data";
import { getConfig } from "../config/environments.js";
import { tpsThresholds } from "../config/thresholds.js";
import { authHeaders } from "../shared/auth.js";
import { checkResponse, jsonBody, request } from "../shared/http-client.js";
import { recordTransaction } from "../shared/metrics.js";

const cfg = getConfig();

const products = new SharedArray("products-checkout", function () {
  return JSON.parse(open("../data/products.json"));
});

export const options = {
  scenarios: {
    checkout_tps: {
      executor: "constant-arrival-rate",
      rate: Number(__ENV.TPS || 5),
      timeUnit: "1s",
      duration: __ENV.DURATION || "3m",
      preAllocatedVUs: Number(__ENV.PRE_VUS || 10),
      maxVUs: Number(__ENV.MAX_VUS || 80),
    },
  },
  thresholds: tpsThresholds(Number(__ENV.TPS || 5)),
};

export default function () {
  const startedAt = Date.now();
  const product = products[Math.floor(Math.random() * products.length)];
  const headers = { ...authHeaders() };

  const addToCart = request("POST", `${cfg.baseUrl}/cart/items`, jsonBody({
    productId: product.id,
    quantity: product.quantity,
  }), {
    headers,
    tags: { name: "checkout-add-to-cart" },
  });

  const cartOk = checkResponse(addToCart, "checkout-add-to-cart", Number(__ENV.CART_STATUS || 200));

  const checkout = request("POST", `${cfg.baseUrl}/checkout`, jsonBody({
    paymentMethod: "card",
  }), {
    headers,
    tags: { name: "checkout-complete" },
  });

  const checkoutOk = checkResponse(checkout, "checkout-complete", Number(__ENV.CHECKOUT_STATUS || 200));

  recordTransaction("checkout-flow", Date.now() - startedAt, cartOk && checkoutOk);
  sleep(Number(__ENV.SLEEP || 0.2));
}
