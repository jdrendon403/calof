/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Identidad corporativa InControl (incontrol.com.co)
        brand: {
          primary: "#39436B", // azul marino: botones, títulos
          accent: "#51649D", // azul medio: hover, secundarios
          blue: "#00639B", // azul corporativo: franja del encabezado, gráficas
          text: "#606060", // gris de texto del sitio
        },
        // La UI usa la paleta `slate` en todos los componentes; se reemplaza por una
        // escala azul marino construida sobre los colores de marca (700 = primary).
        slate: {
          50: "#F4F6FA",
          100: "#E8ECF4",
          200: "#D3D9E8",
          300: "#B3BDD5",
          400: "#8393BA",
          500: "#51649D",
          600: "#45568A",
          700: "#39436B",
          800: "#2E3657",
          900: "#232A44",
          950: "#171C2E",
        },
      },
      fontFamily: {
        sans: ["Montserrat", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
