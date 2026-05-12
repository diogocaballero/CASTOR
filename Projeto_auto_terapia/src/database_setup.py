import sqlite3
import logging

def configurar_banco():
    conn = sqlite3.connect('data/terapia.db')
    cursor = conn.cursor()
    
    # Ativar suporte a Foreign Keys
    cursor.execute('PRAGMA foreign_keys = ON;')

    # Tabela de Sessões
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id_sessao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_crianca TEXT,
            data TEXT,
            duracao TEXT,
            arquivo_origem TEXT
        )
    ''')
    
    # Tabelas de Sensores e Ações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_olhos (
            id_leitura_olho INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER, timestamp TEXT, x REAL, y REAL, z REAL, id_persona TEXT,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_laser (
            id_leitura_laser INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER, timestamp TEXT, distancia_mm REAL,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acoes_robo (
            id_acao_executada INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER, timestamp TEXT, categoria TEXT, nome_comando TEXT,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao) ON DELETE CASCADE
        )
    ''')

    # Índices para Performance (Semana 3)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessao_laser ON sensor_laser(id_sessao)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessao_olhos ON sensor_olhos(id_sessao)')
    
    conn.commit()
    conn.close()
    logging.info("Estrutura do banco de dados verificada/criada.")

if __name__ == "__main__":
    configurar_banco()