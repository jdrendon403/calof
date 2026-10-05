import { useRef, useState } from "react";
import { fotos } from "../api/client";
import { compressImage } from "../utils/image";

/**
 * Selección de fotos nuevas (cámara o galería). Comprime cada foto en el navegador y
 * mantiene la lista local `items` = [{key, blob, preview, descripcion}] para subirla luego.
 */
export default function PhotoPicker({ items, onChange, max = 10, disabled = false }) {
  const inputRef = useRef(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const handleFiles = async (fileList) => {
    setError("");
    const files = Array.from(fileList).slice(0, Math.max(0, max - items.length));
    if (fileList.length > files.length) setError(`Máximo ${max} fotos.`);
    setProcessing(true);
    const nuevos = [];
    for (const file of files) {
      try {
        const blob = await compressImage(file);
        nuevos.push({ key: `${Date.now()}-${Math.random()}`, blob, preview: URL.createObjectURL(blob), descripcion: "" });
      } catch {
        setError(`"${file.name}" no es una imagen válida.`);
      }
    }
    setProcessing(false);
    onChange([...items, ...nuevos]);
    if (inputRef.current) inputRef.current.value = "";
  };

  const update = (key, patch) => onChange(items.map((it) => (it.key === key ? { ...it, ...patch } : it)));
  const remove = (key) => {
    const it = items.find((i) => i.key === key);
    if (it) URL.revokeObjectURL(it.preview);
    onChange(items.filter((i) => i.key !== key));
  };

  return (
    <div>
      {items.length > 0 && (
        <div className="mb-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {items.map((it) => (
            <div key={it.key} className="rounded border border-slate-200 p-1.5">
              <div className="relative">
                <img src={it.preview} alt="" className="h-28 w-full rounded object-cover" />
                <button
                  type="button"
                  onClick={() => remove(it.key)}
                  disabled={disabled}
                  className="absolute right-1 top-1 rounded bg-white/90 px-2 text-sm font-semibold text-red-600 shadow"
                  aria-label="Quitar foto"
                >
                  ×
                </button>
              </div>
              <input
                type="text"
                placeholder="Descripción (opcional)"
                value={it.descripcion}
                onChange={(e) => update(it.key, { descripcion: e.target.value })}
                disabled={disabled}
                className="mt-1.5 w-full rounded border border-slate-300 px-2 py-1 text-xs"
              />
            </div>
          ))}
        </div>
      )}
      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />
      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        disabled={disabled || processing || items.length >= max}
        className="rounded border border-dashed border-slate-400 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-50"
      >
        {processing ? "Procesando fotos..." : "📷 Agregar fotos"}
      </button>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}

/** Sube en orden las fotos pendientes de un PhotoPicker. Devuelve cuántas fallaron. */
export async function uploadPending(tipo, padreId, items, onProgress) {
  let fallidas = 0;
  for (let i = 0; i < items.length; i++) {
    onProgress?.(i + 1, items.length);
    try {
      await fotos.upload(tipo, padreId, items[i].blob, items[i].descripcion);
      URL.revokeObjectURL(items[i].preview);
    } catch {
      fallidas++;
    }
  }
  return fallidas;
}
