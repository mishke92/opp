# Consultorio Jurídico Virtual - Aplicación Flask

Esta aplicación es una plataforma de consultorio jurídico virtual diseñada para ofrecer asesoría legal, información sobre leyes, perfiles de abogados, y más, con un enfoque inicial en Ecuador y preparada para expansión multi-país.

## Características Principales (Simuladas/Implementadas)

*   **Autenticación de Usuarios:** Registro, inicio de sesión, cierre de sesión, y modo invitado.
*   **Gestión de Contenido:**
    *   Leyes (resúmenes y contenido completo para premium).
    *   Perfiles de Abogados (básicos y completos para premium).
    *   Artículos/Blog (vistas previas y contenido completo para premium).
    *   Eventos (información básica y detalles exclusivos para premium).
    *   Terminología Legal (glosario básico y completo para premium).
*   **Niveles de Suscripción:**
    *   **Gratuito:** Acceso limitado al contenido.
    *   **Premium:** Acceso completo a todo el contenido y funcionalidades avanzadas (simulado).
    *   Gestión de suscripción simulada (selección de plan, "pago", cancelación).
*   **Funcionalidades Premium:**
    *   Búsqueda avanzada y filtros en leyes.
    *   Marcar leyes como favoritas.
    *   Acceso a contenido y perfiles completos.
    *   Placeholders para generador de documentos y chatbot avanzado.
*   **Interfaz de Administración:** Sección `/admin` (protegida) para gestionar modelos de datos principales (Usuarios, Países, Leyes, etc.) usando Flask-Admin.
*   **Preparación Multi-País:**
    *   La estructura del backend (modelos y rutas) está preparada para manejar contenido de múltiples países.
    *   **Selector de País en UI:** La barra de navegación incluye un selector de país que permite al usuario cambiar el país activo en su sesión. El contenido mostrado en las secciones (Leyes, Abogados, etc.) se filtra según el país seleccionado. Actualmente, solo Ecuador tiene datos de ejemplo sembrados.

## Configuración y Ejecución (Desarrollo)

1.  **Clonar el Repositorio:**
    ```bash
    git clone <url_del_repositorio>
    cd nombre_del_proyecto
    ```
2.  **Entorno Virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate # o venv\Scripts\activate en Windows
    ```
3.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Variables de Entorno:**
    *   Copia `.env.example` a `.env`.
    *   Configura `FLASK_CONFIG=development`.
    *   Asegúrate de que `SECRET_KEY` esté definida.
    *   Para desarrollo, `DATABASE_URL` puede apuntar a una base de datos PostgreSQL local o se usará SQLite (`dev.db`) si `DEV_DATABASE_URL` no está definida (ver `app/config.py`).
5.  **Base de Datos (Desarrollo):**
    *   Si usas PostgreSQL, asegúrate de que el servidor esté corriendo y la base de datos exista.
    *   Aplica las migraciones:
        ```bash
        flask db upgrade
        ```
6.  **Sembrar Datos de Ejemplo (Opcional pero Recomendado):**
    ```bash
    flask seed-db
    ```
    Esto creará usuarios de ejemplo (incluyendo un admin: `admin@example.com` pass: `adminpass` y un premium: `testuser1@example.com` pass: `password123`), países, y contenido de ejemplo para Ecuador.
7.  **Ejecutar la Aplicación:**
    ```bash
    flask run
    ```
    La aplicación estará disponible en `http://127.0.0.1:5000/`.
    El panel de administración está en `http://127.0.0.1:5000/admin/`.

## Pruebas

*   Configura el entorno de pruebas (ver `TESTING_NOTES.md` y `tests/conftest.py`).
*   Ejecuta las pruebas con:
    ```bash
    pytest
    ```

## Despliegue

Consulta `DEPLOYMENT.md` para instrucciones detalladas sobre cómo desplegar la aplicación en un entorno de producción usando Gunicorn y PostgreSQL.

## Tecnologías Utilizadas

*   **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Admin
*   **Base de Datos:** PostgreSQL (para producción), SQLite (para pruebas y desarrollo opcional)
*   **Frontend:** HTML, CSS (básico), JavaScript (básico para interacciones UI)
*   **Servidor WSGI (Producción):** Gunicorn
*   **Pruebas:** Pytest, Pytest-Flask

## Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue las guías estándar de estilo de código y envía Pull Requests.
