import psycopg2

# Conexión via IPv4 Shared Pooler (compatible con redes sin IPv6)
DB_CONFIG = {
    "host":     "aws-0-us-west-2.pooler.supabase.com",
    "port":     6543,
    "database": "postgres",
    "user":     "postgres.wrlicucehfopryhguank",
    "password": "/y@z?Fp+@CT!89R",
}


def get_connection():
    """Retorna una conexión activa a la base de datos de Supabase."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(f"No se pudo conectar a la base de datos: {e}")
