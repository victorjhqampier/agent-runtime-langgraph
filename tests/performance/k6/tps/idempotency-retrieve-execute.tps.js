// tps/idempotency-retrieve-execute.tps.js

import { check } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

import { getConfig } from "../config/environments.js";
import { jsonBody, request } from "../shared/http-client.js";

const cfg = getConfig();

const TARGET_TPS = Number(__ENV.TPS || 900);
const VUS = Number(__ENV.VUS || 60);
const DURATION = __ENV.DURATION || "30s";

const BASE_URL = __ENV.BASE_URL || "http://127.0.0.1:8000";

const DEVICE_IDENTIFIER = __ENV.DEVICE_IDENTIFIER || "dskfhshfusdfsb";
const CHANNEL_IDENTIFIER = __ENV.CHANNEL_IDENTIFIER || "dskfhshfusdfsb";
const ACCOUNT_ID = __ENV.ACCOUNT_ID || "1234567890";

const GET_STATUS = Number(__ENV.GET_STATUS || 200);
const POST_STATUS = Number(__ENV.POST_STATUS || 200);

// =====================================================
// MÉTRICAS DE NEGOCIO
// =====================================================

const transactionsTotal = new Counter("transactions_total");
const transactionsSuccess = new Counter("transactions_success");
const transactionsFailed = new Counter("transactions_failed");

const transactionSuccessRate = new Rate("transaction_success_rate");
const transactionDuration = new Trend("transaction_duration", true);

// =====================================================
// CONFIGURACIÓN K6
// =====================================================

export const options = {
  scenarios: {
    idempotency_tps: {
      executor: "constant-arrival-rate",

      rate: TARGET_TPS,
      timeUnit: "1s",
      duration: DURATION,

      preAllocatedVUs: VUS,
      maxVUs: VUS,

      gracefulStop: "5s",
    },
  },

  thresholds: {
    // No deben descartarse transacciones.
    dropped_iterations: ["count==0"],

    // Al menos 99 % de transacciones exitosas.
    transaction_success_rate: ["rate>=0.99"],

    // Menos del 1 % de errores HTTP.
    http_req_failed: ["rate<0.01"],

    // Al menos 99 % de checks exitosos.
    checks: ["rate>=0.99"],

    // Latencia P95 de la transacción completa.
    transaction_duration: ["p(95)<1000"],
  },
};

// =====================================================
// UTILIDADES
// =====================================================

function uuid() {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(
    /[xy]/g,
    (character) => {
      const random = Math.floor(Math.random() * 16);

      const value =
        character === "x"
          ? random
          : (random & 0x3) | 0x8;

      return value.toString(16);
    }
  );
}

function buildHeaders(messageIdentifier) {
  return {
    accept: "*/*",
    "device-identifier": DEVICE_IDENTIFIER,
    "message-identifier": messageIdentifier,
    "channel-identifier": CHANNEL_IDENTIFIER,
  };
}

// =====================================================
// REGISTRO DE TRANSACCIÓN
// =====================================================

function recordResult(startedAt, success) {
  const duration = Date.now() - startedAt;

  transactionsTotal.add(1);
  transactionSuccessRate.add(success);
  transactionDuration.add(duration);

  if (success) {
    transactionsSuccess.add(1);
  } else {
    transactionsFailed.add(1);
  }
}

// =====================================================
// FLUJO TRANSACCIONAL
// =====================================================

export default function () {
  const startedAt = Date.now();

  const retrieveMessageId = uuid();
  const executeMessageId = uuid();

  // ===================================================
  // PASO 1: GET /retrieve
  // ===================================================

  const retrieveResponse = request(
    "GET",
    `${BASE_URL}/business-api-b/v1/idempotency/retrieve`,
    null,
    {
      headers: buildHeaders(retrieveMessageId),

      tags: {
        name: "idempotency-retrieve",
        endpoint: "retrieve",
        operation: "GET",
      },
    }
  );

  const retrieveOk = check(retrieveResponse, {
    "GET retrieve status correcto": (response) =>
      response.status === GET_STATUS,
  });

  if (!retrieveOk) {
    recordResult(startedAt, false);
    return;
  }

  // ===================================================
  // PASO 2: POST /execute
  // ===================================================

  const executeResponse = request(
    "POST",
    `${BASE_URL}/business-api-b/v1/idempotency/execute`,
    jsonBody({
      previewMessageIdentification: retrieveMessageId,
      identificationForAccount: ACCOUNT_ID,
    }),
    {
      headers: {
        ...buildHeaders(executeMessageId),
        "Content-Type": "application/json",
      },

      tags: {
        name: "idempotency-execute",
        endpoint: "execute",
        operation: "POST",
      },
    }
  );

  const executeOk = check(executeResponse, {
    "POST execute status correcto": (response) =>
      response.status === POST_STATUS,
  });

  // ===================================================
  // RESULTADO DE TRANSACCIÓN COMPLETA
  // ===================================================

  recordResult(startedAt, retrieveOk && executeOk);
}