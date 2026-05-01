# Cambridge-Academy

El proyecto consiste en el desarrollo de un sistema de gestión académica para Cambridge Academy, con el objetivo de digitalizar y automatizar los procesos de inscripción de estudiantes, administración de cursos y profesores, control de pagos, generación de reportes y gestión de accesos.

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

---

## Requisitos

- Python 3.10 o superior. (pip incluido)
- PostgreSQL instalado y en ejecución.
- Sistema operativo Windows, Linux o macOS.
- Conexión a una base de datos PostgreSQL configurada.

## Dependencias principales

Antes de iniciar el programa, se debe ejecutar `setup.py` para la instalación automática de los siguientes componentes.

- PySide6: interfaz gráfica.
- psycopg2-binary: conexión con PostgreSQL.

---

## Detalles de desarrollo

Version 0.2.0 - Funciones de modificación, eliminación y búsqueda para usuarios administrativos.

Esta versión completa la gestión administrativa de estudiantes, cursos y profesores, extendiendo las funcionalidades de registro y consulta desarrolladas en la versión 0.1.0.

Funciones integradas:

1. El usuario administrador puede modificar datos de estudiantes.
2. El usuario administrador puede eliminar datos de estudiantes.
3. El usuario administrador puede buscar estudiantes por nombre.
4. El usuario administrador puede modificar datos de cursos.
5. El usuario administrador puede eliminar datos de cursos.
6. El usuario administrador puede buscar cursos por nombre.
7. El usuario administrador puede modificar datos de profesores.
8. El usuario administrador puede eliminar datos de profesores.
9. El usuario administrador puede buscar profesores por nombre.

Historias de usuario implementadas:

- HU-03: Modificar datos de estudiantes.
- HU-04: Eliminar datos de estudiantes.
- HU-05: Buscar estudiantes por nombre.
- HU-08: Modificar datos de cursos.
- HU-09: Eliminar datos de cursos.
- HU-10: Buscar cursos por nombre.
- HU-13: Modificar datos de profesores.
- HU-14: Eliminar datos de profesores.
- HU-15: Buscar profesores por nombre.

# Versiones posteriores de desarrollo:

- 0.1.0 : Registro y consulta de estudiantes, cursos y profesores.
- 0.1.1 : Modificar estudiantes.
- 0.1.2 : Eliminar estudiantes.
- 0.1.3 : Buscar estudiantes.
- 0.1.4 : Modificar cursos.
- 0.1.5 : Eliminar cursos.
- 0.1.6 : Buscar cursos
- 0.1.7 : Modificar profesores.
- 0.1.8 : Eliminar profesores.
- 0.1.9 : Buscar profesores.

---

> Autores: Miguel Angel Mosquera, Junior Stiven Mejia, Santiago Marvin.
