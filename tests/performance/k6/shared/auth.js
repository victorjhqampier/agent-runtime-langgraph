import { getConfig } from "../config/environments.js";
import { checkResponse, jsonBody, request } from "./http-client.js";

let cachedToken;

export function login(username, password) {
  const cfg = getConfig();
  const response = request("POST", `${cfg.baseUrl}/auth/login`, jsonBody({ username, password }), {
    tags: { name: "auth-login" },
  });

  const ok = checkResponse(response, "auth-login", 200);

  if (!ok) {
    return null;
  }

  const parsed = response.json();
  return parsed?.access_token || parsed?.token || null;
}

export function getAuthToken() {
  if (cachedToken) {
    return cachedToken;
  }

  const cfg = getConfig();
  cachedToken = login(cfg.username, cfg.password);
  return cachedToken;
}

export function authHeaders() {
  const token = getAuthToken();

  if (!token) {
    return {};
  }

  return {
    Authorization: `Bearer ${token}`,
  };
}
