import { useState } from "react";
import { auth } from "../api/client";

export default function ChangePasswordModal({ onClose }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("La contraseña nueva y la confirmación no coinciden.");
      return;
    }
    setLoading(true);
    try {
      await auth.changePassword(currentPassword, newPassword);
      setSuccess(true);
    } catch (err) {
      const data = err.response?.data;
      setError(
        data?.current_password?.[0] || data?.new_password?.[0] || data?.detail || "Error al cambiar la contraseña."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 text-slate-800 shadow-md">
        <h3 className="mb-4 text-lg font-semibold">Cambiar contraseña</h3>
        {success ? (
          <div className="space-y-4">
            <p className="text-sm text-green-700">Contraseña actualizada correctamente.</p>
            <button
              type="button"
              onClick={onClose}
              className="w-full rounded bg-slate-800 py-2 font-medium text-white hover:bg-slate-700"
            >
              Cerrar
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700">Contraseña actual</label>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                required
                autoComplete="current-password"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Contraseña nueva</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                required
                minLength={4}
                autoComplete="new-password"
              />
              <p className="mt-1 text-xs text-slate-500">Mínimo 4 caracteres.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Confirmar contraseña nueva</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="mt-1 w-full rounded border border-slate-300 px-3 py-2"
                required
                autoComplete="new-password"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <div className="flex gap-2">
              <button
                type="submit"
                disabled={loading}
                className="flex-1 rounded bg-slate-800 py-2 font-medium text-white hover:bg-slate-700 disabled:opacity-50"
              >
                {loading ? "Guardando..." : "Guardar"}
              </button>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 rounded border border-slate-300 py-2 hover:bg-slate-100"
              >
                Cancelar
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
