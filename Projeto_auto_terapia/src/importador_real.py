import sqlite3     # Biblioteca para gerenciar o Banco de Dados SQL (o arquivo .db)
import pandas as pd # A ferramenta principal para ler e manipular tabelas (CSVs)
import json        # Para ler o arquivo de resumo que a Elizabeth mandou
import os          # Para verificar se os arquivos existem na pasta 'data'
from datetime import datetime # Para registrar automaticamente a data da importação

def importar_dados_reais():
    print(" Iniciando a integração dos dados reais...")
    
    # 1. CONEXÃO: Abre o banco de dados. Se o arquivo não existir, ele cria um novo.
    conn = sqlite3.connect('data/terapia.db')
    cursor = conn.cursor()

    # --- PASSO 2: CRIAÇÃO DAS TABELAS (O "Esqueleto" do Banco) ---
    # Usamos 'IF NOT EXISTS' para o código não dar erro se você rodar o script várias vezes.
    
    # Tabela principal com os dados da criança e da sessão
    cursor.execute('CREATE TABLE IF NOT EXISTS sessoes (id_sessao INTEGER PRIMARY KEY AUTOINCREMENT, id_crianca TEXT, data TEXT, duracao TEXT, arquivo_origem TEXT)')
    
    # Tabela para os dados de olhar (Sensor 1)
    cursor.execute('CREATE TABLE IF NOT EXISTS sensor_olhos (id_leitura_olho INTEGER PRIMARY KEY AUTOINCREMENT, id_sessao INTEGER, timestamp TEXT, x REAL, y REAL, z REAL, id_persona TEXT, FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao))')
    
    # Tabela para a distância do laser (Sensor 2)
    cursor.execute('CREATE TABLE IF NOT EXISTS sensor_laser (id_leitura_laser INTEGER PRIMARY KEY AUTOINCREMENT, id_sessao INTEGER, timestamp TEXT, distancia_mm REAL, FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao))')
    
    # Tabela para os comandos e movimentos do robô Castor
    cursor.execute('CREATE TABLE IF NOT EXISTS acoes_robo (id_acao_executada INTEGER PRIMARY KEY AUTOINCREMENT, id_sessao INTEGER, timestamp TEXT, categoria TEXT, nome_comando TEXT, FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao))')

    # --- PASSO 3: PROCESSAR O RESUMO DA SESSÃO (JSON) ---
    caminho_json = 'data/session_summary_video1.json'
    with open(caminho_json, 'r', encoding='utf-8') as f:
        resumo = json.load(f) # Transforma o arquivo JSON em um dicionário do Python
    
    # Mapeamento: Usamos 'session_label' como o ID (ex: 'baixa' interacao) e pegamos a duração
    child_id = resumo.get('session_label', 'Sessao_Real')
    data_sessao = datetime.now().strftime("%d/%m/%Y") # Pega a data de hoje
    duracao_total = f"{resumo.get('duration_sec', 0):.2f}s"

    # Inserimos a sessão e guardamos o ID gerado (id_sessao_atual)
    cursor.execute('''
        INSERT INTO sessoes (id_crianca, data, duracao, arquivo_origem)
        VALUES (?, ?, ?, ?)
    ''', (child_id, data_sessao, duracao_total, os.path.basename(caminho_json)))
    
    # O 'lastrowid' é fundamental: ele é o link (clip de papel) que une os CSVs a esta sessão
    id_sessao_atual = cursor.lastrowid

    # --- PASSO 4: PROCESSAR EVENTOS DE INTERAÇÃO (CSV de Eventos) ---
    caminho_eventos = 'data/interaction_events.csv'
    if os.path.exists(caminho_eventos):
        df_eventos = pd.read_csv(caminho_eventos) # O Pandas lê o CSV como uma planilha
        for _, row in df_eventos.iterrows():
            # Mapeamos 'start_time_sec' para o nosso campo 'timestamp'
            # E 'label' (baixa/media/alta) para o nome da ação
            cursor.execute('''
                INSERT INTO acoes_robo (id_sessao, timestamp, categoria, nome_comando)
                VALUES (?, ?, ?, ?)
            ''', (id_sessao_atual, str(row['start_time_sec']), 'Engajamento', row['label']))
        print(f" {len(df_eventos)} eventos de interação importados.")

    # --- PASSO 5: PROCESSAR MÉTRICAS DE SENSORES (CSV de Frames) ---
    caminho_metricas = 'data/frame_metrics.csv'
    if os.path.exists(caminho_metricas):
        df_metrics = pd.read_csv(caminho_metricas)
        # Este CSV tem milhares de linhas (uma para cada frame do vídeo)
        for _, row in df_metrics.iterrows():
            # Mapeamos 'time_sec' para saber o tempo exato de cada leitura
            cursor.execute('''
                INSERT INTO sensor_olhos (id_sessao, timestamp, x, y, z, id_persona)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (id_sessao_atual, str(row['time_sec']), 0.0, 0.0, 0.0, 'Criança'))
            
            # Aqui salvamos a distância medida (min_person_to_castor_px)
            cursor.execute('''
                INSERT INTO sensor_laser (id_sessao, timestamp, distancia_mm)
                VALUES (?, ?, ?)
            ''', (id_sessao_atual, str(row['time_sec']), row['min_person_to_castor_px']))
        print(f" {len(df_metrics)} frames de métricas integrados.")

    # 6. FINALIZAÇÃO: Salva as mudanças no arquivo 'terapia.db'
    conn.commit()
    conn.close()
    print(f" TUDO CERTO! A sessão '{child_id}' agora faz parte do seu banco de dados.")

if __name__ == "__main__":
    importar_dados_reais()