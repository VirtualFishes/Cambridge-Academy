# Cambridge Academy — Sistema de Gestión Académica

**Versión:** 1.0.0
**Estado:** Entrega funcional estable
**Arquitectura:** MVC + Entities
**Lenguaje:** Python
**Interfaz gráfica:** PySide6
**Base de datos:** PostgreSQL / Supabase

> Contenido publicitario: https://www.tiktok.com/@stivenmejiajo/video/7634946003065376021?_r=1&_t=ZS-9608R907UkH

---

## Descripción del proyecto

Cambridge Academy es un sistema de gestión académica desarrollado para una academia de idiomas ficticia.
Su objetivo es digitalizar y automatizar procesos administrativos relacionados con estudiantes, profesores, cursos, matrículas, pagos, reportes y gestión de accesos según el rol del usuario.

La versión `1.0.0` representa una entrega funcional completa, ejecutable y evaluable, construida a partir de los requerimientos definidos en las historias de usuario y organizada bajo una arquitectura **MVC + Entities**.

---

## Funcionalidades principales

### Gestión de acceso

- Inicio de sesión de usuarios.
- Validación de credenciales.
- Redirección según rol:
  - Administrador.
  - Profesor.
  - Estudiante.

### Módulo administrativo

- Registro de estudiantes.
- Consulta de estudiantes.
- Actualización de datos de estudiantes.
- Eliminación de estudiantes.
- Registro de profesores.
- Consulta de profesores.
- Actualización de datos de profesores.
- Eliminación de profesores.
- Registro de cursos.
- Consulta de cursos.
- Actualización de cursos.
- Eliminación de cursos.
- Gestión de matrículas.
- Gestión de pagos.
- Consulta de reportes administrativos.

### Módulo profesor

- Consulta de cursos asignados.
- Consulta de detalles de cursos.
- Registro y gestión de notas de estudiantes.

### Módulo estudiante

- Consulta de información académica.
- Consulta de cursos.
- Consulta de calificaciones.
- Consulta de estado académico.

---

## Estructura del repositorio:

Carpeta `ca_program`
> Entorno de desarrollo del software.

Carpeta `database`
> Módulo que establece la conexión con la base de datos.

Archivo `main.py`
> Ejecuta el software.

Carpeta `docs`
> Agrupa la documentación en el desarrollo del software.

Archivo `setup.py`
> Configura el entorno virtual e instala las dependencias.

Archivo `.env`
> Archivo local de configuración para la conexión con la base de datos. No debe versionarse.

---

## Requisitos

- Python 3.10 o superior. (pip incluido)
- PostgreSQL instalado y en ejecución.
- Sistema operativo Windows, Linux o macOS.
- Conexión a una base de datos PostgreSQL configurada.
- Archivo `.env` configurado en la raíz del proyecto.

## Dependencias principales

Antes de iniciar el programa, se debe ejecutar `setup.py` para la instalación automática de los siguientes componentes.

- PySide6: interfaz gráfica.
- psycopg2-binary: conexión con PostgreSQL.

---

## Configuración del archivo .env

Desde esta versión, la conexión con la base de datos se configura mediante variables de entorno.

Crear un archivo `.env` en la raíz del proyecto con la siguiente estructura:

DB_HOST=host
DB_PORT=5432
DB_NAME=nombre_base_datos
DB_USER=usuario_postgres
DB_PASSWORD=contraseña_postgres

El archivo `.env` contiene información sensible y no debe subirse al repositorio.

---
## Novedades

- Re-escritura de código - Mucho más limpio y ordenado, cumple con lineamientos de código de calidad.
- Nuevas validaciones - El programa se asegura que el id sea numérico y el nombre no contenga números en el registro de estudiantes y profesores.

---

> Autores: Miguel Angel Mosquera, Junior Stiven Mejia, Santiago Marvin.
