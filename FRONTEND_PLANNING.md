# Planeación del Frontend (React)

## 🎨 Componentes Clave
- **LoginView:** Formulario de acceso con redirección según rol.
- **DashboardOperario:** - Selector de proyectos asignados.
    - Cronómetro visual (Tiempo activo hoy / Tiempo total proyecto).
    - Botón "Play/Stop" de gran visibilidad.
- **DashboardLider:**
    - Panel de control de proyectos.
    - Buscador y asignador de usuarios.
    - Gráficas de horas hombre (Chart.js / Recharts).
- **AdminPanel:** Tablas CRUD para gestión de personal.

## 🔄 Gestión de Estado (State Management)
- **Context API o Redux:** Para manejar la información del usuario autenticado y el estado global del cronómetro (para que no se pierda al navegar entre páginas).

## 📱 Responsividad
- Diseño **Mobile-First** usando Tailwind CSS, asegurando que el operario pueda marcar tiempos fácilmente desde un navegador móvil antes del lanzamiento de las apps nativas.

## ⏱️ Lógica del Contador
1. Al dar "Start", se envía la petición al Backend.
2. El Frontend inicia un `setInterval` para mostrar el incremento de segundos en pantalla.
3. Al dar "Stop", se sincroniza el tiempo final con el servidor.