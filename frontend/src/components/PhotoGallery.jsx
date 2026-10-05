/** Fotos ya guardadas. Al tocar una se abre en tamaño completo; si `onDelete`, permite borrarla. */
export default function PhotoGallery({ fotos, onDelete }) {
  if (!fotos?.length) return null;
  return (
    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
      {fotos.map((f) => (
        <figure key={f.id} className="relative">
          <a href={f.url} target="_blank" rel="noreferrer">
            <img src={f.miniatura_url} alt={f.descripcion} className="h-24 w-full rounded object-cover" loading="lazy" />
          </a>
          {f.descripcion && <figcaption className="mt-0.5 truncate text-xs text-slate-500">{f.descripcion}</figcaption>}
          {onDelete && (
            <button
              type="button"
              onClick={() => window.confirm("¿Eliminar esta foto?") && onDelete(f.id)}
              className="absolute right-1 top-1 rounded bg-white/90 px-2 text-sm font-semibold text-red-600 shadow"
              aria-label="Eliminar foto"
            >
              ×
            </button>
          )}
        </figure>
      ))}
    </div>
  );
}
