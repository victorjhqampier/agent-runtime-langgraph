import http from "k6/http";
import { check } from "k6";
import { getConfig } from "../config/environments.js";
import { recordResponse } from "./metrics.js";

function mergeParams(params = {}) {
  const cfg = getConfig();
  const headers = {
    "Content-Type": "application/json",
    ...(params.headers || {}),
  };

  return {
    ...params,
    timeout: params.timeout || cfg.httpTimeout,
    headers,
  };
}

export function request(method, url, body = null, params = {}) {
  const merged = mergeParams(params);
  const response = http.request(method, url, body, merged);
  recordResponse(response, merged.tags || {});
  return response;
}

export function checkResponse(response, name, expectedStatus = 200) {
  return check(response, {
    [`${name} - status is ${expectedStatus}`]: (r) => r.status === expectedStatus,
  });
}

export function jsonBody(payload) {
  return JSON.stringify(payload);
}
