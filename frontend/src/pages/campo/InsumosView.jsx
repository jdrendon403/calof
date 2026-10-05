import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { fotos as fotosApi, insumos as api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import PhotoGallery from "../../components/PhotoGallery";
import PhotoPicker, { uploadPending } from "../../components/PhotoPicker";
import StatusBadge from "../../components/StatusBadge";
import { errorMessage, formatDate, formatDateTime } from "../../utils/format";
import {
  AccionLider, Campo, ItemCard, Toolbar, Vacio, btnPrimary, btnSecondary, input, label, useEsLider, useProyectos,
} from "./common";

const FILTROS = [
  { value: "PENDIENTE,APROBADA", label: "Por resolver" },
  { value: "PENDIENTE", label: "Pendientes" },
  { value: "APROBADA", label: "Aprobadas (por entregar)" },
  { value: "ENTREGADA,RECHAZADA", label: "Cerradas" },
  { value: "", label: "Todas" },
];

function SolicitudForm({ onDone, onCancel }) {
  const proyectos = useProyectos();
  const [form, setForm] = useState({ proyecto: "", detalle: "", fecha_requerida: "" });
  const [fotos, setFotos] = useState([]);
  const [estado, setEstado] = useState("");
  const [error, setError] = useState("");
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  useEffect(() => {
    if (proyectos.length === 1) setForm((f) => ({ ...f, proyecto: String(proyectos[0].id) }));
  }, [proyectos]);

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    setEstado("Enviando...");
    try {
      const sol = await api.create({ ...form, fecha_requerida: form.fecha_requerida || null });
      const fallidas = await uploadPending("solicitud", sol.id, fotos, (i, n) => setEstado(`Subiendo foto ${i} de ${n}...`));
      onDone(sol.id, fallidas);
    } catch (err) {
      setError(errorMessage(err));
      setEstado("");
    }
  };

  return (
    <form onSubmit={submit} className="space-y-4 rounded-lg bg-white p-4 shadow sm:p-6">
      <h3 className="text-lg font-medium text-slate-800">Pedir insumos</h3>
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className={label}>Proyecto</label>
          <select required value={form.proyecto} onChange={set("proyecto")} className={input}>
            <option value="">Seleccione un proyecto</option>
            {proyectos.map((p) => <option key={p.id} value={p.id}>{p.nombre}</option>)}
          </select>
        </div>
        <div>
          <label className={label}>¿Para cuándo? (opcional)</label>
          <input type="date" value={form.fecha_requerida} onChange={set("fecha_requerida")} className={input} />
        </div>
      </div>
      <div>
        <label className={label}>¿Qué necesita?</label>
        <textarea required rows={5} value={form.detalle} onChange={set("detalle")}
          placeholder={"Un insumo por línea, con la cantidad. Por ejemplo:\n20 m de cable 12 AWG\n2 cajas de guantes talla L"}
          className={input} />
      </div>
      <div>
        <label className={label}>Fotos (opcional, p. ej. de la referencia o la pieza dañada)</label>
        <div className="mt-1"><PhotoPicker items={fotos} onChange={setFotos} max={10} disabled={!!estado} /></div>
      </div>
      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex gap-2">
        <button type="submit" disabled={!!estado} className={btnPrimary}>{estado || "Enviar solicitud"}</button>
        <button type="button" onClick={onCancel} disabled={!!estado} className={btnSecondary}>Cancelar</button>
      </div>
    </form>
  );
}

