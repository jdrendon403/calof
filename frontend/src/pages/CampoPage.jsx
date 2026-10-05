import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import NovedadesView from "./campo/NovedadesView";
import InsumosView from "./campo/InsumosView";
import InformesView from "./campo/InformesView";

const TABS = [
  { to: "novedades", label: "Novedades" },
  { to: "insumos", label: "Insumos" },
  { to: "informes", label: "Informes" },
];

export default function CampoPage() {
  return (
    <div className="space-y-4">
      <nav className="flex gap-1 rounded-lg bg-white p-1 shadow">
        {TABS.map((t) => (
          <NavLink
            key={t.to}
            to={t.to}
            className={({ isActive }) =>
              `flex-1 rounded px-3 py-2 text-center text-sm font-medium ${
                isActive ? "bg-slate-700 text-white" : "text-slate-700 hover:bg-slate-100"
              }`
            }
          >
            {t.label}
          </NavLink>
        ))}
      </nav>
      <Routes>
        <Route index element={<Navigate to="novedades" replace />} />
        <Route path="novedades" element={<NovedadesView />} />
        <Route path="insumos" element={<InsumosView />} />
        <Route path="informes" element={<InformesView />} />
      </Routes>
    </div>
  );
}
