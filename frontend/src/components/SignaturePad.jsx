import { useEffect, useRef, useState } from "react";

/** Firma con el dedo o el mouse. `onSave(blob)` recibe un PNG con fondo transparente. */
export default function SignaturePad({ onSave, onCancel, saving = false }) {
  const canvasRef = useRef(null);
  const drawing = useRef(false);
  const [empty, setEmpty] = useState(true);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ratio = window.devicePixelRatio || 1;
    canvas.width = canvas.offsetWidth * ratio;
    canvas.height = canvas.offsetHeight * ratio;
    const ctx = canvas.getContext("2d");
    ctx.scale(ratio, ratio);
    ctx.lineWidth = 2.2;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.strokeStyle = "#232A44";
  }, []);

  const point = (e) => {
    const r = canvasRef.current.getBoundingClientRect();
    return [e.clientX - r.left, e.clientY - r.top];
  };

  const down = (e) => {
    e.preventDefault();
    canvasRef.current.setPointerCapture(e.pointerId);
    drawing.current = true;
    const ctx = canvasRef.current.getContext("2d");
    ctx.beginPath();
    ctx.moveTo(...point(e));
  };

  const move = (e) => {
    if (!drawing.current) return;
    const ctx = canvasRef.current.getContext("2d");
    ctx.lineTo(...point(e));
    ctx.stroke();
    setEmpty(false);
  };

  const up = () => (drawing.current = false);

  const clear = () => {
    const c = canvasRef.current;
    c.getContext("2d").clearRect(0, 0, c.width, c.height);
    setEmpty(true);
  };

  const save = () => canvasRef.current.toBlob((blob) => blob && onSave(blob), "image/png");

  return (
    <div>
      <canvas
        ref={canvasRef}
        onPointerDown={down}
        onPointerMove={move}
        onPointerUp={up}
        onPointerLeave={up}
        className="h-40 w-full touch-none rounded border-2 border-dashed border-slate-300 bg-white"
      />
      <p className="mt-1 text-xs text-slate-500">Firme dentro del recuadro.</p>
      <div className="mt-2 flex gap-2">
        <button type="button" onClick={save} disabled={empty || saving}
          className="rounded bg-slate-700 px-3 py-1.5 text-sm text-white hover:bg-slate-800 disabled:opacity-50">
          {saving ? "Guardando..." : "Guardar firma"}
        </button>
        <button type="button" onClick={clear} disabled={saving}
          className="rounded border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50">
          Borrar
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel} className="px-3 py-1.5 text-sm text-slate-600">Cancelar</button>
        )}
      </div>
    </div>
  );
}
