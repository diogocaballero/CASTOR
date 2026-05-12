import sqlite3
import pandas as pd
import json
import os
from datetime import datetime
import logging
from database_setup import configurar_banco

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def importar_dados_reais():
    # Garante que as tabelas existem
    configurar_banco()
    
    caminho_json = 'data/session_summary_video1.json'
    caminho_eventos = 'data/interaction_events.csv'
    caminho_metricas = 'data/frame_metrics.csv'

    if not all(os.path.exists(f) for f in [caminho_json, caminho_eventos, caminho_metricas]):
        logging.error("Arquivos necessários não encontrados na pasta /data.")
        return

    conn = sqlite3.connect('data/terapia.db')
    cursor = conn.cursor()

    try:
        # 1. Processar JSON (Metadados)
        with open(caminho_json, 'r', encoding='utf-8') as f:
            resumo = json.load(f)
        
        child_id = resumo.get('session_label', 'Sessao_Real')
        duracao_total = f"{resumo.get('duration_sec', 0):.2f}s"
        
        cursor.execute('''
            INSERT INTO sessoes (id_crianca, data, duracao, arquivo_origem)
            VALUES (?, ?, ?, ?)
        ''', (child_id, datetime.now().strftime("%d/%m/%Y"), duracao_total, os.path.basename(caminho_json)))
        
        id_sessao_atual = cursor.lastrowid

        # 2. Importar Eventos (CSV) - Usando executemany para ser mais rápido
        df_eventos = pd.read_csv(caminho_eventos)
        eventos_data = [
            (id_sessao_atual, str(row['start_time_sec']), 'Engajamento', row['label'])
            for _, row in df_eventos.iterrows()
        ]
        cursor.executemany('INSERT INTO acoes_robo (id_sessao, timestamp, categoria, nome_comando) VALUES (?,?,?,?)', eventos_data)

        # 3. Importar Métricas (CSV Pesado) - Otimização Máxima
        df_metrics = pd.read_csv(caminho_metricas)
        
        # Preparamos listas de tuplas para inserção em massa
        olhos_data = [
            (id_sessao_atual, str(row['time_sec']), 0.0, 0.0, 0.0, 'Criança')
            for _, row in df_metrics.iterrows()
        ]
        
        laser_data = [
            (id_sessao_atual, str(row['time_sec']), row['min_person_to_castor_px'])
            for _, row in df_metrics.iterrows()
        ]

        cursor.executemany('INSERT INTO sensor_olhos (id_sessao, timestamp, x, y, z, id_persona) VALUES (?,?,?,?,?,?)', olhos_data)
        cursor.executemany('INSERT INTO sensor_laser (id_sessao, timestamp, distancia_mm) VALUES (?,?,?)', laser_data)

        conn.commit() # Salva tudo de uma vez (Transaction)
        logging.info(f"Sucesso! {len(df_metrics)} frames importados para a sessão {id_sessao_atual}.")

    except Exception as e:
        conn.rollback() # Se der erro em qualquer parte, desfaz tudo para não sujar o banco
        logging.error(f"Falha na importação: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    importar_dados_reais()