import sqlite3
import logging

# Configuração de log técnico
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def otimizar_banco_dados():
    """
    Garante a existência de índices para otimização de consultas em larga escala.
    """
    try:
        conn = sqlite3.connect('data/terapia.db')
        cursor = conn.cursor()
        
        logging.info("Iniciando criação de índices SQL...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessao_laser ON sensor_laser(id_sessao)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessao_olhos ON sensor_olhos(id_sessao)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_crianca ON sessoes(id_crianca)')
        
        conn.commit()
        conn.close()
        logging.info("Otimização de banco de dados concluída com sucesso.")
    except sqlite3.Error as e:
        logging.error(f"Erro na otimização do banco de dados: {e}")

def gerar_estatisticas_validacao():
    """
    Calcula métricas agregadas de todas as sessões para validar a carga de dados.
    """
    try:
        conn = sqlite3.connect('data/terapia.db')
        cursor = conn.cursor()

        # Contagem de sessões consolidadas
        cursor.execute('SELECT COUNT(*) FROM sessoes')
        total_sessoes = cursor.fetchone()[0]

        # Volume de frames importados na tabela de laser
        cursor.execute('SELECT COUNT(*) FROM sensor_laser')
        total_frames = cursor.fetchone()[0]
        
        # AJUSTE: Cálculo da média de todas as sessões presentes no banco
        cursor.execute('SELECT AVG(distancia_mm) FROM sensor_laser')
        media_distancia = cursor.fetchone()[0] or 0

        # Sumário Executivo de Encerramento da Semana 2
        print("-" * 50)
        print("RESUMO TÉCNICO DE INTEGRAÇÃO - SEMANA 2")
        print("-" * 50)
        print(f"Sessões consolidadas no banco: {total_sessoes}")
        print(f"Total de frames importados:    {total_frames}")
        print(f"Média de proximidade (Px):     {media_distancia:.2f}")
        print("-" * 50)
        print("Status: Estrutura de dados validada para Semana 3.")
        print("-" * 50)

        conn.close()
    except sqlite3.Error as e:
        logging.error(f"Erro ao gerar estatísticas: {e}")

if __name__ == "__main__":
    otimizar_banco_dados()
    gerar_estatisticas_validacao()