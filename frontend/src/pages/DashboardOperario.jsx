import { useState, useEffect, useRef } from "react";
import { useTime } from "../context/TimeContext";
import { projects as projectsApi, time as timeApi, cuadrillas as cuadrillasApi } from "../api/client";
import { minutesToHHMM } from "../utils/time";

export default function DashboardOperario() {
  const { activeEntry, elapsedSeconds, formatElapsed, start, stop, loading, refresh } = useTime();
  const [projectList, setProjectList] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [timeEntries, setTimeEntries] = useState([]);

  // Modo cuadrilla
  const [myCuadrillas, setMyCuadrillas] = useState([]);
  const [selectedCuadrillaId, setSelectedCuadrillaId] = useState("");
  const [cuadrillaStatus, setCuadrillaStatus] = useState(null);
  const [cuadrillaLoading, setCuadrillaLoading] = useState(false);
  const [skippedWarning, setSkippedWarning] = useState(0);
  const cuadrillaIntervalRef = useRef(null);

  useEffect(() => {
    projectsApi.list().then(setProjectList).catch(console.error);
    cuadrillasApi.list().then(setMyCuadrillas).catch(console.error);
    refresh();
  }, []);

  useEffect(() => {
    timeApi.list().then(setTimeEntries).catch(console.error);
  }, [activeEntry]);

  const handleStart = async () => {
    if (!selectedProjectId) return;
    await start(Number(selectedProjectId));
    timeApi.list().then(setTimeEntries).catch(console.error);
  };

  const handleStop = async () => {
    await stop();
    timeApi.list().then(setTimeEntries).catch(console.error);
  };

  // Cuadrilla handlers
  const fetchCuadrillaStatus = async (id) => {
    if (!id) return;
    try {
      const status = await cuadrillasApi.current(id);
      setCuadrillaStatus(status);
    } catch { setCuadrillaStatus(null); }
  };

  const handleSelectCuadrilla = (id) => {
    setSelectedCuadrillaId(id);
    setSkippedWarning(0);
    setCuadrillaStatus(null);
    if (cuadrillaIntervalRef.current) clearInterval(cuadrillaIntervalRef.current);
    if (id) {
      fetchCuadrillaStatus(id);
      cuadrillaIntervalRef.current = setInterval(() => fetchCuadrillaStatus(id), 30000);
    }
  };

  useEffect(() => () => { if (cuadrillaIntervalRef.current) clearInterval(cuadrillaIntervalRef.current); }, []);

  const handleCuadrillaStart = async () => {
    if (!selectedCuadrillaId) return;
    setCuadrillaLoading(true);
    try {
      const res = await cuadrillasApi.start(selectedCuadrillaId);
      setSkippedWarning(res.skipped_user_ids?.length || 0);
      await fetchCuadrillaStatus(selectedCuadrillaId);
      timeApi.list().then(setTimeEntries).catch(console.error);
    } finally { setCuadrillaLoading(false); }
  };

  const handleCuadrillaStop = async () => {
    if (!selectedCuadrillaId) return;
    setCuadrillaLoading(true);
    try {
      await cuadrillasApi.stop(selectedCuadrillaId);
      setSkippedWarning(0);
      await fetchCuadrillaStatus(selectedCuadrillaId);
      timeApi.list().then(setTimeEntries).catch(console.error);
    } finally { setCuadrillaLoading(false); }
  };

  const formatDate = (s) => (s ? new Date(s).toLocaleString("es-CO") : "-");

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Registro de tiempos</h2>

      <div className="rounded-lg bg-white p-6 shadow">
        <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700">Proyecto</label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              disabled={!!activeEntry}
              className="mt-1 w-full rounded border border-slate-300 px-3 py-2 disabled:bg-slate-100"
            >
              <option value="">Seleccione un proyecto</option>
              {projectList.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.nombre}
                </option>
              ))}
            </select>
          </div>
          <div className="flex gap-2">
            {!activeEntry ? (
              <button
                type="button"
                onClick={handleStart}
                disabled={loading || !selectedProjectId}
                className="rounded bg-green-600 px-6 py-2 font-medium text-white hover:bg-green-700 disabled:opacity-50"
              >
                Iniciar
              </button>
            ) : (
              <button
                type="button"
                onClick={handleStop}
                disabled={loading}
                className="rounded bg-red-600 px-6 py-2 font-medium text-white hover:bg-red-700 disabled:opacity-50"
              >
                Detener
              </button>
            )}
          </div>
        </div>

        {activeEntry && (
          <div className="rounded bg-slate-100 p-4 text-center">
            <p className="text-slate-600">Proyecto: <strong>{activeEntry.proyecto_nombre}</strong></p>
            <p className="mt-2 text-3xl font-mono font-semibold text-slate-800">
              {formatElapsed(elapsedSeconds)}
            </p>
          </div>
        )}
      </div>

      {myCuadrillas.length > 0 && (
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4 text-lg font-medium text-slate-800">Modo cuadrilla</h3>
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-1">Cuadrilla</label>
            <select
              value={selectedCuadrillaId}
              onChange={(e) => handleSelectCuadrilla(e.target.value)}
              className="w-full rounded border border-slate-300 px-3 py-2 sm:w-64"
            >
              <option value="">Seleccione una cuadrilla</option>
              {myCuadrillas.map((c) => (
                <option key={c.id} value={c.id}>{c.nombre} — {c.proyecto_nombre}</option>
              ))}
            </select>
          </div>

          {selectedCuadrillaId && cuadrillaStatus && (
            <div>
              {skippedWarning > 0 && (
                <p className="mb-3 rounded bg-yellow-50 border border-yellow-200 px-3 py-2 text-sm text-yellow-800">
                  {skippedWarning} miembro(s) omitidos porque ya tenían una actividad individual activa.
                </p>
              )}
              {cuadrillaStatus.active ? (
                <div className="space-y-3">
                  <div className="rounded bg-green-50 border border-green-200 px-4 py-3">
                    <p className="text-sm text-green-800 font-medium">Cuadrilla activa</p>
                    <p className="text-sm text-green-700">{cuadrillaStatus.entries.length} miembro(s) trabajando</p>
                  </div>
                  <button
                    type="button"
                    onClick={handleCuadrillaStop}
                    disabled={cuadrillaLoading}
                    className="rounded bg-red-600 px-6 py-2 font-medium text-white hover:bg-red-700 disabled:opacity-50"
                  >
                    Detener cuadrilla
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={handleCuadrillaStart}
                  disabled={cuadrillaLoading}
                  className="rounded bg-green-600 px-6 py-2 font-medium text-white hover:bg-green-700 disabled:opacity-50"
                >
                  Iniciar cuadrilla
                </button>
              )}
            </div>
          )}
        </div>
      )}

      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-medium text-slate-800">Mis registros</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="pb-2 font-medium text-slate-700">Proyecto</th>
                <th className="pb-2 font-medium text-slate-700">Inicio</th>
                <th className="pb-2 font-medium text-slate-700">Fin</th>
                <th className="pb-2 font-medium text-slate-700">Duración</th>
                <th className="pb-2 font-medium text-slate-700">Cierre auto</th>
              </tr>
            </thead>
            <tbody>
              {timeEntries.map((e) => (
                <tr key={e.id} className="border-b border-slate-100">
                  <td className="py-2">{e.proyecto_nombre}</td>
                  <td className="py-2">{formatDate(e.hora_inicio)}</td>
                  <td className="py-2">{formatDate(e.hora_fin)}</td>
                  <td className="py-2">{minutesToHHMM(e.duracion_minutos)}</td>
                  <td className="py-2">{e.cierre_automatico ? "Sí" : "No"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
