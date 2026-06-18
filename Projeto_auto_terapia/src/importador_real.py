# Importa o módulo sqlite3 para abrir, ler e escrever no banco de dados local
import sqlite3
# Importa o pandas para fazer a leitura rápida e em massa dos ficheiros CSV pesados
import pandas as pd
# Importa o módulo json para abrir e interpretar a estrutura dos relatórios JSON
import json
# Importa o módulo os para verificar se os ficheiros existem no disco e extrair nomes
import os
# Importa o datetime para capturar e formatar a data atual do dia da importação
from datetime import datetime
# Importa o logging para exibir mensagens organizadas de sucesso ou falha no terminal
import logging
# Importa a função configurar_banco do database_setup.py para garantir as tabelas prontas
from database_setup import configurar_banco

# Define o formato padrão dos logs para mostrar o tipo da mensagem e o texto explicativo
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def importar_dados_reais() -> None:
    # Executa a função do outro arquivo para criar o banco e as tabelas caso não existam
    configurar_banco()
    
    # Cria a lista de dicionários mapeando os caminhos de cada sessão que temos na pasta data
    # Adicionamos o campo "nome_paciente" para alimentar de forma limpa a nova tabela relacional
    lista_sessoes = [
        {
            # Caminho do JSON de metadados da primeira sessão longa
            "json": 'data/session_summary_video1.json',
            # Caminho do CSV de eventos de engajamento da primeira sessão
            "eventos": 'data/interaction_events.csv',
            # Caminho do CSV de métricas de frames e sensores da primeira sessão
            "metricas": 'data/frame_metrics.csv',
            # Nome real do paciente que será verificado/cadastrado no banco
            "nome_paciente": "Daniel",
            # Nome alternativo caso o arquivo não possua nota interna para cálculo
            "default_label": "Sessão 01"
        },
        {
            # Caminho do JSON de metadados da nova sessão curta
            "json": 'data/session_summary_video2.json',
            # Definido como None pois os eventos da sessão 2 estão embutidos no próprio JSON
            "eventos": None,
            # Caminho do CSV de métricas de frames e sensores da segunda sessão
            "metricas": 'data/frames_metrics2.csv',
            # Nome real do paciente que será verificado/cadastrado no banco
            "nome_paciente": "Daniel",
            # Nome alternativo caso o arquivo não possua nota interna para cálculo
            "default_label": "Sessão 02"
        }
    ]

    # Conecta ao arquivo de banco de dados SQLite localizado na pasta data
    conn = sqlite3.connect('data/terapia.db')
    # Inicializa o cursor que serve para executar os comandos SQL dentro da transação
    cursor = conn.cursor()

    try:
        # Inicia o loop para processar uma sessão por vez de forma isolada e organizada
        for sessao in lista_sessoes:
            # Verifica se os ficheiros fundamentais da sessão atual existem na pasta física
            if not os.path.exists(sessao["json"]) or not os.path.exists(sessao["metricas"]):
                # Caso falte algum ficheiro, exibe um erro no console e pula para a próxima sessão
                logging.error(f"Ficheiros de métricas/JSON não encontrados para {sessao['default_label']}. A saltar...")
                # Comando que força o loop a ignorar o resto deste bloco e ir para o próximo item
                continue

            # Isola apenas o nome do ficheiro JSON final para usar como identificador único
            nome_arquivo = os.path.basename(sessao["json"])

            # --- TRAVA ANTI-DUPLICADOS ---
            # Executa uma busca na tabela de sessoes procurando pelo nome do arquivo de origem
            cursor.execute("SELECT id_sessao FROM sessoes WHERE arquivo_origem = ?", (nome_arquivo,))
            # Guarda o resultado da consulta na variável resultado
            resultado = cursor.fetchone()

            # Condicional que valida se o arquivo já foi importado em execuções anteriores
            if resultado:
                # Exibe um log informativo no console avisando que a sessão já está guardada
                logging.info(f"ℹ️ A sessão do ficheiro {nome_arquivo} já existe no banco (ID: {resultado[0]}). A saltar...")
                # Interrompe o processo desta sessão específica para evitar dados repetidos
                continue
            # -----------------------------

            # --- GERENCIAMENTO RELACIONAL DO PACIENTE ---
            nome_paciente = sessao["nome_paciente"]
            # Consulta se o nome do paciente mapeado já existe na base de dados
            cursor.execute("SELECT id_paciente FROM pacientes WHERE nome = ?", (nome_paciente,))
            registro_paciente = cursor.fetchone()

            if registro_paciente:
                # Se o paciente já existir, reaproveita o ID dele para criar o elo
                id_paciente_atual = registro_paciente[0]
            else:
                # Se for a primeira vez do paciente, faz o cadastro dinâmico dele na tabela própria
                cursor.execute("INSERT INTO pacientes (nome) VALUES (?)", (nome_paciente,))
                # Captura o ID incremental gerado na hora pelo SQLite para este novo paciente
                id_paciente_atual = cursor.lastrowid
            # ---------------------------------------------

            # 1. PROCESSAR METADADOS (JSON)
            # Abre o ficheiro JSON em modo de leitura garantindo suporte a acentuação com utf-8
            with open(sessao["json"], 'r', encoding='utf-8') as f:
                # Converte o conteúdo de texto do ficheiro em um dicionário Python nativo
                resumo = json.load(f)

            # --- CÁLCULO / CLASSIFICAÇÃO CLÍNICA AUTOMÁTICA DO ENGAJAMENTO ---
            # Extrai o sub-dicionário 'metrics' caso ele exista (comum no formato da Sessão 2)
            metrics_dict = resumo.get('metrics', {})
            
            # Varre o JSON buscando a nota por todas as chaves possíveis dos dois formatos
            score_global = metrics_dict.get('score_global_0_100') or resumo.get('score_global_0_100') or resumo.get('mean_frame_score')

            # Verifica se alguma das chaves numéricas de score foi encontrada com sucesso
            if score_global is not None:
                # Converte o valor capturado para float para permitir comparações decimais exatas
                score_num = float(score_global)
                
                # Regra de corte 1: Se o score for exatamente zero, a interação foi nula
                if score_num == 0:
                    nivel_interacao = "nula"
                # Regra de corte 2: Se a nota for até 35, classifica como baixa interação
                elif score_num <= 35:
                    nivel_interacao = "baixa"
                # Regra de corte 3: Se a nota for até 70, classifica como média interação
                elif score_num <= 70:
                    nivel_interacao = "media"
                # Regra de corte 4: Se passar de 70, classifica o engajamento clínico como alto
                else:
                    nivel_interacao = "alta"
            else:
                # Caso seja um ficheiro sem score, busca a chave 'session_label' ou adota o padrão
                nivel_interacao = resumo.get('session_label', "baixa")
            # -----------------------------------------------------------------

            # Captura a duração total adaptando para as diferentes chaves de tempo e formata com 2 casas
            duracao_total = f"{resumo.get('duration_sec', metrics_dict.get('tempo_total_s', 0)):.2f}s"
            
            # Prepara a instrução SQL atualizada para salvar a sessão apontando para o id_paciente e o nível calculado
            cursor.execute('''
                INSERT INTO sessoes (id_paciente, nivel_interacao, data, duracao, arquivo_origem)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_paciente_atual, nivel_interacao, datetime.now().strftime("%d/%m/%Y"), duracao_total, nome_arquivo))
            
            # Recupera o ID numérico incremental gerado automaticamente pelo banco de dados para esta sessão
            id_sessao_atual = cursor.lastrowid

            # 2. IMPORTAR EVENTOS DE INTERAÇÃO (TABELA ACOES_ROBO)
            # Condicional que checa se existe um ficheiro CSV de eventos dedicado para a sessão
            if sessao["eventos"] and os.path.exists(sessao["eventos"]):
                # Faz a leitura do CSV de eventos mapeando as colunas via pandas
                df_eventos = pd.read_csv(sessao["eventos"])
                # Estrutura uma lista de tuplas associando cada linha do CSV ao ID da sessão atual
                eventos_data = [
                    (id_sessao_atual, str(row['start_time_sec']), 'Engajamento', row['label'])
                    for _, row in df_eventos.iterrows()
                ]
            else:
                # Caso não tenha CSV, faz a varredura da lista embutida na chave 'events' do JSON
                eventos_json = resumo.get('events', [])
                # Estrutura a lista de tuplas puxando os tempos e tipos de eventos diretamente do JSON
                eventos_data = [
                    (id_sessao_atual, str(ev.get('start_sec')), 'Engajamento', ev.get('event_type'))
                    for ev in eventos_json
                ]
            
            # Insere todos os eventos mapeados de uma única vez no banco para ganho de velocidade
            cursor.executemany('INSERT INTO acoes_robo (id_sessao, timestamp, categoria, nome_comando) VALUES (?,?,?,?)', eventos_data)

            # 3. CARREGAR MÉTRICAS DOS SENSORES (TABELAS SENSOR_OLHOS E SENSOR_LASER)
            # Lê o arquivo CSV pesado frame a frame jogando os dados para a memória
            df_metrics = pd.read_csv(sessao["metricas"])

            # Descobre dinamicamente se a coluna de distância se chama 'body_to_castor_distance_cm' ou 'min_person_to_castor_px'
            col_dist = 'body_to_castor_distance_cm' if 'body_to_castor_distance_cm' in df_metrics.columns else 'min_person_to_castor_px'
            # Descobre dinamicamente se a coluna de tempo se chama 'timestamp_sec' ou 'time_sec'
            col_time = 'timestamp_sec' if 'timestamp_sec' in df_metrics.columns else 'time_sec'

            # Cria a lista de tuplas para inserção do olhar com os eixos X, Y, Z zerados por padrão
            olhos_data = [
                (id_sessao_atual, str(row[col_time]), 0.0, 0.0, 0.0, 'Criança')
                for _, row in df_metrics.iterrows()
            ]
            
            # Cria a lista de tuplas para a tabela do laser puxando o tempo e a distância dinâmica calculada
            laser_data = [
                (id_sessao_atual, str(row[col_time]), row[col_dist])
                for _, row in df_metrics.iterrows()
            ]

            # Grava as milhares de linhas do olhar de uma vez utilizando a técnica de inserção em massa
            cursor.executemany('INSERT INTO sensor_olhos (id_sessao, timestamp, x, y, z, id_persona) VALUES (?,?,?,?,?,?)', olhos_data)
            # Grava as milhares de linhas de distância do laser de uma vez na tabela correspondente
            cursor.executemany('INSERT INTO sensor_laser (id_sessao, timestamp, distancia_mm) VALUES (?,?,?)', laser_data)

            # Printa uma mensagem de sucesso no console exibindo o diagnóstico clínico e o nome relacional do paciente
            logging.info(f"✅ Sucesso! {nome_arquivo} cadastrado para o paciente '{nome_paciente}' com o nível calculado: '{nivel_interacao}' (ID Interno: {id_sessao_atual}).")

        # Finaliza a transação salvando definitivamente todas as inserções no arquivo fisica do banco .db
        conn.commit()

    except Exception as e:
        # Se ocorrer qualquer erro técnico ou travamento durante o loop, entra em ação o plano de segurança
        conn.rollback()
        # Cancela tudo o que foi feito na execução atual para não deixar dados quebrados ou parciais
        logging.error(f"Falha na importação: {e}")
    finally:
        # Garante o encerramento seguro da comunicação com o banco eliminando conexões pendentes
        conn.close()

# Bloco padrão do Python que assegura que a função só será disparada se o arquivo for executado diretamente
if __name__ == "__main__":
    importar_dados_reais()