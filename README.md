Projeto Castor — Módulo Offline



Este projeto faz parte de uma pesquisa de Iniciação Científica da
Universidade Federal do Espírito Santo (UFES), voltada ao desenvolvimento
do robô assistente para terapia infantil Castor.

O Módulo Offline corresponde à versão do sistema responsável pelo
processamento e análise dos dados das sessões sem necessidade de conexão
direta com o hardware do robô.

O sistema permite importar logs previamente registrados, armazená-los em
um banco de dados SQLite e disponibilizar as informações por meio de um
dashboard analítico desenvolvido em Streamlit.



⚙️ Como executar

Acesse a pasta do projeto:

cd Projeto_auto_terapia

Instale as dependências:

python -m pip install -r requirements.txt

Execute o dashboard:

python -m streamlit run src/app.py

Após a execução, o Streamlit disponibilizará o dashboard para visualização
dos dados das sessões.



🔄 Fluxo do sistema

O funcionamento do módulo offline segue o fluxo:

Logs das sessões
       ↓
importador_real.py
       ↓
Banco de dados SQLite
       ↓
terapia.db
       ↓
app.py / Streamlit
       ↓
Dashboard analítico
       ↓
Gráficos, indicadores e notas clínicas



📊 Funcionalidades atuais

Dashboard Interativo

Visualização das informações das sessões e do nível de engajamento
classificado em:

Alto

Médio

Baixo

Análise de Proximidade

Visualização da distância entre a criança e o robô ao longo da sessão
por meio de gráfico de linha baseado nos dados do sensor laser.

Exportação de Dados

Geração de arquivos CSV contendo os dados tratados e seus respectivos
timestamps.

Notas Clínicas

Campo destinado ao registro de observações realizadas pela terapeuta
durante a análise da sessão.



📁 Estrutura do repositório

Projeto_auto_terapia/
│
├── data/

│   ├── frame_metrics.csv

│   ├── frames_metrics2.csv

│   ├── interaction_events.csv

│   ├── session_summary_video1.json

│   ├── session_summary_video2.json

│   ├── terapia.db

│   └── terapia1.db
│
├── src/
│   ├── app.py

│   ├── captura_sessao.py

│   ├── database_setup.py

│   ├── importador_real.py

│   ├── importar_para_banco.py

│   ├── macaco.jpg

│   ├── semana_12.py

│   └── verificar_dados.py
│
├── venv/

├── .gitignore

├── requirements.txt

└── README.md



🧩 Principais arquivos

Arquivo

Função

app.py

Ponto de entrada do dashboard Streamlit

database_setup.py

Configuração das tabelas do banco de dados

importador_real.py

Importação dos logs para o banco SQLite

verificar_dados.py

Verificação da integridade dos dados

captura_sessao.py

Script utilizado para testes de captura

importar_para_banco.py

Script auxiliar utilizado em testes

semana_12.py

Script utilizado para verificações dos dados de proximidade



🗄️ Banco de dados

O sistema utiliza SQLite para armazenamento das informações das sessões.

O banco principal utilizado pelo projeto é:

data/terapia.db

Nele são armazenados os dados utilizados posteriormente pelo dashboard
para análise das sessões.



🎯 Objetivo do módulo offline

O Módulo Offline tem como objetivo fornecer uma estrutura para:

receber dados previamente registrados;

organizar e importar esses dados;

armazená-los em um banco de dados;

disponibilizar informações para análise;

apresentar indicadores e gráficos por meio de uma interface visual.

Esta etapa serve como base para a análise dos dados coletados durante as
sessões terapêuticas e para o desenvolvimento posterior dos relatórios
clínicos automatizados.
