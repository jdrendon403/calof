import { useState } from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import logo from "../assets/IncontrolLogo.png";
import ChangePasswordModal from "./ChangePasswordModal";
import NotificationBell from "./NotificationBell";

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
      <header className="border-b-4 border-brand-blue bg-white shadow-sm">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <img src={logo} alt="InControl" className="h-12 w-auto" />
          <nav className="flex flex-wrap items-center gap-2 text-sm font-medium sm:gap-4">
            {(user?.rol === "OPERARIO" || user?.rol === "LIDER" || user?.rol === "ADMIN") && (
              <NavLink
                to="/operario"
                className={({ isActive }) =>
                  isActive ? "rounded px-3 py-1.5 bg-slate-700 text-white" : "rounded px-3 py-1.5 text-slate-700 hover:bg-slate-100"
                }
              >
                Tiempos
              </NavLink>
            )}
            <NavLink
              to="/campo"
              className={({ isActive }) =>
                isActive ? "rounded px-3 py-1.5 bg-slate-700 text-white" : "rounded px-3 py-1.5 text-slate-700 hover:bg-slate-100"
              }
            >
              Campo
            </NavLink>
            {(user?.rol === "LIDER" || user?.rol === "ADMIN") && (
              <NavLink
                to="/lider"
                className={({ isActive }) =>
                  isActive ? "rounded px-3 py-1.5 bg-slate-700 text-white" : "rounded px-3 py-1.5 text-slate-700 hover:bg-slate-100"
                }
              >
                Proyectos
              </NavLink>
            )}
            {user?.rol === "ADMIN" && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  isActive ? "rounded px-3 py-1.5 bg-slate-700 text-white" : "rounded px-3 py-1.5 text-slate-700 hover:bg-slate-100"
                }
              >
                Usuarios
              </NavLink>
            )}
            <NotificationBell />
            <span className="px-2 py-1 font-normal text-brand-text">
              {user?.first_name && user?.last_name
                ? `${user.first_name} ${user.last_name}`
                : user?.username}
            </span>
            <button
              type="button"
              onClick={() => setShowChangePassword(true)}
              className="rounded px-2 py-1 text-slate-700 hover:bg-slate-100"
            >
              Cambiar contraseña
            </button>
            <button
              type="button"
              onClick={handleLogout}
              className="rounded bg-slate-700 px-3 py-1.5 text-white hover:bg-slate-500"
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
