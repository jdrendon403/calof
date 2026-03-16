# Planeación del Backend (Django)

## 🗄️ Modelos de Datos (App: `core` o `management`)
- **CustomUser:** Extensión de `AbstractUser` para incluir `rol` y `telefono`.
- **Project:** Almacena datos del proyecto y `usuarios_asignados` (Many-to-Many).
- **TimeEntry:** Registra `hora_inicio`, `hora_fin` y el flag `cierre_automatico`.
- **Assignment:** Planificación de fechas específicas para usuarios en proyectos.

## 🛠️ Endpoints Principales (API)
- `POST /api/auth/login/`: Autenticación y retorno de Token/Rol.
- `GET /api/projects/`: Lista de proyectos (filtrado según rol).
- `POST /api/time/start/`: Inicia el contador para un proyecto.
- `PATCH /api/time/stop/`: Finaliza la actividad actual.
- `GET /api/reports/settlement/`: Datos calculados para liquidación (semanal/mensual).

## ⏲️ Lógica de Automatización
Se implementará un **Management Command** de Django:
- `python manage.py close_sessions`
- **Regla 1:** Ejecución a las 17:00. Cierra registros abiertos con `cierre_automatico=True`.
- **Regla 2:** Ejecución a las 00:00. Cierre de seguridad para cualquier registro remanente.

## 🔒 Seguridad
- Autenticación vía JWT (JSON Web Tokens).
- Permissions Classes de DRF: `IsAdminUser`, `IsProjectLeader`, `IsOperario`.