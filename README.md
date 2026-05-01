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

Version 0.1.0 - Funciones de registro y consulta para usuarios administrativos.

Funciones integradas:
1. El usuario administrador puede registrar estudiantes, cursos y profesores.
2. El usuario administrador puede consultar datos de estudiantes, cursos y profesores.

# Versiones posteriores de desarrollo:

- 0.0.1 : Iniciar sesión.
- 0.0.2 : Registrar estudiantes.
- 0.0.3 : Consultar estudiantes.
- 0.0.4 : Registrar cursos.
- 0.0.5 : Consultar cursos.
- 0.0.6 : Registrar profesores.
- 0.0.7 : Consultar profesores.

---

> Autores: Miguel Angel Mosquera, Junior Stiven Mejia, Santiago Marvin.
