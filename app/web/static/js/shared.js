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

export function toLocalDateTimeInput(value) {
  if (!value) {
    return "";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return "";
  }

  const localDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return localDate.toISOString().slice(0, 16);
}
