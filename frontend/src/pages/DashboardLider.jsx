import { useState, useEffect } from "react";
import { minutesToHHMM } from "../utils/time";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { projects as projectsApi, time as timeApi, users as usersApi, reports as reportsApi } from "../api/client";
import CuadrillaManager from "../components/CuadrillaManager";

export default function DashboardLider() {
  const [projects, setProjects] = useState([]);
  const [timeEntries, setTimeEntries] = useState([]);
  const [users, setUsers] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [selectedProject, setSelectedProject] = useState(null);
  const [assignUserIds, setAssignUserIds] = useState([]);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newProject, setNewProject] = useState({ nombre: "", descripcion: "", cliente: "", estado: "ABIERTO" });
  const [settlement, setSettlement] = useState(null);
  const [settlementPeriod, setSettlementPeriod] = useState("month");

  const fetchLiveData = () => {
    timeApi.list().then(setTimeEntries).catch(console.error);
    reportsApi.settlement(settlementPeriod).then(setSettlement).catch(console.error);
  };

  useEffect(() => {
    projectsApi.list().then(setProjects).catch(console.error);
    usersApi.list().then(setUsers).catch(console.error);
    fetchLiveData();

    const interval = setInterval(fetchLiveData, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    reportsApi.settlement(settlementPeriod).then(setSettlement).catch(console.error);
  }, [settlementPeriod]);

  useEffect(() => {
    const byProject = {};
    timeEntries.forEach((e) => {
      const name = e.proyecto_nombre || "Sin proyecto";
      if (!byProject[name]) byProject[name] = { nombre: name, minutos: 0 };
      const minutos = e.duracion_minutos != null
        ? e.duracion_minutos
        : Math.floor((Date.now() - new Date(e.hora_inicio).getTime()) / 60000);
      byProject[name].minutos += minutos;
    });
    setChartData(Object.values(byProject));
  }, [timeEntries]);

  const handleAssign = async () => {
    if (!selectedProject || assignUserIds.length === 0) return;
    await projectsApi.assignUsers(selectedProject.id, assignUserIds);
    setAssignUserIds([]);
    setSelectedProject(null);
    projectsApi.list().then(setProjects).catch(console.error);
  };

  const handleCreateProject = async (e) => {
    e?.preventDefault();
    await projectsApi.create(newProject);
    setNewProject({ nombre: "", descripcion: "", cliente: "", estado: "ABIERTO" });
    setShowNewProject(false);
    projectsApi.list().then(setProjects).catch(console.error);
  };

  const formatDate = (s) => (s ? new Date(s).toLocaleString("es-CO") : "-");

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Panel de proyectos y horas</h2>

      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-medium text-slate-800">Liquidación</h3>
        <div className="mb-4 flex gap-2">
          <select
            value={settlementPeriod}
            onChange={(e) => setSettlementPeriod(e.target.value)}
            className="rounded border border-slate-300 px-2 py-1"
          >
            <option value="week">Última semana</option>
            <option value="month">Último mes</option>
          </select>
        </div>
        {settlement && (
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <h4 className="text-sm font-medium text-slate-600">Por usuario</h4>
              <ul className="mt-1 text-sm">
                {settlement.por_usuario.map((u) => (
                  <li key={u.usuario_id}>{u.nombre_completo}: {minutesToHHMM(u.total_minutos)}</li>
                ))}
              </ul>
            </div>
            <div>
              <h4 className="text-sm font-medium text-slate-600">Por proyecto</h4>
              <ul className="mt-1 text-sm">
                {settlement.por_proyecto.map((p) => (
                  <li key={p.proyecto_id}>{p.nombre}: {minutesToHHMM(p.total_minutos)}</li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-medium text-slate-800">Horas por proyecto</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <XAxis dataKey="nombre" />
              <YAxis />
              <Tooltip formatter={(v) => [minutesToHHMM(v), "Tiempo"]} />
              <Bar dataKey="minutos" fill="#00639B" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg bg-white p-6 shadow">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-medium text-slate-800">Proyectos</h3>
          <button
            type="button"
            onClick={() => setShowNewProject(!showNewProject)}
            className="rounded bg-slate-600 px-3 py-1 text-sm text-white hover:bg-slate-700"
          >
            {showNewProject ? "Cancelar" : "Nuevo proyecto"}
          </button>
        </div>
        {showNewProject && (
          <form onSubmit={handleCreateProject} className="mb-4 rounded border border-slate-200 bg-slate-50 p-4">
            <div className="grid gap-2 sm:grid-cols-3">
              <input
                type="text"
                placeholder="Nombre"
                value={newProject.nombre}
                onChange={(e) => setNewProject((p) => ({ ...p, nombre: e.target.value }))}
                className="rounded border border-slate-300 px-2 py-1"
                required
              />
              <input
                type="text"
                placeholder="Cliente"
                value={newProject.cliente}
                onChange={(e) => setNewProject((p) => ({ ...p, cliente: e.target.value }))}
                className="rounded border border-slate-300 px-2 py-1"
              />
              <select
                value={newProject.estado}
                onChange={(e) => setNewProject((p) => ({ ...p, estado: e.target.value }))}
                className="rounded border border-slate-300 px-2 py-1"
              >
                <option value="ABIERTO">Abierto</option>
                <option value="CERRADO">Cerrado</option>
              </select>
            </div>
            <textarea
              placeholder="Descripción"
              value={newProject.descripcion}
              onChange={(e) => setNewProject((p) => ({ ...p, descripcion: e.target.value }))}
              className="mt-2 w-full rounded border border-slate-300 px-2 py-1"
              rows={2}
            />
            <button type="submit" className="mt-2 rounded bg-slate-700 px-3 py-1 text-sm text-white hover:bg-slate-800">
              Crear proyecto
            </button>
          </form>
        )}
        <div className="space-y-2">
          {projects.map((p) => (
            <div
              key={p.id}
              className="flex flex-wrap items-center justify-between gap-2 rounded border border-slate-200 p-3"
            >
              <div>
                <span className="font-medium">{p.nombre}</span>
                <span className="ml-2 text-slate-500 text-sm">{p.cliente}</span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => {
                    if (selectedProject?.id === p.id) {
                      setSelectedProject(null);
                      setAssignUserIds([]);
                    } else {
                      setSelectedProject(p);
                      setAssignUserIds(p.usuarios_asignados ?? []);
                    }
                  }}
                  className="rounded bg-slate-600 px-3 py-1 text-sm text-white hover:bg-slate-700"
                >
                  Asignar personal
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {selectedProject && (
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4">Asignar a: {selectedProject.nombre}</h3>
          <div className="flex flex-wrap gap-2">
            {users.map((u) => (
              <label key={u.id} className="flex items-center gap-1 rounded border px-2 py-1">
                <input
                  type="checkbox"
                  checked={assignUserIds.includes(u.id)}
                  onChange={(e) =>
                    setAssignUserIds((prev) =>
                      e.target.checked ? [...prev, u.id] : prev.filter((id) => id !== u.id)
                    )
                  }
                />
                <span className="text-sm">{u.username}</span>
              </label>
            ))}
          </div>
          <button
            type="button"
            onClick={handleAssign}
            className="mt-4 rounded bg-slate-700 px-4 py-2 text-white hover:bg-slate-800"
          >
            Asignar seleccionados
          </button>
        </div>
      )}

      <CuadrillaManager />

      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-medium text-slate-800">Registros de tiempo</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="pb-2 font-medium text-slate-700">Usuario</th>
                <th className="pb-2 font-medium text-slate-700">Proyecto</th>
                <th className="pb-2 font-medium text-slate-700">Inicio</th>
                <th className="pb-2 font-medium text-slate-700">Fin</th>
                <th className="pb-2 font-medium text-slate-700">Duración</th>
              </tr>
            </thead>
            <tbody>
              {timeEntries.slice(0, 50).map((e) => (
                <tr key={e.id} className="border-b border-slate-100">
                  <td className="py-2">{e.usuario_username ?? "-"}</td>
                  <td className="py-2">{e.proyecto_nombre}</td>
                  <td className="py-2">{formatDate(e.hora_inicio)}</td>
                  <td className="py-2">{formatDate(e.hora_fin)}</td>
                  <td className="py-2">{minutesToHHMM(e.duracion_minutos)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
