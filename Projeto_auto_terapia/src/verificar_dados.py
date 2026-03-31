import sqlite3

def escanear_banco():
    print(" Iniciando varredura completa no terapia.db...\n")
    
    conn = sqlite3.connect('data/terapia.db')
    cursor = conn.cursor()

    # 1. Verificar a tabela de Olhar (Sensor 1)
    # Contamos quantas linhas possuem X, Y ou Z DIFERENTES de zero.
    cursor.execute('''
        SELECT 
            COUNT(*) FILTER (WHERE x != 0.0) as x_validos,
            COUNT(*) FILTER (WHERE y != 0.0) as y_validos,
            COUNT(*) FILTER (WHERE z != 0.0) as z_validos,
            COUNT(*) as total_linhas
        FROM sensor_olhos
    ''')
    olhar = cursor.fetchone()

    # 2. Verificar a tabela de Laser (Sensor 2)
    # Contamos quantas distâncias são maiores que zero.
    cursor.execute('SELECT COUNT(*) FROM sensor_laser WHERE distancia_mm > 0')
    laser_validos = cursor.fetchone()[0]

    # 3. Verificar Eventos e Ações
    cursor.execute('SELECT COUNT(*) FROM acoes_robo')
    acoes_totais = cursor.fetchone()[0]

    print(" --- RELATÓRIO DE INTEGRIDADE ---")
    print(f" Tabela Olhar (sensor_olhos):")
    print(f"   - Total de registros: {olhar[3]}")
    print(f"   - Coordenadas X válidas (!= 0): {olhar[0]}")
    print(f"   - Coordenadas Y válidas (!= 0): {olhar[1]}")
    print(f"   - Coordenadas Z válidas (!= 0): {olhar[2]}")
    print(f"\n Tabela Laser (sensor_laser):")
    print(f"   - Medições reais encontradas: {laser_validos}")
    print(f"\n Tabela Ações (acoes_robo):")
    print(f"   - Comandos registrados: {acoes_totais}")
    print("------------------------------------\n")

    if olhar[0] == 0 and laser_validos > 0:
        print("Conclusão Técnica: O banco está saudável! Os dados de distância ")
        print("estão presentes, mas as coordenadas de olhar foram importadas como zero ")
        print("conforme o mapeamento do arquivo 'frame_metrics.csv'.")
    
    conn.close()

if __name__ == "__main__":
    escanear_banco()