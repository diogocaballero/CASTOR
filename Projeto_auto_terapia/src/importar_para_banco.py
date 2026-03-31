import json
import sqlite3
import os

def importar_sistema_castor(caminho_json):
    # 1. Carregamos o JSON com todos os dados da Elizabeth e da Interface
    with open(caminho_json, 'r', encoding='utf-8') as f:
        dados = json.load(f)
    
    meta = dados['metadata']
    conn = sqlite3.connect('data/terapia.db')
    cursor = conn.cursor()
    
    # --- CRIAÇÃO DAS TABELAS (Estrutura Relacional) ---

    # TABELA MÃE: Cadastro da Sessão
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id_sessao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_crianca TEXT,
            data TEXT,
            duracao TEXT,
            arquivo_origem TEXT
        )
    ''')
    
    # TABELA FILHA 1: Sensor de Olhar (HuskyLens)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_olhos (
            id_leitura_olho INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER,
            timestamp TEXT,
            x REAL, y REAL, z REAL,
            id_persona TEXT,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao)
        )
    ''')

    # TABELA FILHA 2: Sensor Laser (Proximidade)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_laser (
            id_leitura_laser INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER,
            timestamp TEXT,
            distancia_mm REAL,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao)
        )
    ''')

    # TABELA FILHA 3: Logs da Interface Web (O que o terapeuta clicou)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs_interface (
            id_log INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER,
            timestamp TEXT,
            tipo_evento TEXT,
            acao TEXT,
            detalhe TEXT,
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao)
        )
    ''')

    # TABELA FILHA 4: Ações do Robô (O que o Castor fez fisicamente)
    # Aqui salvaremos se ele acenou, dançou ou qual MP3 tocou
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acoes_robo (
            id_acao_executada INTEGER PRIMARY KEY AUTOINCREMENT,
            id_sessao INTEGER,
            timestamp TEXT,
            categoria TEXT, -- Ex: 'Movimento', 'Fala', 'Emoção'
            nome_comando TEXT, -- Ex: 'wave', 'muito_bem.mp3', 'happy'
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao)
        )
    ''')

    # --- INSERÇÃO DOS DADOS ---

    # Insere a sessão e guarda o ID gerado
    cursor.execute('''
        INSERT INTO sessoes (id_crianca, data, duracao, arquivo_origem)
        VALUES (?, ?, ?, ?)
    ''', (meta['id_crianca'], meta['data'], meta['duracao_total'], os.path.basename(caminho_json)))
    
    id_sessao_atual = cursor.lastrowid

    # Importa Sensores (Olhar e Laser)
    for leitura in dados.get('dados_sensores', []):
        ts = leitura.get('timestamp')
        h = leitura.get('huskylens', {})
        cursor.execute('INSERT INTO sensor_olhos (id_sessao, timestamp, x, y, z, id_persona) VALUES (?,?,?,?,?,?)',
                       (id_sessao_atual, ts, h.get('x'), h.get('y'), h.get('z'), h.get('id')))
        cursor.execute('INSERT INTO sensor_laser (id_sessao, timestamp, distancia_mm) VALUES (?,?,?)',
                       (id_sessao_atual, ts, leitura.get('distancia', 0) * 10))

    # Importa Ações e Cliques (Tudo o que vem do acciones.py e da interface)
    for log in dados.get('logs_atividades', []):
        # Salvamos na tabela de interface
        cursor.execute('''
            INSERT INTO logs_interface (id_sessao, timestamp, tipo_evento, acao, detalhe)
            VALUES (?, ?, ?, ?, ?)
        ''', (id_sessao_atual, log.get('timestamp'), log.get('tipo'), log.get('acao'), log.get('valor')))
        
        # Se o evento for um comando de robô, salvamos também na tabela de ações
        if log.get('tipo') in ['Movimento', 'Fala', 'Emoção']:
            cursor.execute('''
                INSERT INTO acoes_robo (id_sessao, timestamp, categoria, nome_comando)
                VALUES (?, ?, ?, ?)
            ''', (id_sessao_atual, log.get('timestamp'), log.get('tipo'), log.get('acao')))
    
    conn.commit()
    conn.close()
    print(f"🚀 PROJETO INTEGRADO! Dados da criança {meta['id_crianca']} salvos no terapia.db")

if __name__ == "__main__":
    # Teste final com o seu JSON
    arquivo = 'data/sessao_65465465_151056.json' 
    if os.path.exists(arquivo):
        importar_sistema_castor(arquivo)
    else:
        print("Arquivo JSON não encontrado para teste.")