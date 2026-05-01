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

## Detalles de desarrollo

Version 0.4.0 - Funciones del módulo profesor y control académico de notas.

Esta versión integra el rol profesor y completa el flujo académico relacionado con la gestión de calificaciones. También permite que estudiantes y administradores consulten registros académicos desde sus respectivos perfiles.

Funciones integradas:

1. El usuario profesor puede consultar los cursos que tiene asignados.
2. El usuario profesor puede consultar el detalle de sus cursos asignados.
3. El usuario profesor puede registrar notas de estudiantes inscritos.
4. El usuario profesor puede consultar el registro de notas de sus cursos.
5. El usuario profesor puede modificar notas previamente registradas.
6. El usuario estudiante puede consultar su registro de notas.
7. El usuario administrador puede consultar el registro de notas por estudiante.
8. El sistema valida el rango de notas académicas entre 0.0 y 5.0.
9. El sistema calcula el promedio y el estado académico del estudiante.

Historias de usuario implementadas:

- HU-24: Consultar cursos asignados.
- HU-25: Consultar datos de cursos asignados.
- HU-26: Registrar notas de cada estudiante.
- HU-27: Consultar registro de notas.
- HU-28: Modificar notas de estudiantes.
- HU-23: Consultar registro de notas.
- HU-17: Consultar registro de notas por estudiante.

# Versiones posteriores de desarrollo:

- 0.1.0 : Registro y consulta de estudiantes, cursos y profesores.
- 0.2.0 : Modificación, eliminación y búsqueda de estudiantes, cursos y profesores.
- 0.3.0 : Módulo estudiante, inscripción, pagos y cambio de contraseña.
- 0.3.1 : Resumen cursos
- 0.3.2 : Detalles cursos
- 0.3.3 : Registrar notas
- 0.3.4 : Consultar notas
- 0.3.5 : Modificar notas
- 0.3.6 : Consultar notas como estudiante
- 0.3.7 : Consultar notas como administrador

---

> Autores: Miguel Angel Mosquera, Junior Stiven Mejia, Santiago Marvin.
