import json
import time
from datetime import datetime

def iniciar_sessao():
    id_crianca = input("Digite o ID da criança/turma: ")
    print(f"\n--- Sessão iniciada para {id_crianca} ---")
    
    inicio = datetime.now()
    leituras_sensores = []
    logs_atividades = []

    # Simulação de captura (Enquanto o terapeuta não encerra)
    try:
        print("Capturando dados... (Pressione Ctrl+C para encerrar a sessão)")
        while True:
            # Simulando dados vindo dos sensores
            dado_atual = {
                "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
                "huskylens": {"id": 1, "status": "olhando"}, # Exemplo
                "velostat": 512,
                "distancia": 25.4
            }
            leituras_sensores.append(dado_atual)
            
            time.sleep(1) # Captura a cada 1 segundo
            print(".", end="", flush=True)
            
    except KeyboardInterrupt:
        fim = datetime.now()
        duracao = str(fim - inicio).split(".")[0] # Formato HH:MM:SS
        print(f"\n\n--- Sessão Finalizada ---")
        print(f"Duração: {duracao}")

    # O "Pulo do Gato" da María: Salvar ou Descartar?
    escolha = input("\nDeseja SALVAR esta sessão? (s/n): ").lower()
    
    if escolha == 's':
        dados_finais = {
            "metadata": {
                "id_crianca": id_crianca,
                "data": inicio.strftime("%d/%m/%Y"),
                "hora_inicio": inicio.strftime("%H:%M:%S"),
                "hora_fim": fim.strftime("%H:%M:%S"),
                "duracao_total": duracao
            },
            "dados_sensores": leituras_sensores
        }
        
        nome_arquivo = f"data/sessao_{id_crianca}_{inicio.strftime('%H%M%S')}.json"
        with open(nome_arquivo, 'w', encoding='utf-8') as f:
            json.dump(dados_finais, f, indent=4, ensure_ascii=False)
        print(f"✅ Sucesso! Arquivo {nome_arquivo} gerado.")
    else:
        print("⚠️ Sessão descartada. Nenhum arquivo foi gerado.")

if __name__ == "__main__":
    iniciar_sessao()