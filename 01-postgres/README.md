**Descripción**

El archivo docker-compose.yml define un entorno de desarrollo con:
- Un contenedor de PostgreSQL con soporte para pgvector
- Un contenedor de pgAdmin para gestionar la base de datos

**Uso**

Para iniciar el entorno, abrir una ventana de comandos y ejecutar:

```bash
docker compose up -d
```

Para detener el entorno, abrir una ventana de comandos y ejecutar:

```bash
docker compose down
```

**Instalación de pgvector**

Ingrese a pgadmin utilizando: http://localhost:8080, utilizando las credenciales:
Email: demo@acme.com
Password: demo

En pgAdmin, haga clic derecho sobre "Servers" y seleccione "Register" > "Server...".
En la pestaña "General", dé un nombre a su servidor (por ejemplo, "Local PostgreSQL with pgvector").
En la pestaña "Connection":
Host name/address: postgres (Este es el nombre del servicio definido en docker-compose.yml)
Port: 5432
Maintenance database: dbtest
Username: postgres
Password: postgres
Click "Save".

Una vez conectado en pgAdmin, abra una herramienta de consulta para su base de datos y ejecute:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Si todo se ejecuta correctamente, PostgreSQL tebdrá la extensión pgvector.

**Conexión a la base de datos desde fuera de Docker**

Para conectarse a la base de datos desde fuera de Docker se debe ingresar las siguientes credenciales:

Hostname: localhost
Port: 5432
Database: dbtest
Username: postgres
Password: postgres

