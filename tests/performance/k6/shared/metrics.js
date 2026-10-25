import { Counter, Rate, Trend } from "k6/metrics";

export const requestErrors = new Counter("request_errors");
export const requestSuccessRate = new Rate("request_success_rate");
export const transactionSuccessRate = new Rate("transaction_success_rate");
export const responseBodySize = new Trend("response_body_size", true);
export const transactionDuration = new Trend("transaction_duration", true);

export function recordResponse(response, tags = {}) {
  const ok = response.status >= 200 && response.status < 400;

  requestSuccessRate.add(ok, tags);
  responseBodySize.add((response.body || "").length, tags);

  if (!ok) {
    requestErrors.add(1, tags);
  }

  return ok;
}

export function recordTransaction(name, durationMs, success) {
  const tags = { transaction: name };
  transactionDuration.add(durationMs, tags);
  transactionSuccessRate.add(success, tags);
}
