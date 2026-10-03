import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/IncontrolLogo.png";
import ChangePasswordModal from "./ChangePasswordModal";

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [showChangePassword, setShowChangePassword] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-slate-800 text-white shadow">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <img src={logo} alt="InControl" className="h-10 w-auto" />
          <nav className="flex gap-4">
            {(user?.rol === "OPERARIO" || user?.rol === "LIDER" || user?.rol === "ADMIN") && (
              <NavLink
                to="/operario"
                className={({ isActive }) =>
                  isActive ? "rounded px-2 py-1 bg-slate-600" : "rounded px-2 py-1 hover:bg-slate-700"
                }
              >
                Tiempos
              </NavLink>
            )}
            {(user?.rol === "LIDER" || user?.rol === "ADMIN") && (
              <NavLink
                to="/lider"
                className={({ isActive }) =>
                  isActive ? "rounded px-2 py-1 bg-slate-600" : "rounded px-2 py-1 hover:bg-slate-700"
                }
              >
                Proyectos
              </NavLink>
            )}
            {user?.rol === "ADMIN" && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  isActive ? "rounded px-2 py-1 bg-slate-600" : "rounded px-2 py-1 hover:bg-slate-700"
                }
              >
                Usuarios
              </NavLink>
            )}
            <span className="px-2 py-1 text-slate-300 text-sm">
              {user?.first_name && user?.last_name
                ? `${user.first_name} ${user.last_name}`
                : user?.username}
            </span>
            <button
              type="button"
              onClick={() => setShowChangePassword(true)}
              className="rounded px-2 py-1 text-sm hover:bg-slate-700"
            >
              Cambiar contraseña
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded bg-slate-600 px-3 py-1 text-sm hover:bg-slate-500"
            >
              Salir
            </button>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
      {showChangePassword && <ChangePasswordModal onClose={() => setShowChangePassword(false)} />}
    </div>
  );
}
