## 🚀 Plan Maestro de Desarrollo: Sistema de Gestión de Proyectos y Tiempos

### 1. Diseño de Arquitectura y Base de Datos

Antes de escribir código, definiremos la estructura de datos. Django facilita esto con sus *Models*.

* **Modelo de Usuario Personalizado:** Extender `AbstractUser` de Django para incluir `telefono`, `rol` (Admin, Líder, Operario).
* **Modelo de Proyecto:** Nombre, descripción, cliente, estado (Abierto/Cerrado), fecha de inicio y fin.
* **Modelo de Asignación:** Tabla intermedia que vincula usuarios con proyectos y fechas programadas.
* **Modelo de Registro de Tiempos (Timesheets):** * Campos: Usuario, Proyecto, Inicio (datetime), Fin (datetime, puede ser nulo si está activo), Duración total.

---

### 2. Fase de Backend (Django + PostgreSQL)

El "cerebro" de la aplicación se encargará de la lógica de negocio y la seguridad.

1. **Configuración de Entorno:** Uso de **Docker** para levantar contenedores de Python y la base de datos PostgreSQL.
2. **Módulo de Autenticación:** Implementar **JWT (JSON Web Tokens)** para una comunicación segura con React.
3. **Desarrollo de API (Django REST Framework):**
* **Endpoints de Usuarios:** CRUD completo según el rol.
* **Endpoints de Proyectos:** Creación y asignación de personal.
* **Lógica de Registro de Tiempos:** Crear el endpoint para "Iniciar actividad" (pone un `timestamp` de inicio) y "Finalizar actividad".


4. **Tareas Programadas (Celery + Redis):** Implementar el "cierre automático" de las 5:00 PM y medianoche para usuarios activos.

---

### 3. Fase de Frontend (React)

La interfaz debe ser **Responsive** (adaptable a móvil y PC) usando una librería de componentes como Tailwind CSS o Material UI.

* **Dashboard por Rol:**
* **Operario:** Botón grande de "Play/Stop" para actividad, contador en tiempo real y tabla de sus propias horas.
* **Líder:** Vista de calendario para programación y gráficos de barras para horas hombre por proyecto.
* **Administrador:** Panel de control de usuarios y configuración global.


* **Estado Global:** Uso de *React Context* o *Redux* para mantener la sesión del usuario y el estado del cronómetro activo.

---

### 4. Lógica de Liquidación y Reportes

Este es el núcleo de valor para la empresa de ingeniería.

* **Cálculo de Horas:** Algoritmos que sumen las diferencias entre `inicio` y `fin`, agrupando por día, semana o mes.
* **Exportación:** Generación de reportes en PDF o Excel para la liquidación de nómina.

---

### 5. Roadmap de Implementación (Paso a Paso)

| Fase | Tarea Principal | Entregable |
| --- | --- | --- |
| **0** | Configuración de Docker y Base de Datos | Entorno de desarrollo listo. |
| **1** | Autenticación y Modelos de Usuario | Login funcional y roles definidos. |
| **2** | Gestión de Proyectos y Asignaciones | CRUD de proyectos y asignación de personal. |
| **3** | Módulo de Tiempos (Check-in / Check-out) | Registro de actividad y cronómetro funcional. |
| **4** | Automatización de Cierres | Script que finaliza turnos a las 5 PM. |
| **5** | Frontend y Visualización de Datos | Dashboard responsive con gráficas de horas. |
| **6** | Pruebas y Despliegue | App desplegada en servidor (ej. AWS o DigitalOcean). |

---

### 6. Consideración Especial: El Cierre Automático

Para cumplir con el requerimiento de las 5:00 PM, usaremos **Django-Crontab** o **Celery Beat**. La lógica será:

> "Si existe un registro de tiempo donde `fin` es nulo, actualizar `fin` con la hora actual y marcar como 'Finalizado por sistema'".

---

### Siguientes pasos recomendados

¿Te gustaría que comencemos definiendo el **esquema técnico detallado de la base de datos** (tablas y relaciones) o prefieres que te ayude primero con la **configuración inicial del archivo `docker-compose.yml**` para el proyecto?