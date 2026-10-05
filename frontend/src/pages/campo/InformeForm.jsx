import { useEffect, useState } from "react";
import { fotos as fotosApi, informes as api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import PhotoGallery from "../../components/PhotoGallery";
import PhotoPicker, { uploadPending } from "../../components/PhotoPicker";
import SignaturePad from "../../components/SignaturePad";
import { minutesToHHMM } from "../../utils/time";
import { errorMessage } from "../../utils/format";
import {
  NotaProyectoEnCurso, btnPrimary, btnSecondary, input, label, useProyectoPorDefecto, useProyectos,
} from "./common";

const hoy = () => {
  const d = new Date();
  d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
  return d.toISOString().slice(0, 10);
};

/**
 * Crear o editar un informe (borrador o devuelto). Al guardar: crea/actualiza el informe,
 * sube las fotos nuevas y la firma pendiente. `onDone(id, mensaje)`.
 */
export default function InformeForm({ informe, onDone, onCancel }) {
  const { user } = useAuth();
  const proyectos = useProyectos();
  const [form, setForm] = useState({
    proyecto: informe?.proyecto ? String(informe.proyecto) : "",
    fecha_servicio: informe?.fecha_servicio || hoy(),
    ubicacion: informe?.ubicacion || "",
    actividades: informe?.actividades || "",
    observaciones: informe?.observaciones || "",
    firma_nombre: informe?.firma_nombre || "",
    firma_cargo: informe?.firma_cargo || "",
  });
  // Personal: lo que ya tenía el informe + quienes registraron tiempo ese día en el proyecto
  const [personal, setPersonal] = useState(
    (informe?.participantes || []).map((p) => ({ usuario_id: p.id, nombre: p.nombre, minutos: null }))
  );
  const [seleccion, setSeleccion] = useState(new Set((informe?.participantes || []).map((p) => p.id)));
  const [fotosGuardadas, setFotosGuardadas] = useState(informe?.fotos || []);
  const [fotosNuevas, setFotosNuevas] = useState([]);
  const [firmaUrl, setFirmaUrl] = useState(informe?.firma_url || null);
  const [firmaPendiente, setFirmaPendiente] = useState(null);
  const [firmando, setFirmando] = useState(false);
  const [estado, setEstado] = useState("");
  const [error, setError] = useState("");
  // Si el informe se creó pero algo posterior falló (foto, firma), reintentar no lo duplica
  const [guardadoId, setGuardadoId] = useState(informe?.id || null);
  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }));

  const enCurso = useProyectoPorDefecto(
    proyectos, form.proyecto, (proyecto) => setForm((f) => ({ ...f, proyecto })), !informe
  );

  // Prellenar personal desde Tiempos al elegir proyecto y fecha
  useEffect(() => {
    if (!form.proyecto || !form.fecha_servicio) return;
    api.sugerirPersonal(form.proyecto, form.fecha_servicio).then((sugeridos) => {
      setPersonal((prev) => {
        const porId = new Map(prev.filter((p) => seleccion.has(p.usuario_id)).map((p) => [p.usuario_id, p]));
        sugeridos.forEach((s) => porId.set(s.usuario_id, s));
        if (!porId.has(user.id)) {
          porId.set(user.id, { usuario_id: user.id, nombre: `${user.first_name} ${user.last_name}`.trim() || user.username, minutos: null });
        }
        return [...porId.values()].sort((a, b) => a.nombre.localeCompare(b.nombre));
      });
      if (!informe) setSeleccion(new Set([user.id, ...sugeridos.map((s) => s.usuario_id)]));
    }).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [form.proyecto, form.fecha_servicio]);

  const toggle = (id) =>
    setSeleccion((s) => {
      const n = new Set(s);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });

  const guardar = async (enviar) => {
    setError("");
    setEstado("Guardando...");
    try {
      const data = { ...form, participante_ids: [...seleccion] };
      const inf = guardadoId ? await api.update(guardadoId, data) : await api.create(data);
      setGuardadoId(inf.id);
      const fallidas = await uploadPending("informe", inf.id, fotosNuevas, (i, n) => setEstado(`Subiendo foto ${i} de ${n}...`));
      setFotosNuevas([]);
      if (firmaPendiente) {
        setEstado("Guardando firma...");
        await api.guardarFirma(inf.id, firmaPendiente);
        setFirmaPendiente(null);
      }
      if (enviar) {
        setEstado("Enviando a revisión...");
        await api.accion(inf.id, "enviar");
      }
      const extra = fallidas ? ` ${fallidas} foto(s) no se pudieron subir.` : "";
      onDone(inf.id, (enviar ? "Informe enviado a revisión." : "Borrador guardado.") + extra);
    } catch (err) {
      setError(errorMessage(err));
      setEstado("");
    }
  };

  const ocupado = !!estado;

  return (
    <form onSubmit={(e) => e.preventDefault()} className="space-y-5 rounded-lg bg-white p-4 shadow sm:p-6">
      <div>
        <h3 className="text-lg font-medium text-slate-800">{informe ? "Editar informe de servicio" : "Nuevo informe de servicio"}</h3>
        {informe?.estado === "DEVUELTO" && informe.comentario_revision && (
          <p className="mt-2 rounded bg-red-50 px-3 py-2 text-sm text-red-800">
            <strong>Devuelto para corrección:</strong> {informe.comentario_revision}
          </p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="sm:col-span-2">
          <label className={label}>Proyecto</label>
          <select required value={form.proyecto} onChange={set("proyecto")} className={input}>
            <option value="">Seleccione un proyecto</option>
            {proyectos.map((p) => <option key={p.id} value={p.id}>{p.nombre}{p.cliente ? ` — ${p.cliente}` : ""}</option>)}
          </select>
          {!informe && <NotaProyectoEnCurso enCurso={enCurso} valor={form.proyecto} />}
        </div>
        <div>
          <label className={label}>Fecha del servicio</label>
          <input type="date" required value={form.fecha_servicio} onChange={set("fecha_servicio")} className={input} />
        </div>
      </div>
      <div>
        <label className={label}>Ubicación / sitio</label>
        <input type="text" value={form.ubicacion} onChange={set("ubicacion")} placeholder="Ej.: Subestación Norte, celda 4" className={input} />
      </div>

      <div>
        <label className={label}>Personal</label>
        <p className="text-xs text-slate-500">Se toma de los registros de Tiempos del proyecto en esa fecha.</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {personal.length === 0 && <span className="text-sm text-slate-500">Elija proyecto y fecha.</span>}
          {personal.map((p) => (
            <label key={p.usuario_id} className="flex cursor-pointer items-center gap-2 rounded border border-slate-300 px-3 py-1.5 text-sm">
              <input type="checkbox" checked={seleccion.has(p.usuario_id)} onChange={() => toggle(p.usuario_id)} />
              {p.nombre}
              {p.minutos != null && <span className="text-xs text-slate-500">{minutesToHHMM(p.minutos)}</span>}
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className={label}>Actividades realizadas</label>
        <textarea rows={6} value={form.actividades} onChange={set("actividades")}
          placeholder="Describa el trabajo realizado, paso a paso." className={input} />
      </div>
      <div>
        <label className={label}>Observaciones y recomendaciones</label>
        <textarea rows={3} value={form.observaciones} onChange={set("observaciones")}
          placeholder="Hallazgos, pendientes, recomendaciones al cliente..." className={input} />
      </div>

      <div>
        <label className={label}>Registro fotográfico</label>
        <div className="mt-2 space-y-3">
          <PhotoGallery
            fotos={fotosGuardadas}
            onDelete={async (id) => {
              await fotosApi.delete(id);
              setFotosGuardadas((f) => f.filter((x) => x.id !== id));
            }}
          />
          <PhotoPicker items={fotosNuevas} onChange={setFotosNuevas} max={30 - fotosGuardadas.length} disabled={ocupado} />
        </div>
      </div>

      <fieldset className="rounded border border-slate-200 p-4">
        <legend className="px-1 text-sm font-medium text-slate-700">Recibido por el cliente</legend>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={label}>Nombre</label>
            <input type="text" value={form.firma_nombre} onChange={set("firma_nombre")} className={input} />
          </div>
          <div>
            <label className={label}>Cargo</label>
            <input type="text" value={form.firma_cargo} onChange={set("firma_cargo")} className={input} />
          </div>
        </div>
        <div className="mt-3">
          {firmando ? (
            <SignaturePad
              onCancel={() => setFirmando(false)}
              onSave={(blob) => {
                setFirmaPendiente(blob);
                setFirmaUrl(URL.createObjectURL(blob));
                setFirmando(false);
              }}
            />
          ) : (
            <div className="flex flex-wrap items-center gap-3">
              {firmaUrl && <img src={firmaUrl} alt="Firma del cliente" className="h-20 rounded border border-slate-200 bg-white" />}
              <button type="button" onClick={() => setFirmando(true)} className={btnSecondary}>
                {firmaUrl ? "Volver a firmar" : "✍ Firma del cliente"}
              </button>
              {firmaUrl && informe?.firma_url && !firmaPendiente && (
                <button type="button" className="text-sm text-red-600 hover:underline"
                  onClick={async () => { await api.borrarFirma(informe.id); setFirmaUrl(null); }}>
                  Quitar firma
                </button>
              )}
            </div>
          )}
        </div>
      </fieldset>

      {error && <p className="text-sm text-red-600">{error}</p>}
      <div className="flex flex-wrap gap-2">
        <button type="button" disabled={ocupado || !form.proyecto} onClick={() => guardar(true)}
          className="rounded bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-50">
          Enviar a revisión
        </button>
        <button type="button" disabled={ocupado || !form.proyecto} onClick={() => guardar(false)} className={btnPrimary}>
          {estado || "Guardar borrador"}
        </button>
        <button type="button" disabled={ocupado} onClick={onCancel} className={btnSecondary}>Cancelar</button>
      </div>
    </form>
  );
}
