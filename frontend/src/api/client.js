import axios from "axios";

const API_BASE = "/api";

const client = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

client.interceptors.response.use(
  (r) => r,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem("refresh");
      if (refresh) {
        try {
          const { data } = await axios.post(API_BASE + "/auth/refresh/", { refresh });
          localStorage.setItem("access", data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return client(original);
        } catch (_) {
          localStorage.removeItem("access");
          localStorage.removeItem("refresh");
          window.location.href = "/login";
        }
      }
    }
    return Promise.reject(err);
  }
);

export default client;

export const auth = {
  login: (username, password) =>
    client.post("/auth/login/", { username, password }).then((r) => r.data),
  me: () => client.get("/auth/me/").then((r) => r.data),
  changePassword: (currentPassword, newPassword) =>
    client.post("/auth/change-password/", {
      current_password: currentPassword,
      new_password: newPassword,
    }),
};

export const projects = {
  list: () => client.get("/projects/").then((r) => r.data),
  get: (id) => client.get(`/projects/${id}/`).then((r) => r.data),
  create: (data) => client.post("/projects/", data).then((r) => r.data),
  update: (id, data) => client.patch(`/projects/${id}/`, data).then((r) => r.data),
  assignUsers: (id, userIds) =>
    client.post(`/projects/${id}/assign-users/`, { user_ids: userIds }).then((r) => r.data),
  unassignUser: (id, userId) =>
    client.post(`/projects/${id}/unassign-user/`, { user_id: userId }).then((r) => r.data),
};

export const time = {
  start: (projectId) => client.post("/time/start/", { project_id: projectId }).then((r) => r.data),
  stop: () => client.patch("/time/stop/").then((r) => r.data),
  current: () => client.get("/time/current/").then((r) => r.data),
  list: () => client.get("/time/").then((r) => r.data),
};

export const users = {
  list: () => client.get("/users/").then((r) => r.data),
  get: (id) => client.get(`/users/${id}/`).then((r) => r.data),
  create: (data) => client.post("/users/", data).then((r) => r.data),
  update: (id, data) => client.patch(`/users/${id}/`, data).then((r) => r.data),
  delete: (id) => client.delete(`/users/${id}/`).then((r) => r.data),
};

export const reports = {
  settlement: (period = "month") =>
    client.get("/reports/settlement/", { params: { period } }).then((r) => r.data),
};

export const cuadrillas = {
  list:         ()             => client.get("/cuadrillas/").then((r) => r.data),
  get:          (id)           => client.get(`/cuadrillas/${id}/`).then((r) => r.data),
  create:       (data)         => client.post("/cuadrillas/", data).then((r) => r.data),
  update:       (id, data)     => client.patch(`/cuadrillas/${id}/`, data).then((r) => r.data),
  addMembers:   (id, userIds)  => client.post(`/cuadrillas/${id}/add-members/`, { user_ids: userIds }).then((r) => r.data),
  removeMember: (id, userId)   => client.post(`/cuadrillas/${id}/remove-member/`, { user_id: userId }).then((r) => r.data),
  start:        (id)           => client.post(`/cuadrillas/${id}/start/`).then((r) => r.data),
  stop:         (id)           => client.post(`/cuadrillas/${id}/stop/`).then((r) => r.data),
  current:      (id)           => client.get(`/cuadrillas/${id}/current/`).then((r) => r.data),
};

// ── Campo: novedades, insumos, informes, fotos y avisos ──────────────────────
const multipart = { headers: { "Content-Type": "multipart/form-data" } };

function recurso(base) {
  return {
    list:   (params)   => client.get(`/${base}/`, { params }).then((r) => r.data),
    get:    (id)       => client.get(`/${base}/${id}/`).then((r) => r.data),
    create: (data)     => client.post(`/${base}/`, data).then((r) => r.data),
    update: (id, data) => client.patch(`/${base}/${id}/`, data).then((r) => r.data),
    delete: (id)       => client.delete(`/${base}/${id}/`),
    accion: (id, nombre, data = {}) => client.post(`/${base}/${id}/${nombre}/`, data).then((r) => r.data),
  };
}

export const campo = {
  proyectos: () => client.get("/campo/proyectos/").then((r) => r.data),
};
export const novedades = recurso("novedades");
export const insumos = recurso("insumos");
export const informes = {
  ...recurso("informes"),
  sugerirPersonal: (proyecto, fecha) =>
    client.get("/informes/sugerir-personal/", { params: { proyecto, fecha } }).then((r) => r.data),
  guardarFirma: (id, blob) => {
    const fd = new FormData();
    fd.append("imagen", blob, "firma.png");
    return client.post(`/informes/${id}/firma/`, fd, multipart).then((r) => r.data);
  },
  borrarFirma: (id) => client.delete(`/informes/${id}/firma/`).then((r) => r.data),
};
export const fotos = {
  // tipo: "novedad" | "solicitud" | "informe"
  upload: (tipo, padreId, blob, descripcion = "") => {
    const fd = new FormData();
    fd.append(tipo, padreId);
    fd.append("archivo", blob, "foto.jpg");
    fd.append("descripcion", descripcion);
    return client.post("/fotos/", fd, multipart).then((r) => r.data);
  },
  delete: (id) => client.delete(`/fotos/${id}/`),
};
export const notificaciones = {
  list:        ()    => client.get("/notificaciones/").then((r) => r.data),
  noLeidas:    ()    => client.get("/notificaciones/no-leidas/").then((r) => r.data.total),
  marcarLeidas: (ids) => client.post("/notificaciones/marcar-leidas/", ids ? { ids } : {}).then((r) => r.data),
};
