// shared/request-builder.js
// Constructor de requests específicos para los 3 controllers

import { getConfig } from "../config/environments.js";
import { request, checkResponse, jsonBody } from "./http-client.js";

const cfg = getConfig();

/**
 * Headers comunes requeridos por todos los endpoints
 */
export function getCommonHeaders() {
  return {
    "Content-Type": "application/json",
    "device_identifier": cfg.deviceIdentifier,
    "message_identifier": cfg.messageIdentifier + "-" + Math.random(),
    "channel_identifier": cfg.channelIdentifier,
  };
}

/**
 * Body estándar para requests de ejemplo
 */
export function getExampleRequestBody() {
  return {
    example_field: "test_value_" + Math.random().toString(36).substr(2, 9),
    timestamp: new Date().toISOString(),
  };
}

/**
 * POST /{customer_id}/create - BianExampleController
 * Uso sin autenticación
 */
export function bianExampleCreate(customerId = cfg.customerId) {
  const url = `${cfg.baseUrl}/bian-example/${customerId}/create`;
  const body = jsonBody(getExampleRequestBody());
  const params = {
    headers: getCommonHeaders(),
    timeout: cfg.httpTimeout,
    tags: { name: "BianExampleCreate", endpoint: "/bian-example/{id}/create" },
  };
  
  return request("POST", url, body, params);
}

/**
 * POST /new/create - BianExampleController
 * Uso con autenticación Cognito
 */
export function bianExampleCreateSecure(authToken = null) {
  const url = `${cfg.baseUrl}/bian-example/new/create`;
  const body = jsonBody(getExampleRequestBody());
  const headers = getCommonHeaders();
  
  if (authToken) {
    headers["Authorization"] = `Bearer ${authToken}`;
  }
  
  const params = {
    headers,
    timeout: cfg.httpTimeout,
    tags: { name: "BianExampleCreateSecure", endpoint: "/bian-example/new/create" },
  };
  
  return request("POST", url, body, params);
}

/**
 * POST /{customer_id}/create - NoBianExampleController
 */
export function noBianExampleCreate(customerId = cfg.customerId) {
  const url = `${cfg.baseUrl}/no-bian-example/${customerId}/create`;
  const body = jsonBody(getExampleRequestBody());
  const params = {
    headers: getCommonHeaders(),
    timeout: cfg.httpTimeout,
    tags: { name: "NoBianExampleCreate", endpoint: "/no-bian-example/{id}/create" },
  };
  
  return request("POST", url, body, params);
}

/**
 * POST /{customer_id}/create-redis - NoBianExampleRedisController
 * Usa ExampleRedisUsecase con caché
 */
export function noBianExampleRedisCreate(customerId = cfg.customerId) {
  const url = `${cfg.baseUrl}/no-bian-redis/${customerId}/create-redis`;
  const body = jsonBody(getExampleRequestBody());
  const params = {
    headers: getCommonHeaders(),
    timeout: cfg.httpTimeout,
    tags: { name: "NoBianExampleRedisCreate", endpoint: "/no-bian-redis/{id}/create-redis" },
  };
  
  return request("POST", url, body, params);
}

/**
 * Validación estándar de respuesta
 */
export function validateResponse(response, operationName, expectedStatus = 200) {
  return checkResponse(response, operationName, expectedStatus);
}

/**
 * Extrae datos de la respuesta para análisis
 */
export function extractResponseData(response) {
  try {
    return JSON.parse(response.body);
  } catch (e) {
    return null;
  }
}
