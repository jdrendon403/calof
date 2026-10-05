import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { notificaciones as api } from "../api/client";
import { formatDateTime } from "../utils/format";

/** Campana con el número de avisos sin leer; consulta el servidor cada 60 s. */
export default function NotificationBell() {
  const [total, setTotal] = useState(0);
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const boxRef = useRef(null);
  const navigate = useNavigate();

  const refresh = useCallback(() => api.noLeidas().then(setTotal).catch(() => {}), []);

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 60000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    if (!open) return;
    const close = (e) => !boxRef.current?.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, [open]);

  const toggle = async () => {
    if (!open) setItems(await api.list().catch(() => []));
    setOpen(!open);
  };

  const go = async (n) => {
    setOpen(false);
    if (!n.leida) await api.marcarLeidas([n.id]).catch(() => {});
    refresh();
    if (n.enlace) navigate(n.enlace);
  };

  const markAll = async () => {
    await api.marcarLeidas().catch(() => {});
    setItems((prev) => prev.map((n) => ({ ...n, leida: true })));
    refresh();
  };

  return (
    <div ref={boxRef} className="relative">
      <button type="button" onClick={toggle} aria-label={`Avisos (${total} sin leer)`}
        className="relative rounded px-2 py-1.5 text-slate-700 hover:bg-slate-100">
        <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 0 1-3.4 0" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {total > 0 && (
          <span className="absolute -right-0.5 -top-0.5 min-w-[1.1rem] rounded-full bg-red-600 px-1 text-center text-[0.65rem] font-bold leading-[1.1rem] text-white">
            {total > 99 ? "99+" : total}
          </span>
        )}
      </button>
      {open && (
        <div className="absolute right-0 z-20 mt-2 w-80 max-w-[calc(100vw-2rem)] rounded-lg border border-slate-200 bg-white shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-100 px-3 py-2">
            <span className="text-sm font-semibold text-slate-800">Avisos</span>
            {items.some((n) => !n.leida) && (
              <button type="button" onClick={markAll} className="text-xs text-brand-blue hover:underline">
                Marcar todos como leídos
              </button>
            )}
          </div>
          <ul className="max-h-96 overflow-y-auto">
            {items.length === 0 && <li className="px-3 py-6 text-center text-sm text-slate-500">No tiene avisos.</li>}
            {items.map((n) => (
              <li key={n.id}>
                <button type="button" onClick={() => go(n)}
                  className={`block w-full px-3 py-2 text-left text-sm hover:bg-slate-50 ${n.leida ? "text-slate-500" : "bg-sky-50 font-medium text-slate-800"}`}>
                  {n.texto}
                  <span className="mt-0.5 block text-xs font-normal text-slate-400">{formatDateTime(n.creada_en)}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
