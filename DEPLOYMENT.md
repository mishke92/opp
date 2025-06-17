# Guía de Despliegue para Consultorio Jurídico App

Esta guía describe los pasos para desplegar la aplicación Consultorio Jurídico en un entorno de producción.

## 1. Requisitos Previos

*   **Python:** Versión 3.8 o superior.
*   **Pip:** Gestor de paquetes de Python.
*   **Git:** Para clonar el repositorio.
*   **Servidor PostgreSQL:** Una instancia de PostgreSQL en ejecución y accesible.
*   **Entorno Virtual:** Recomendado (ej. `venv`).
*   **Variables de Entorno:** Un mecanismo para configurar variables de entorno en el servidor (ej. archivos `.env` gestionados por el sistema, configuración de PaaS, etc.).

## 2. Configuración Inicial

1.  **Clonar el Repositorio:**
    ```bash
    git clone <url_del_repositorio>
    cd nombre_del_directorio_del_proyecto
    ```

2.  **Crear y Activar Entorno Virtual:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Linux/macOS
    # venv\Scripts\activate    # En Windows
    ```

3.  **Instalar Dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configurar Variables de Entorno:**
    *   Copia el archivo `.env.example` a `.env`:
        ```bash
        cp .env.example .env
        ```
    *   **Edita `.env` y rellena las variables de entorno necesarias.** Es crucial configurar correctamente `SECRET_KEY` y `DATABASE_URL` para producción.
        *   `FLASK_APP=wsgi.py`
        *   `FLASK_CONFIG=production`
        *   `SECRET_KEY`: Genera una clave segura (ej. `python -c 'import secrets; print(secrets.token_hex(32))'`).
        *   `DATABASE_URL`: La URL de conexión a tu base de datos PostgreSQL. Formato: `postgresql://user:password@host:port/database`.

## 3. Base de Datos

1.  **Crear Base de Datos y Usuario en PostgreSQL:**
    *   Asegúrate de tener una base de datos PostgreSQL creada para la aplicación.
    *   Crea un usuario con permisos para acceder y modificar esta base de datos.

2.  **Verificar `DATABASE_URL`:**
    *   Confirma que la variable `DATABASE_URL` en tu archivo `.env` (o en las variables de entorno del servidor) apunta correctamente a tu base de datos de producción.

3.  **Ejecutar Migraciones de Base de Datos:**
    *   Con las variables de entorno configuradas (especialmente `FLASK_APP`, `FLASK_CONFIG`, `DATABASE_URL`), aplica las migraciones:
        ```bash
        flask db upgrade
        ```
    *   Esto creará todas las tablas necesarias en la base de datos según los modelos definidos.

## 4. Crear Usuario Administrador

*   La forma más sencilla de crear un usuario administrador es utilizando el comando de seeding si está configurado para ello:
    ```bash
    flask seed-db
    ```
    Esto debería crear el usuario `admin@example.com` (o el configurado en `seed_data.py`) con privilegios de administrador.
*   Si no se usa `seed-db` para esto en producción, se necesitaría un comando específico como `flask create-admin` (que no está implementado en este proyecto base) o crear el usuario manualmente a través de la interfaz de la aplicación (si es posible registrarse y luego promover a admin manualmente en la BD o con otro script).

## 5. Ejecutar la Aplicación con Gunicorn

*   Gunicorn es el servidor WSGI recomendado para ejecutar aplicaciones Flask en producción.
*   El archivo `wsgi.py` y el `Procfile` están configurados para usar Gunicorn.
*   **Comando Básico:**
    ```bash
    gunicorn --bind 0.0.0.0:8000 wsgi:app
    ```
    (Reemplaza `8000` con el puerto deseado si es necesario).
*   **Usando el Script `start_prod.sh` (si se ha configurado):**
    ```bash
    ./start_prod.sh
    ```
    Este script puede incluir pasos adicionales como aplicar migraciones y configurar más opciones de Gunicorn.
*   **Variables de Entorno para Gunicorn:**
    *   `GUNICORN_WORKERS`: Número de workers (ej. `2-4` por core de CPU).
    *   `PORT`: El puerto en el que Gunicorn debe escuchar (usado por plataformas como Heroku).
    *   Consulta la documentación de Gunicorn para más opciones de configuración (logs, timeouts, etc.).

## 6. Servidor Web (Proxy Inverso - Conceptual)

*   Para un despliegue robusto, se recomienda usar un servidor web como Nginx o Caddy como proxy inverso delante de Gunicorn.
*   **Beneficios:**
    *   Manejo de conexiones entrantes y balanceo de carga (si tienes múltiples instancias de Gunicorn).
    *   Servir archivos estáticos directamente (ver sección 7).
    *   Terminación SSL (manejo de HTTPS).
    *   Configuración de cabeceras de seguridad.
*   **Ejemplo Conceptual (Nginx):**
    ```nginx
    server {
        listen 80;
        server_name tu_dominio.com;

        location / {
            proxy_pass http://127.0.0.1:8000; # Asumiendo que Gunicorn corre en el puerto 8000 localmente
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static {
            alias /ruta/a/tu/proyecto/app/static; # Ruta a tus archivos estáticos
            expires 30d;
        }
    }
    ```
    *   Deberás configurar SSL (ej. con Let's Encrypt) para HTTPS.

## 7. Archivos Estáticos en Producción

*   En desarrollo, Flask sirve los archivos estáticos automáticamente. En producción, esto no es eficiente.
*   **Estrategias:**
    1.  **Servidor Web (Nginx/Caddy):** Configura tu proxy inverso para servir directamente los archivos desde `app/static/`. Esto es lo más común y eficiente. (Ver ejemplo en sección 6).
    2.  **WhiteNoise:** Una librería Python que permite a tu aplicación WSGI servir archivos estáticos de forma eficiente, incluso detrás de Gunicorn, sin necesidad de configurar Nginx para los estáticos. Es útil para plataformas PaaS donde no tienes control total sobre el servidor web.
        *   Para usarlo: `pip install whitenoise`, y luego envolver la app Flask en `wsgi.py`:
            ```python
            # from whitenoise import WhiteNoise
            # application = WhiteNoise(application)
            # application.add_files("path/to/static/files")
            ```
    3.  **CDN (Content Delivery Network):** Para aplicaciones con mucho tráfico, subir los archivos estáticos a un CDN (ej. AWS CloudFront, Cloudflare) puede mejorar significativamente los tiempos de carga para usuarios globales. La aplicación se configuraría para generar URLs de estáticos que apunten al CDN.

## 8. Consideraciones Adicionales

*   **Logging:** Configura un logging robusto para producción. `ProductionConfig` tiene un ejemplo comentado para iniciar. Considera enviar logs a un servicio centralizado.
*   **Backups de Base de Datos:** Implementa una estrategia regular de backups para tu base de datos PostgreSQL.
*   **Seguridad:**
    *   Mantén las dependencias actualizadas.
    *   Revisa las configuraciones de seguridad de Flask (ej. CSRF si no se deshabilitó para APIs).
    *   Configura HTTPS (SSL/TLS).
    *   Usa un firewall.
*   **Monitorización:** Considera herramientas para monitorizar el rendimiento y errores de la aplicación en producción (ej. Sentry, New Relic, Datadog).

Esta guía proporciona una base. Los detalles específicos del despliegue pueden variar según la plataforma de hosting elegida (ej. VPS, Docker, Kubernetes, Heroku, AWS Elastic Beanstalk, etc.).
