import { useEffect, useRef, useState } from "react";
import { campo } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import { errorMessage } from "../../utils/format";

export const input = "mt-1 w-full rounded border border-slate-300 px-3 py-2";
export const label = "block text-sm font-medium text-slate-700";
export const btnPrimary =
  "rounded bg-slate-700 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800 disabled:opacity-50";
export const btnSecondary =
  "rounded border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50";

export function useEsLider() {
  const { user } = useAuth();
  return user?.rol === "LIDER" || user?.rol === "ADMIN";
}

/** Proyectos en los que el usuario puede reportar (asignados; todos para el admin). */
export function useProyectos() {
  const [proyectos, setProyectos] = useState([]);
  useEffect(() => {
    campo.proyectos().then(setProyectos).catch(() => {});
  }, []);
  return proyectos;
}

/** Encabezado de sección con filtro y botón principal. */
export function Toolbar({ titulo, filtro, setFiltro, filtros, accion, onAccion }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <h2 className="text-xl font-semibold text-slate-800">{titulo}</h2>
      <div className="flex flex-wrap items-center gap-2">
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)}
          className="rounded border border-slate-300 px-2 py-2 text-sm">
          {filtros.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
        </select>
        {accion && (
          <button type="button" onClick={onAccion}
            className="rounded bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700">
            {accion}
          </button>
        )}
      </div>
    </div>
  );
}

/** Tarjeta desplegable. Se abre y se desplaza a la vista si `highlight`. */
export function ItemCard({ resumen, children, highlight }) {
  const [open, setOpen] = useState(!!highlight);
  const ref = useRef(null);
  useEffect(() => {
    if (highlight) {
      setOpen(true);
      ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [highlight]);
  return (
    <div ref={ref} className={`rounded-lg bg-white shadow ${highlight ? "ring-2 ring-brand-blue" : ""}`}>
      <button type="button" onClick={() => setOpen(!open)} className="block w-full px-4 py-3 text-left">
        {resumen}
      </button>
      {open && <div className="space-y-3 border-t border-slate-100 px-4 py-3">{children}</div>}
    </div>
  );
}

/** Caja de acción del líder: comentario opcional/obligatorio + botones. */
export function AccionLider({ acciones, placeholder = "Comentario (opcional)" }) {
  const [comentario, setComentario] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const run = async (a) => {
    if (a.requiereComentario && !comentario.trim()) {
      setError("Escriba un comentario para continuar.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await a.onClick(comentario.trim());
      setComentario("");
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="rounded border border-slate-200 bg-slate-50 p-3">
      <textarea value={comentario} onChange={(e) => setComentario(e.target.value)} rows={2}
        placeholder={placeholder} className="w-full rounded border border-slate-300 px-3 py-2 text-sm" />
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
      <div className="mt-2 flex flex-wrap gap-2">
        {acciones.map((a) => (
          <button key={a.label} type="button" disabled={busy} onClick={() => run(a)}
            className={`rounded px-4 py-2 text-sm font-medium text-white disabled:opacity-50 ${a.color || "bg-slate-700 hover:bg-slate-800"}`}>
            {a.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export function Campo({ titulo, children }) {
  if (!children) return null;
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{titulo}</p>
      <div className="mt-0.5 whitespace-pre-line text-sm text-slate-800">{children}</div>
    </div>
  );
}

export function Vacio({ children }) {
  return <p className="rounded-lg bg-white p-6 text-center text-sm text-slate-500 shadow">{children}</p>;
}
