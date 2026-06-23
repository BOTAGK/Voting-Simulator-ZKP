export function setMessage(form, text, type) {
  const message = form.querySelector("[data-form-message]");

  if (!message) {
    return;
  }

  message.textContent = text;
  message.className = `form-message ${type || ""}`;
}

export async function readJsonResponse(response) {
  const text = await response.text();

  if (!text) {
    return {};
  }

  try {
    return JSON.parse(text);
  } catch {
    return { detail: text };
  }
}

export async function readTextResponse(response) {
  return response.text();
}

export function formatApiError(data, fallback) {
  return data.detail || fallback;
}

export function setElementMessage(element, text, type) {
  if (!element) {
    return;
  }

  element.textContent = text;
  element.className = `form-message ${type || ""}`;
}

export function downloadTextFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export function toApiDateTime(value) {
  if (!value) {
    return null;
  }

  return new Date(value).toISOString();
}

function parseApiDateTime(value) {
  if (!value) {
    return null;
  }

  const rawValue = String(value).trim();
  const normalizedValue = rawValue.includes("T")
    ? rawValue
    : rawValue.replace(" ", "T");
  const hasTimezone = /(?:[zZ]|[+-]\d{2}:?\d{2})$/.test(normalizedValue);
  const date = new Date(hasTimezone ? normalizedValue : `${normalizedValue}Z`);

  if (Number.isNaN(date.getTime())) {
    return null;
  }

  return date;
}

export function toLocalDateTimeInput(value) {
  const date = parseApiDateTime(value);

  if (!date) {
    return "";
  }

  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}

export function formatLocalDateTime(value) {
  const localDateTime = toLocalDateTimeInput(value);
  return localDateTime ? localDateTime.replace("T", " ") : "not set";
}

export function renderLocalDateTimes(root = document) {
  for (const element of root.querySelectorAll("[data-local-datetime]")) {
    element.textContent = formatLocalDateTime(element.dataset.localDatetime);
  }
}
