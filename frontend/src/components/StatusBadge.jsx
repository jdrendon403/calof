const COLORS = {
  ABIERTA: "bg-amber-100 text-amber-800",
  PENDIENTE: "bg-amber-100 text-amber-800",
  ENVIADO: "bg-amber-100 text-amber-800",
  ATENDIDA: "bg-green-100 text-green-800",
  APROBADA: "bg-sky-100 text-sky-800",
  APROBADO: "bg-green-100 text-green-800",
  ENTREGADA: "bg-green-100 text-green-800",
  RECHAZADA: "bg-red-100 text-red-700",
  DEVUELTO: "bg-red-100 text-red-700",
  BORRADOR: "bg-slate-100 text-slate-600",
};

export default function StatusBadge({ estado, children }) {
  return (
    <span className={`inline-block rounded px-2 py-0.5 text-xs font-semibold ${COLORS[estado] || "bg-slate-100 text-slate-600"}`}>
      {children}
    </span>
  );
}
