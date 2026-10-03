import { useState, useEffect } from "react";
import { users as usersApi } from "../api/client";

const ROLES = [
  { value: "ADMIN", label: "Administrador" },
  { value: "LIDER", label: "Líder" },
  { value: "OPERARIO", label: "Operario" },
];

export default function AdminPanel() {
  const [users, setUsers] = useState([]);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ username: "", email: "", first_name: "", last_name: "", rol: "OPERARIO", telefono: "", password: "" });
  const [error, setError] = useState("");

  useEffect(() => {
    usersApi.list().then(setUsers).catch(console.error);
  }, []);

  const handleCreate = () => {
    setEditing("new");
    setForm({ username: "", email: "", first_name: "", last_name: "", rol: "OPERARIO", telefono: "", password: "" });
    setError("");
  };

  const handleEdit = (u) => {
    setEditing(u.id);
    setForm({
      username: u.username,
      email: u.email || "",
      first_name: u.first_name || "",
      last_name: u.last_name || "",
      rol: u.rol || "OPERARIO",
      telefono: u.telefono || "",
      password: "",
    });
    setError("");
  };

  const handleSave = async () => {
    setError("");
    try {
      if (editing === "new") {
        if (!form.password) {
          setError("La contraseña es obligatoria para nuevo usuario.");
          return;
        }
        await usersApi.create({
          username: form.username,
          email: form.email,
          password: form.password,
          first_name: form.first_name,
          last_name: form.last_name,
          rol: form.rol,
          telefono: form.telefono,
        });
      } else {
        const payload = {
          email: form.email,
          first_name: form.first_name,
          last_name: form.last_name,
          rol: form.rol,
          telefono: form.telefono,
        };
        if (form.password) payload.password = form.password;
        await usersApi.update(editing, payload);
      }
      setEditing(null);
      usersApi.list().then(setUsers).catch(console.error);
    } catch (err) {
      const data = err.response?.data;
      setError(data?.username?.[0] || data?.password?.[0] || data?.detail || "Error al guardar.");
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("¿Eliminar este usuario?")) return;
    try {
      await usersApi.delete(id);
      usersApi.list().then(setUsers).catch(console.error);
      if (editing === id) setEditing(null);
    } catch (err) {
      setError(err.response?.data?.detail || "Error al eliminar.");
    }
  };

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold text-slate-800">Administración de usuarios</h2>

      {editing && (
        <div className="rounded-lg bg-white p-6 shadow">
          <h3 className="mb-4">{editing === "new" ? "Nuevo usuario" : "Editar usuario"}</h3>
          {error && <p className="mb-2 text-sm text-red-600">{error}</p>}
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label className="block text-sm font-medium text-slate-700">Usuario</label>
              <input
                type="text"
                value={form.username}
                onChange={(e) => setForm((f) => ({ ...f, username: e.target.value }))}
                disabled={editing !== "new"}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2 disabled:bg-slate-100"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Correo</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Nombre</label>
              <input
                type="text"
                value={form.first_name}
                onChange={(e) => setForm((f) => ({ ...f, first_name: e.target.value }))}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Apellido</label>
              <input
                type="text"
                value={form.last_name}
                onChange={(e) => setForm((f) => ({ ...f, last_name: e.target.value }))}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Rol</label>
              <select
                value={form.rol}
                onChange={(e) => setForm((f) => ({ ...f, rol: e.target.value }))}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              >
                {ROLES.map((r) => (
                  <option key={r.value} value={r.value}>{r.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Teléfono</label>
              <input
                type="text"
                value={form.telefono}
                onChange={(e) => setForm((f) => ({ ...f, telefono: e.target.value }))}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">
                Contraseña {editing !== "new" && "(dejar en blanco para no cambiar)"}
              </label>
              <input
                type="password"
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
              />
            </div>
          </div>
          <div className="mt-4 flex gap-2">
            <button
              type="button"
              onClick={handleSave}
              className="rounded bg-slate-700 px-4 py-2 text-white hover:bg-slate-800"
            >
              Guardar
            </button>
            <button
              type="button"
              onClick={() => setEditing(null)}
              className="rounded border border-slate-300 px-4 py-2 hover:bg-slate-100"
            >
              Cancelar
            </button>
          </div>
        </div>
      )}

      <div className="rounded-lg bg-white p-6 shadow">
        <div className="mb-4 flex justify-between">
          <h3 className="text-lg font-medium text-slate-800">Usuarios</h3>
          {!editing && (
            <button
              type="button"
              onClick={handleCreate}
              className="rounded bg-slate-700 px-4 py-2 text-sm text-white hover:bg-slate-800"
            >
              Nuevo usuario
            </button>
          )}
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-200">
                <th className="pb-2 font-medium text-slate-700">Usuario</th>
                <th className="pb-2 font-medium text-slate-700">Nombre</th>
                <th className="pb-2 font-medium text-slate-700">Rol</th>
                <th className="pb-2 font-medium text-slate-700">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="border-b border-slate-100">
                  <td className="py-2">{u.username}</td>
                  <td className="py-2">{u.first_name} {u.last_name}</td>
                  <td className="py-2">{u.rol}</td>
                  <td className="py-2">
                    <button
                      type="button"
                      onClick={() => handleEdit(u)}
                      className="text-slate-600 hover:underline"
                    >
                      Editar
                    </button>
                    {" | "}
                    <button
                      type="button"
                      onClick={() => handleDelete(u.id)}
                      className="text-red-600 hover:underline"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
