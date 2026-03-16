/**
 * Convierte minutos a formato HH:MM
 * @param {number|null} minutes
 * @returns {string}
 */
export function minutesToHHMM(minutes) {
  if (minutes == null) return "-";
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}`;
}