export default function InsumosView() {
  const esLider = useEsLider();
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const highlight = Number(params.get("id")) || null;
  const [filtro, setFiltro] = useState(esLider ? "PENDIENTE,APROBADA" : "");
  const [lista, setLista] = useState(null);
  const [nuevo, setNuevo] = useState(false);
  const [aviso, setAviso] = useState("");

  const cargar = useCallback(
    () => api.list(filtro && !highlight ? { estado: filtro } : {}).then(setLista).catch(() => setLista([])),
    [filtro, highlight]
  );
  useEffect(() => { cargar(); }, [cargar]);

  const reemplazar = (item) => setLista((l) => l.map((x) => (x.id === item.id ? item : x)));
  const accion = (id, nombre) => async (comentario) => reemplazar(await api.accion(id, nombre, { comentario }));

  if (nuevo) {
    return (
      <SolicitudForm
        onCancel={() => setNuevo(false)}
        onDone={(id, fallidas) => {
          setNuevo(false);
          setAviso(fallidas ? `La solicitud se guardó, pero ${fallidas} foto(s) no se pudieron subir.` : "Solicitud enviada.");
          setParams({ id });
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Toolbar titulo="Pedidos de insumos" filtro={filtro} setFiltro={(v) => { setParams({}); setFiltro(v); }}
        filtros={FILTROS} accion="+ Pedir insumos" onAccion={() => { setAviso(""); setNuevo(true); }} />
      {aviso && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-800">{aviso}</p>}
      {lista === null && <Vacio>Cargando...</Vacio>}
      {lista?.length === 0 && <Vacio>No hay solicitudes{filtro ? " en este estado" : ""}.</Vacio>}
      {lista?.map((s) => {
        const propia = s.autor === user?.id;
        const primeraLinea = s.detalle.split("\n")[0];
        return (
          <ItemCard
            key={s.id}
            highlight={s.id === highlight}
            resumen={
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate font-medium text-slate-800">{primeraLinea}</p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {s.proyecto_nombre} · {s.autor_nombre} · {formatDateTime(s.creada_en)}
                    {s.fecha_requerida && ` · Para el ${formatDate(s.fecha_requerida)}`}
                  </p>
                </div>
                <StatusBadge estado={s.estado}>{s.estado_display}</StatusBadge>
              </div>
            }
          >
            <Campo titulo="Insumos solicitados">{s.detalle}</Campo>
            <PhotoGallery
              fotos={s.fotos}
              onDelete={propia && s.estado === "PENDIENTE"
                ? async (id) => { await fotosApi.delete(id); reemplazar(await api.get(s.id)); }
                : null}
            />
            {s.gestionada_por_nombre && (
              <p className="text-xs text-slate-500">
                {s.estado === "RECHAZADA" ? "Rechazada" : "Aprobada"} por {s.gestionada_por_nombre} · {formatDateTime(s.gestionada_en)}
                {s.entregada_en && ` · Entregada el ${formatDateTime(s.entregada_en)}`}
              </p>
            )}
            <Campo titulo="Comentario">{s.comentario}</Campo>
            {s.puede_gestionar && s.estado === "PENDIENTE" && (
              <AccionLider
                placeholder="Comentario (obligatorio si rechaza)"
                acciones={[
                  { label: "Aprobar", color: "bg-green-600 hover:bg-green-700", onClick: accion(s.id, "aprobar") },
                  { label: "Rechazar", color: "bg-red-600 hover:bg-red-700", requiereComentario: true, onClick: accion(s.id, "rechazar") },
                ]}
              />
            )}
            {s.puede_gestionar && s.estado === "APROBADA" && (
              <AccionLider
                placeholder="Comentario de entrega (opcional)"
                acciones={[{ label: "Marcar como entregada", color: "bg-green-600 hover:bg-green-700", onClick: accion(s.id, "entregar") }]}
              />
            )}
            {propia && s.estado === "PENDIENTE" && (
              <button type="button" className="text-sm text-red-600 hover:underline"
                onClick={async () => {
                  if (!window.confirm("¿Cancelar y eliminar esta solicitud?")) return;
                  await api.delete(s.id);
                  setLista((l) => l.filter((x) => x.id !== s.id));
                }}>
                Cancelar solicitud
              </button>
            )}
          </ItemCard>
        );
      })}
    </div>
  );
}
