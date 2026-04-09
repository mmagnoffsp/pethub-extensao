import psycopg2

def get_connection():
    # Sua chave real da Neon aplicada aqui:
    conn = psycopg2.connect("postgresql://neondb_owner:npg_LCNw24mZijge@ep-royal-bread-aclyobrp-pooler.sa-east-1.aws.neon.tech/neondb?sslmode=require")
    return conn

def criar_tabela():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pets (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            especie TEXT NOT NULL,
            idade INTEGER NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()