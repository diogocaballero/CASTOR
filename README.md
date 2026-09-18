# Projeto Castor - Módulo Offline

Este projeto faz parte de uma pesquisa de Iniciação Científica na UFES, focada no desenvolvimento de um robô assistente para terapia infantil (Castor). O sistema utiliza dados de sensores (via ESP32) para monitorar o engajamento e a proximidade da criança durante as sessões clínicas.

Este repositório contém a **versão estática e offline** do projeto, responsável por importar logs, gerenciar o banco de dados e exibir o dashboard analítico, sem a necessidade de conexão direta com o hardware do robô.

## ⚙️ Como Rodar o Sistema

1. Acesse a pasta do projeto no seu terminal:
   ```bash
   cd Projeto_auto_terapia

   python -m pip install -r requirements.txt

   python -m streamlit run src/app.py

   Funcionalidades atuais:
   Dashboard Interativo: Visualização do nível de engajamento clínico (Alto, Médio, Baixo).
   Análise Laser: Gráfico de linha traçando a proximidade entre a criança e o robô ao longo do tempo.
   Exportação de Dados: Geração de arquivos CSV contendo os timestamps tratados.
   Notas Clínicas: Campo dedicado para o registro de observações por parte da terapeuta.

   Estrutura do repositorio

   📁 Projeto_auto_terapia/
├── 📁 data/                           # Diretório de armazenamento de logs e banco de dados
│   ├── 📄 frame_metrics.csv           
│   ├── 📄 frames_metrics2.csv         
│   ├── 📄 interaction_events.csv      
│   ├── 📄 session_summary_video1.json 
│   ├── 📄 session_summary_video2.json 
│   ├── 📄 terapia.db                  # Banco de dados SQLite principal
│   └── 📄 terapia1.db                

├── 📁 src/                            # Código-fonte da aplicação
│   ├── 📄 app.py                      # Ponto de entrada do dashboard Streamlit * 
│   ├── 📄 captura_sessao.py           #teste
│   ├── 📄 database_setup.py           # Configuração de tabelas do banco de dados *
│   ├── 📄 importador_real.py          #importa os dados para o banco
│   ├── 📄 importar_para_banco.py      # Rotina de injeção de dados no SQLite
│   ├── 📄 macaco.jpg                  #imagem da logo aleatorio
│   ├── 📄 semana_12.py                #apenas um verificação de dados de proximidade
│   └── 📄 verificar_dados.py          # Script de validação de integridade

├── 📁 venv/                           # Ambiente virtual Python[cite: 6]
├── 📄 .gitignore                      #[cite: 6]
├── 📄 requirements.txt                # Dependências do projeto[cite: 6]
└── 📄 README.md                       # Documentação do repositório[cite: 6]
