import sqlite3
import logging

# Configuração do sistema de logs para exibir o andamento no terminal
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def configurar_banco():
    conn = sqlite3.connect('data/terapia.db')
    cursor = conn.cursor()
    
    # Ativar suporte a Foreign Keys (Chaves Estrangeiras) no SQLite
    cursor.execute('PRAGMA foreign_keys = ON;')

    # 1. Tabela de Pacientes (Nova)
    # Guarda estritamente os dados de identidade de cada criança cadastrada
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE
        )
    ''')

    # 2. Tabela de Sessões (Atualizada)
    # id_paciente vincula a sessão à nova tabela de pacientes
    # nivel_interacao guardará o diagnóstico do algoritmo (baixa/media/alta)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id_sessao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER,
            nivel_interacao TEXT,
            data TEXT,
            duracao TEXT,
            arquivo_origem TEXT,
            FOREIGN KEY (id_paciente) REFERENCES pacientes (id_paciente) ON DELETE CASCADE
        )
    ''')
    
    # 3. Tabela do Sensor de Olhar (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_olhos (
            id_leitura_olho INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER, timestamp TEXT, x REAL, y REAL, z REAL, id_persona TEXT,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao) ON DELETE CASCADE
        )
    ''')
    
    # 4. Tabela do Sensor Laser (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_laser (
            id_leitura_laser INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER, timestamp TEXT, distancia_mm REAL,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao) ON DELETE CASCADE
        )
    ''')

    # 5. Tabela de Ações do Robô (Mantida)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acoes_robo (
            id_acao_executada INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER, timestamp TEXT, categoria TEXT, nome_comando TEXT,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao) ON DELETE CASCADE
        )
    ''')

    # Índices para otimização de performance nas buscas
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessao_laser ON sensor_laser(id_sessao)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessao_olhos ON sensor_olhos(id_sessao)')
    
    conn.commit()
    conn.close()
    logging.info("Estrutura do banco de dados verificada/criada com suporte relacional a pacientes.")

if __name__ == "__main__":
    configurar_banco()