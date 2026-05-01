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

Version 0.3.0 - Funciones del módulo estudiante, inscripción, pagos y seguridad de cuenta.

Esta versión introduce las funcionalidades principales del usuario estudiante y amplía el sistema con procesos de inscripción, generación de recibos, pagos simulados, consulta financiera y cambio de contraseña.

Funciones integradas:

1. El usuario estudiante puede visualizar los cursos disponibles.
2. El usuario estudiante puede visualizar los cursos en los que está inscrito.
3. El usuario estudiante puede consultar información detallada de los cursos.
4. El usuario estudiante puede solicitar inscripción a un curso disponible.
5. El sistema genera un recibo pendiente asociado a la inscripción.
6. El usuario estudiante puede pagar un recibo pendiente para confirmar la inscripción.
7. El usuario estudiante puede consultar su historial de pagos.
8. El usuario administrador puede consultar los pagos realizados por estudiantes.
9. El usuario autenticado puede cambiar su contraseña.

Historias de usuario implementadas:

- HU-18: Visualizar cursos disponibles.
- HU-19: Visualizar cursos inscritos.
- HU-20: Consultar datos de los cursos.
- HU-21: Inscribirme en un curso disponible.
- HU-22: Consultar historial de pagos.
- HU-16: Consultar pagos de estudiantes.
- HU-30: Cambiar contraseña.

# Versiones posteriores de desarrollo:

- 0.1.0 : Registro y consulta de estudiantes, cursos y profesores.
- 0.2.0 : Modificación, eliminación y búsqueda de estudiantes, cursos y profesores.
- 0.2.1 : Cursos disponibles
- 0.2.2 : Cursos inscritos
- 0.2.3 : Consultar cursos
- 0.2.4 : Inscribir curso
- 0.2.5 : Consultar pagos
- 0.2.6 : Consultar pagos como administrador
- 0.2.7 : Cambiar contraseña

---

> Autores: Miguel Angel Mosquera, Junior Stiven Mejia, Santiago Marvin.
