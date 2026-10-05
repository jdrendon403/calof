import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { informes as api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import PhotoGallery from "../../components/PhotoGallery";
import StatusBadge from "../../components/StatusBadge";
import { formatDate, formatDateTime } from "../../utils/format";
import InformeForm from "./InformeForm";
import { AccionLider, Campo, ItemCard, Toolbar, Vacio, useEsLider } from "./common";

const FILTROS = [
  { value: "ENVIADO", label: "Por revisar" },
  { value: "BORRADOR,DEVUELTO", label: "Borradores y devueltos" },
  { value: "APROBADO", label: "Aprobados" },
  { value: "", label: "Todos" },
];

export default function InformesView() {
  const esLider = useEsLider();
  const { user } = useAuth();
  const [params, setParams] = useSearchParams();
  const highlight = Number(params.get("id")) || null;
  const [filtro, setFiltro] = useState(esLider ? "ENVIADO" : "");
  const [lista, setLista] = useState(null);
  const [editando, setEditando] = useState(null); // "nuevo" | informe
  const [aviso, setAviso] = useState("");

  const cargar = useCallback(
    () => api.list(filtro && !highlight ? { estado: filtro } : {}).then(setLista).catch(() => setLista([])),
    [filtro, highlight]
  );
  useEffect(() => { cargar(); }, [cargar]);

  const reemplazar = (item) => setLista((l) => l.map((x) => (x.id === item.id ? item : x)));

  if (editando) {
    return (
      <InformeForm
        informe={editando === "nuevo" ? null : editando}
        onCancel={() => setEditando(null)}
        onDone={(id, mensaje) => {
          setEditando(null);
          setAviso(mensaje);
          setParams({ id });
          cargar();
        }}
      />
    );
  }

  return (
    <div className="space-y-4">
      <Toolbar titulo="Informes de servicio" filtro={filtro} setFiltro={(v) => { setParams({}); setFiltro(v); }}
        filtros={FILTROS} accion="+ Nuevo informe" onAccion={() => { setAviso(""); setEditando("nuevo"); }} />
      {aviso && <p className="rounded bg-green-50 px-3 py-2 text-sm text-green-800">{aviso}</p>}
      {lista === null && <Vacio>Cargando...</Vacio>}
      {lista?.length === 0 && <Vacio>No hay informes{filtro ? " en este estado" : ""}.</Vacio>}
      {lista?.map((inf) => {
        const editable = (inf.autor === user?.id || user?.rol === "ADMIN") && ["BORRADOR", "DEVUELTO"].includes(inf.estado);
        return (
          <ItemCard
            key={inf.id}
            highlight={inf.id === highlight}
            resumen={
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium text-slate-800">
                    {inf.consecutivo ? `${inf.consecutivo} · ` : ""}{inf.proyecto_nombre}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500">
                    {formatDate(inf.fecha_servicio)} · {inf.cliente || "Sin cliente"} · {inf.autor_nombre}
                    {inf.fotos.length > 0 && ` · 📷 ${inf.fotos.length}`}
                  </p>
                </div>
                <StatusBadge estado={inf.estado}>{inf.estado_display}</StatusBadge>
              </div>
            }
          >
            {inf.estado === "DEVUELTO" && inf.comentario_revision && (
              <p className="rounded bg-red-50 px-3 py-2 text-sm text-red-800">
                <strong>Devuelto por {inf.revisado_por_nombre}:</strong> {inf.comentario_revision}
              </p>
            )}
            {inf.pdf_url && (
              <a href={inf.pdf_url} target="_blank" rel="noreferrer"
                className="inline-block rounded bg-brand-blue px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
                Ver / descargar PDF
              </a>
            )}
            <Campo titulo="Ubicación">{inf.ubicacion}</Campo>
            <Campo titulo="Personal">{inf.participantes.map((p) => p.nombre).join(", ")}</Campo>
            <Campo titulo="Actividades realizadas">{inf.actividades}</Campo>
            <Campo titulo="Observaciones y recomendaciones">{inf.observaciones}</Campo>
            <PhotoGallery fotos={inf.fotos} />
            {(inf.firma_url || inf.firma_nombre) && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Recibido por</p>
                {inf.firma_url && <img src={inf.firma_url} alt="Firma" className="mt-1 h-16 rounded border border-slate-200" />}
                <p className="text-sm text-slate-800">{inf.firma_nombre}{inf.firma_cargo && ` — ${inf.firma_cargo}`}</p>
              </div>
            )}
            {inf.estado === "APROBADO" && (
              <p className="text-xs text-slate-500">Aprobado por {inf.revisado_por_nombre} · {formatDateTime(inf.revisado_en)}</p>
            )}
            {editable && (
              <div className="flex flex-wrap gap-3">
                <button type="button" onClick={() => setEditando(inf)}
                  className="rounded bg-slate-700 px-4 py-2 text-sm font-medium text-white hover:bg-slate-800">
                  Editar y enviar
                </button>
                <button type="button" className="text-sm text-red-600 hover:underline"
                  onClick={async () => {
                    if (!window.confirm("¿Eliminar este informe y sus fotos?")) return;
                    await api.delete(inf.id);
                    setLista((l) => l.filter((x) => x.id !== inf.id));
                  }}>
                  Eliminar
                </button>
              </div>
            )}
            {inf.puede_gestionar && inf.estado === "ENVIADO" && (
              <AccionLider
                placeholder="Comentario (obligatorio si lo devuelve)"
                acciones={[
                  {
                    label: "Aprobar y generar PDF",
                    color: "bg-green-600 hover:bg-green-700",
                    onClick: async (comentario) => reemplazar(await api.accion(inf.id, "aprobar", { comentario })),
                  },
                  {
                    label: "Devolver para corrección",
                    color: "bg-red-600 hover:bg-red-700",
                    requiereComentario: true,
                    onClick: async (comentario) => reemplazar(await api.accion(inf.id, "devolver", { comentario })),
                  },
                ]}
              />
            )}
          </ItemCard>
        );
      })}
    </div>
  );
}
