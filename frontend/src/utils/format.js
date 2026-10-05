// Formato de errores de la API y fechas para la UI.
/** Mensaje legible a partir de un error de la API (DRF). */
export function errorMessage(err, fallback = "Ocurrió un error. Intente de nuevo.") {
  const data = err?.response?.data;
  if (!data) return err?.message && !err.response ? "Sin conexión con el servidor." : fallback;
  if (typeof data === "string") return fallback;
  if (Array.isArray(data)) return data[0] || fallback;
  if (data.detail) return data.detail;
  const first = Object.values(data)[0];
  return (Array.isArray(first) ? first[0] : first) || fallback;
}

export const formatDateTime = (s) =>
  s ? new Date(s).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" }) : "-";

export const formatDate = (s) =>
  s ? new Date(`${s}T00:00:00`).toLocaleDateString("es-CO", { dateStyle: "medium" }) : "-";
