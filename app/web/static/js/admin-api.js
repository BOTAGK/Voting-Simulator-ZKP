import {
  formatApiError,
  readJsonResponse,
  readTextResponse,
} from "./shared.js";

export async function fetchAdminJson(url, options) {
  const response = await fetch(url, options);
  const data = await readJsonResponse(response);

  if (!response.ok) {
    throw new Error(formatApiError(data, "Administrator operation failed."));
  }

  return data;
}

export async function fetchAdminText(url, options) {
  const response = await fetch(url, options);
  const text = await readTextResponse(response);

  if (!response.ok) {
    throw new Error(text || "Administrator operation failed.");
  }

  return text;
}
