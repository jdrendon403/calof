import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import LoginView from "./pages/LoginView";
import DashboardOperario from "./pages/DashboardOperario";
import DashboardLider from "./pages/DashboardLider";
import AdminPanel from "./pages/AdminPanel";
import Layout from "./components/Layout";

function PrivateRoute({ children, allowedRoles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-center">Cargando...</div>;
  if (!user) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(user.rol))
    return <Navigate to="/" replace />;
  return children;
}

function RoleRedirect() {
  const { user } = useAuth();
  if (user?.rol === "ADMIN") return <Navigate to="/admin" replace />;
  if (user?.rol === "LIDER") return <Navigate to="/lider" replace />;
  return <Navigate to="/operario" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginView />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <Layout />
          </PrivateRoute>
        }
      >
        <Route index element={<RoleRedirect />} />
        <Route
          path="operario"
          element={
            <PrivateRoute allowedRoles={["OPERARIO", "LIDER", "ADMIN"]}>
              <DashboardOperario />
            </PrivateRoute>
          }
        />
        <Route
          path="lider"
          element={
            <PrivateRoute allowedRoles={["LIDER", "ADMIN"]}>
              <DashboardLider />
            </PrivateRoute>
          }
        />
        <Route
          path="admin"
          element={
            <PrivateRoute allowedRoles={["ADMIN"]}>
              <AdminPanel />
            </PrivateRoute>
          }
        />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
