const API_BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    headers: isFormData
      ? options.headers || {}
      : {
          "Content-Type": "application/json",
          ...(options.headers || {}),
        },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export function getDailyBriefing() {
  return request("/daily-briefing");
}

export function askAssistant(question) {
  return request("/assistant/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export function getGroceries() {
  return request("/groceries");
}

export function addGrocery(payload) {
  return request("/groceries", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteGrocery(id) {
  return request(`/groceries/${id}`, {
    method: "DELETE",
  });
}

export function getWardrobe() {
  return request("/wardrobe");
}

export function addWardrobeItem(payload) {
  return request("/wardrobe", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteWardrobeItem(id) {
  return request(`/wardrobe/${id}`, {
    method: "DELETE",
  });
}

export function uploadWardrobePhoto(payload) {
  const formData = new FormData();
  Object.entries(payload).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      formData.append(key, value);
    }
  });
  return request("/wardrobe/upload-photo", {
    method: "POST",
    body: formData,
  });
}

export function getSchedule() {
  return request("/schedule");
}

export function addScheduleItem(payload) {
  return request("/schedule", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteScheduleItem(id) {
  return request(`/schedule/${id}`, {
    method: "DELETE",
  });
}

export function importCalendarUrl(url) {
  return request("/calendar/import-ics-url", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function getCalendarSources() {
  return request("/calendar/sources");
}

export function getAppleCalendarStatus() {
  return request("/calendar/apple/status");
}

export function addCalendarSource(payload) {
  return request("/calendar/sources", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function deleteCalendarSource(id) {
  return request(`/calendar/sources/${id}`, {
    method: "DELETE",
  });
}

export function syncCalendar() {
  return request("/calendar/sync", {
    method: "POST",
  });
}

export function getReceipts() {
  return request("/receipts");
}

export function deleteReceipt(id) {
  return request(`/receipts/${id}`, {
    method: "DELETE",
  });
}

export function addReceiptText(payload) {
  return request("/receipts/from-text", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function scanReceiptPhoto(payload) {
  const formData = new FormData();
  formData.append("store", payload.store);
  formData.append("purchased_on", payload.purchased_on);
  formData.append("file", payload.file);
  return request("/receipts/scan-photo", {
    method: "POST",
    body: formData,
  });
}

export function processReceiptText(receiptId, rawText) {
  return request(`/receipts/${receiptId}/process-text`, {
    method: "POST",
    body: JSON.stringify({ raw_text: rawText }),
  });
}

export function getExpenses(month) {
  return request(`/expenses/monthly${month ? `?month=${month}` : ""}`);
}

export function getBudgetStatus(month) {
  return request(`/budget/status${month ? `?month=${month}` : ""}`);
}

export function getOcrStatus() {
  return request("/ocr/status");
}

export { API_BASE };
