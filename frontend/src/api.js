const API_BASE = "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `Request failed: ${response.status}`);
  }

  return response.json();
}

export function getDailyBriefing() {
  return request("/daily-briefing");
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

export function getWardrobe() {
  return request("/wardrobe");
}

export function addWardrobeItem(payload) {
  return request("/wardrobe", {
    method: "POST",
    body: JSON.stringify(payload),
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

export function getReceipts() {
  return request("/receipts");
}

export function addReceiptText(payload) {
  return request("/receipts/from-text", {
    method: "POST",
    body: JSON.stringify(payload),
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

