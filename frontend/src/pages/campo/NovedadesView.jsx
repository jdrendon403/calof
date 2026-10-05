import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fotos as fotosApi, novedades as api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import PhotoGallery from "../../components/PhotoGallery";
import PhotoPicker, { uploadPending } from "../../components/PhotoPicker";
import StatusBadge from "../../components/StatusBadge";
import { errorMessage, formatDateTime } from "../../utils/format";
import {
  AccionLider, Campo, ItemCard, NotaProyectoEnCurso, Toolbar, Vacio, btnPrimary, btnSecondary, input, label, useEsLider,
  useProyectoPorDefecto, useProyectos,
} from "./common";

export const CATEGORIAS = [
  { value: "SEGURIDAD", label: "Seguridad" },
  { value: "DANO_FALLA", label: "Daño o falla" },
  { value: "RETRASO", label: "Retraso o bloqueo" },
  { value: "PERSONAL", label: "Personal" },
  { value: "OTRA", label: "Otra" },
];

const FILTROS = [
  { value: "ABIERTA", label: "Abiertas" },
  { value: "ATENDIDA", label: "Atendidas" },
  { value: "", label: "Todas" },
];

// datetime-local en hora del navegador
const ahoraLocal = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 16);
};

function NovedadForm({ onDone, onCancel }) {
  const proyectos = useProyectos();
  const [form, setForm] = useState({ proyecto: "", categoria: "OTRA", titulo: "", descripcion: "", fecha_hecho: ahoraLocal() });
  const [fotos, setFotos] = useState([]);
  const [estado, setEstado] = useState("");
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));
  const enCurso = useProyectoPorDefecto(proyectos, form.proyecto, (proyecto) => setForm((f) => ({ ...f, proyecto })));

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setEstado("Guardando...");
    try {
      const nov = await api.create({
        ...form,
        proyecto: form.proyecto || null,
        fecha_hecho: new Date(form.fecha_hecho).toISOString(),
      });
      const fallidas = await uploadPending("novedad", nov.id, fotos, (i, n) => setEstado(`Subiendo foto ${i} de ${n}...`));
      onDone(nov.id, fallidas);
    } catch (err) {
      setError(errorMessage(err));
      setEstado("");
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4 rounded-lg bg-white p-4 shadow sm:p-6">
      <h3 className="text-lg font-medium text-slate-800">Reportar novedad</h3>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className={label}>Categoría</label>
          <select value={form.categoria} onChange={set("categoria")} className={input}>
            {CATEGORIAS.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </select>
        </div>
        <div>
          <label className={label}>Proyecto</label>
          <select value={form.proyecto} onChange={set("proyecto")} className={input}>
            <option value="">Sin proyecto (general)</option>
            {proyectos.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
          </select>
          <NotaProyectoEnCurso enCurso={enCurso} valor={form.proyecto} />
        </div>
      </div>
      <div>
        <label className={label}>¿Qué pasó?</label>
        <input type="text" required maxLength={200} value={form.titulo} onChange={set("titulo")}
          placeholder="Resumen corto, p. ej. «Cable expuesto en el tablero 3»" className={input} />
      </div>
      <div>
        <label className={label}>Detalle</label>
        <textarea rows={4} value={form.descripcion} onChange={set("descripcion")}
          placeholder="Describa lo ocurrido, dónde, a quién afecta..." className={input} />
      </div>
      <div className="sm:w-64">
        <label className={label}>Fecha y hora</label>
        <input type="datetime-local" required value={form.fecha_hecho} onChange={set("fecha_hecho")} className={input} />
      </div>
      <div>
        <label className={label}>Fotos</label>
        <div className="mt-1"><PhotoPicker items={fotos} onChange={setFotos} max={10} disabled={!!estado} /></div>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={!!estado} className={btnPrimary}>{estado || "Enviar novedad"}</button>
        <button type="button" onClick={onCancel} disabled={!!estado} className={btnSecondary}>Cancelar</button>
      </div>
    </form>
  );
}

export default function NovedadesView() {
  const esLider = useEsLider();
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const highlight = Number(params.get("id")) || null;
  const [filtro, setFiltro] = useState(esLider ? "ABIERTA" : "");
  const [lista, setLista] = useState(null);
  const [nuevo, setNuevo] = useState(false);
  const [aviso, setAviso] = useState("");

  const cargar = useCallback(
    () => api.list(filtro && !highlight ? { estado: filtro } : {}).then(setLista).catch(() => setLista([])),
    [filtro, highlight]
  );
  useEffect(() => { cargar(); }, [cargar]);

  const reemplazar = (item) => setLista((l) => l.map((x) => (x.id === item.id ? item : x)));

  if (nuevo) {
    return (
      <NovedadForm
        onCancel={() => setNuevo(false)}
        onDone={(id, fallidas) => {
          setNuevo(false);
          setAviso(fallidas ? `La novedad se guardó, pero ${fallidas} foto(s) no se pudieron subir.` : "Novedad enviada.");
          setParams({ id });
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Toolbar titulo="Novedades" filtro={filtro} setFiltro={(v) => { setParams({}); setFiltro(v); }}
        filtros={FILTROS} accion="+ Reportar novedad" onAccion={() => { setAviso(""); setNuevo(true); }} />
      {aviso && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-800">{aviso}</p>}
      {lista === null && <Vacio>Cargando...</Vacio>}
      {lista?.length === 0 && <Vacio>No hay novedades{filtro ? " en este estado" : ""}.</Vacio>}
      {lista?.map((n) => {
        const propia = n.autor === user?.id;
        return (
          <ItemCard
            key={n.id}
            highlight={n.id === highlight}
            resumen={
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium text-slate-800">{n.titulo}</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {n.categoria_display} · {n.proyecto_nombre || "Sin proyecto"} · {n.autor_nombre} · {formatDateTime(n.fecha_hecho)}
                    {n.fotos.length > 0 && ` · 📷 ${n.fotos.length}`}
                  </p>
                </div>
                <StatusBadge estado={n.estado}>{n.estado_display}</StatusBadge>
              </div>
            }
          >
            <Campo titulo="Detalle">{n.descripcion}</Campo>
            <PhotoGallery
              fotos={n.fotos}
              onDelete={propia && n.estado === "ABIERTA"
                ? async (id) => { await fotosApi.delete(id); reemplazar(await api.get(n.id)); }
                : null}
            />
            {n.estado === "ATENDIDA" && (
              <div className="rounded bg-green-50 p-3">
                <p className="text-xs font-semibold text-green-800">
                  Atendida por {n.atendida_por_nombre} · {formatDateTime(n.atendida_en)}
                </p>
                {n.respuesta && <p className="mt-1 whitespace-pre-line text-sm text-green-900">{n.respuesta}</p>}
              </div>
            )}
            {n.puede_gestionar && n.estado === "ABIERTA" && (
              <AccionLider
                placeholder="Respuesta o acción tomada (opcional)"
                acciones={[{
                  label: "Marcar como atendida",
                  color: "bg-green-600 hover:bg-green-700",
                  onClick: async (respuesta) => reemplazar(await api.accion(n.id, "atender", { respuesta })),
                }]}
              />
            )}
            {propia && n.estado === "ABIERTA" && (
              <button type="button" className="text-sm text-red-600 hover:underline"
                onClick={async () => {
                  if (!window.confirm("¿Eliminar esta novedad?")) return;
                  await api.delete(n.id);
                  setLista((l) => l.filter((x) => x.id !== n.id));
                }}>
                Eliminar novedad
              </button>
            )}
          </ItemCard>
        );
      })}
    </div>
  );
}
