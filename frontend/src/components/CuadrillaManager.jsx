import { useState, useEffect } from "react";
import { cuadrillas as cuadrillasApi, projects as projectsApi, users as usersApi } from "../api/client";

export default function CuadrillaManager() {
  const [cuadrillasList, setCuadrillasList] = useState([]);
  const [projects, setProjects] = useState([]);
  const [users, setUsers] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [newCuadrilla, setNewCuadrilla] = useState({ nombre: "", proyecto: "", miembro_ids: [] });
  const [selectedCuadrilla, setSelectedCuadrilla] = useState(null);
  const [memberIds, setMemberIds] = useState([]);

  const fetchCuadrillas = () => cuadrillasApi.list().then(setCuadrillasList).catch(console.error);

  useEffect(() => {
    fetchCuadrillas();
    projectsApi.list().then(setProjects).catch(console.error);
    usersApi.list().then(setUsers).catch(console.error);
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    await cuadrillasApi.create({
      nombre: newCuadrilla.nombre,
      proyecto: Number(newCuadrilla.proyecto),
      miembro_ids: newCuadrilla.miembro_ids,
    });
    setNewCuadrilla({ nombre: "", proyecto: "", miembro_ids: [] });
    setShowCreate(false);
    fetchCuadrillas();
  };

  const openMemberPanel = (c) => {
    setSelectedCuadrilla(c);
    setMemberIds(c.miembros.map((m) => m.id));
  };

  const handleSaveMembers = async () => {
    const current = selectedCuadrilla.miembros.map((m) => m.id);
    const toAdd = memberIds.filter((id) => !current.includes(id));
    const toRemove = current.filter((id) => !memberIds.includes(id));
    if (toAdd.length) await cuadrillasApi.addMembers(selectedCuadrilla.id, toAdd);
    for (const id of toRemove) await cuadrillasApi.removeMember(selectedCuadrilla.id, id);
    setSelectedCuadrilla(null);
    fetchCuadrillas();
  };

  const handleToggleActive = async (c) => {
    await cuadrillasApi.update(c.id, { activa: !c.activa });
    fetchCuadrillas();
  };

  const toggleNewMember = (id) =>
    setNewCuadrilla((prev) => ({
      ...prev,
      miembro_ids: prev.miembro_ids.includes(id)
        ? prev.miembro_ids.filter((x) => x !== id)
        : [...prev.miembro_ids, id],
    }));

  const toggleMember = (id) =>
    setMemberIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );

  return (
    <div className="rounded-lg bg-white p-6 shadow">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-medium text-slate-800">Cuadrillas</h3>
        <button
          type="button"
          onClick={() => setShowCreate(!showCreate)}
          className="rounded bg-slate-600 px-3 py-1 text-sm text-white hover:bg-slate-700"
        >
          {showCreate ? "Cancelar" : "Nueva cuadrilla"}
        </button>
      </div>

      {showCreate && (
        <form onSubmit={handleCreate} className="mb-4 rounded border border-slate-200 bg-slate-50 p-4 space-y-3">
          <div className="grid gap-2 sm:grid-cols-2">
            <input
              type="text"
              placeholder="Nombre de la cuadrilla"
              value={newCuadrilla.nombre}
              onChange={(e) => setNewCuadrilla((p) => ({ ...p, nombre: e.target.value }))}
              className="rounded border border-slate-300 px-2 py-1"
              required
            />
            <select
              value={newCuadrilla.proyecto}
              onChange={(e) => setNewCuadrilla((p) => ({ ...p, proyecto: e.target.value }))}
              className="rounded border border-slate-300 px-2 py-1"
              required
            >
              <option value="">Seleccione proyecto</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.nombre}</option>
              ))}
            </select>
          </div>
          <div>
            <p className="text-sm font-medium text-slate-700 mb-1">Miembros</p>
            <div className="flex flex-wrap gap-2">
              {users.map((u) => (
                <label key={u.id} className="flex items-center gap-1 rounded border px-2 py-1 text-sm cursor-pointer">
                  <input
                    type="checkbox"
                    checked={newCuadrilla.miembro_ids.includes(u.id)}
                    onChange={() => toggleNewMember(u.id)}
                  />
                  {u.first_name && u.last_name ? `${u.first_name} ${u.last_name}` : u.username}
                </label>
              ))}
            </div>
          </div>
          <button type="submit" className="rounded bg-slate-700 px-3 py-1 text-sm text-white hover:bg-slate-800">
            Crear cuadrilla
          </button>
        </form>
      )}

      <div className="space-y-2">
        {cuadrillasList.length === 0 && (
          <p className="text-sm text-slate-500">No hay cuadrillas registradas.</p>
        )}
        {cuadrillasList.map((c) => (
          <div key={c.id} className="rounded border border-slate-200 p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div>
                <span className="font-medium">{c.nombre}</span>
                <span className="ml-2 text-sm text-slate-500">{c.proyecto_nombre}</span>
                <span className={`ml-2 rounded px-1.5 py-0.5 text-xs font-medium ${c.activa ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
                  {c.activa ? "Activa" : "Inactiva"}
                </span>
                <span className="ml-2 text-xs text-slate-400">{c.miembros.length} miembro(s)</span>
              </div>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => selectedCuadrilla?.id === c.id ? setSelectedCuadrilla(null) : openMemberPanel(c)}
                  className="rounded bg-slate-600 px-2 py-1 text-xs text-white hover:bg-slate-700"
                >
                  Miembros
                </button>
                <button
                  type="button"
                  onClick={() => handleToggleActive(c)}
                  className="rounded bg-slate-200 px-2 py-1 text-xs text-slate-700 hover:bg-slate-300"
                >
                  {c.activa ? "Desactivar" : "Activar"}
                </button>
              </div>
            </div>

            {selectedCuadrilla?.id === c.id && (
              <div className="mt-3 border-t border-slate-100 pt-3">
                <p className="text-sm font-medium text-slate-700 mb-2">Gestionar miembros</p>
                <div className="flex flex-wrap gap-2 mb-3">
                  {users.map((u) => (
                    <label key={u.id} className="flex items-center gap-1 rounded border px-2 py-1 text-sm cursor-pointer">
                      <input
                        type="checkbox"
                        checked={memberIds.includes(u.id)}
                        onChange={() => toggleMember(u.id)}
                      />
                      {u.first_name && u.last_name ? `${u.first_name} ${u.last_name}` : u.username}
                    </label>
                  ))}
                </div>
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={handleSaveMembers}
                    className="rounded bg-slate-700 px-3 py-1 text-sm text-white hover:bg-slate-800"
                  >
                    Guardar
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedCuadrilla(null)}
                    className="rounded bg-slate-200 px-3 py-1 text-sm text-slate-700 hover:bg-slate-300"
                  >
                    Cancelar
                  </button>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
