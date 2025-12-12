// src/services/api.js
export const API_BASE =
  process.env.REACT_APP_API_URL || "http://localhost:8000";

export async function translate(code) {
  const res = await fetch(`${API_BASE}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });

  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      msg = err.detail ? err.detail : msg;
    } catch (_) {}
    throw new Error(msg);
  }

  const data = await res.json();
  return data.cpp; // сервер возвращает { cpp: "..." }
}
