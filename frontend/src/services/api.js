// src/services/api.js
export const API_BASE =
  process.env.REACT_APP_API_URL || "http://localhost:8000";

export async function translate(code) {
  const res = await fetch(`${API_BASE}/translate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });

  const data = await res.json();

  if (!res.ok || !data.success) {
    // Извлекаем ошибки из структурированного ответа
    const errors = data.errors || [
      { type: "general", message: data.detail || "Unknown error" },
    ];
    throw { errors }; // Кидаем объект с errors
  }

  return data.cpp;
}
