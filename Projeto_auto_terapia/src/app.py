import streamlit as st          # Importa o Streamlit para construir a interface web interativa
import sqlite3                  # Importa o driver para ler o banco de dados 'terapia.db'
import pandas as pd             # Importa o Pandas para organizar os dados em tabelas e fazer cálculos
import plotly.express as px     # Importa o Plotly para criar o gráfico de pizza moderno e interativo
import os                       # Importa a biblioteca do sistema para verificar caminhos de arquivos

# Configura as definições da página (título que aparece na aba do navegador e layout em tela cheia)
st.set_page_config(page_title="Castor - Sistema de Relatórios", layout="wide")

# --- BLOCO DE BUSCA DE DADOS (USANDO CACHE PARA VELOCIDADE) ---

@st.cache_data # Diz ao Streamlit para guardar os dados na memória RAM e não ler o banco toda hora
def carregar_lista_sessoes():
    conn = sqlite3.connect('data/terapia.db') # Abre a conexão com o banco de dados SQLite
    # Comando SQL para pegar o ID, o nome da criança e a data de todas as sessões cadastradas
    query = "SELECT id_sessao, id_crianca, data FROM sessoes ORDER BY id_sessao DESC"
    df = pd.read_sql(query, conn) # Transforma o resultado do banco em uma tabela do Pandas
    conn.close() # Fecha a conexão para liberar o arquivo do banco
    return df # Devolve a lista de sessões para o menu lateral

@st.cache_data # Cache para os dados pesados (milhares de registros do laser e das ações)
def buscar_dados_sessao(id_sessao):
    conn = sqlite3.connect('data/terapia.db') # Abre o banco novamente
    # Busca a distância do laser e garante que o tempo (timestamp) seja um número com 3 casas decimais
    df_laser = pd.read_sql(f"SELECT timestamp, distancia_mm FROM sensor_laser WHERE id_sessao = {id_sessao}", conn)
    df_laser['timestamp'] = pd.to_numeric(df_laser['timestamp']).round(3)
    # Busca os logs do robô (comandos e níveis de engajamento) para a sessão escolhida
    df_acoes = pd.read_sql(f"SELECT timestamp, nome_comando FROM acoes_robo WHERE id_sessao = {id_sessao}", conn)
    df_acoes['timestamp'] = pd.to_numeric(df_acoes['timestamp']) # Mantém como número para cálculos
    conn.close() # Fecha a conexão
    return df_laser, df_acoes # Retorna os dois conjuntos de dados para os gráficos

# --- BLOCO DE LÓGICA DE CÁLCULOS E ESTILIZAÇÃO ---

def aplicar_cores(val):
    # Retorna o código de cor CSS baseado na palavra encontrada na célula da tabela
    if val == 'alta': return 'background-color: #d4edda; color: #155724' # Verde (Engajamento bom)
    if val == 'media': return 'background-color: #fff3cd; color: #856404' # Amarelo (Atenção)
    if val == 'baixa': return 'background-color: #f8d7da; color: #721c24' # Vermelho (Engajamento baixo)
    return '' # Se não for nenhum desses, não aplica cor

def calcular_duracao_engajamento(df, fim_sessao):
    # Organiza os eventos pelo tempo em que aconteceram
    df = df.sort_values('timestamp').copy()
    # Identifica quando o PRÓXIMO evento começou. Se for o último, usa o fim da sessão como limite.
    df['proximo_ts'] = df['timestamp'].shift(-1).fillna(fim_sessao)
    # A duração é: Tempo do próximo evento - Tempo do evento atual
    df['duracao'] = df['proximo_ts'] - df['timestamp']
    # Agrupa por categoria (alta/média/baixa) e soma todos os segundos gastos em cada uma
    return df.groupby('nome_comando')['duracao'].sum().reset_index()

@st.cache_data # Cache para preparar o arquivo de download sem travar o app
def converter_para_csv(df, observacao):
    # Criamos uma cópia para arredondar os dados sem mexer no que o usuário vê na tela
    df_export = df.copy()
    df_export['timestamp'] = df_export['timestamp'].round(3) # Arredonda o tempo para 3 casas
    
    # Geramos o texto da tabela em formato CSV
    csv_tabela = df_export.to_csv(index=False)
    
    # Criamos um cabeçalho de texto para incluir a observação clínica no arquivo
    cabecalho = f"RELATÓRIO DE SESSÃO CASTOR\n"
    cabecalho += f"OBSERVAÇÃO CLÍNICA: {observacao}\n" # Adiciona o que você escreveu no app
    cabecalho += "-"*40 + "\n" # Adiciona uma linha divisória no arquivo
    
    # Junta o cabeçalho de texto com os dados da tabela
    conteudo_final = cabecalho + csv_tabela
    
    return conteudo_final.encode('utf-8') # Retorna o arquivo codificado para download

# --- CONSTRUÇÃO DA INTERFACE VISUAL (UI) ---

# Define o caminho para a imagem do macaquinho (ajustado para macaco.jpg conforme você renomeou)
CAMINHO_MACACO = os.path.join("src", "macaco.jpg")

# Adiciona o título principal na barra lateral esquerda
st.sidebar.title("Menu do Sistema")

# Tenta carregar a imagem do macaquinho para a barra lateral
if os.path.exists(CAMINHO_MACACO):
    st.sidebar.image(CAMINHO_MACACO, width=150) # Exibe a imagem com largura de 150px
else:
    # Caso a imagem não seja encontrada na pasta src, exibe um ícone genérico
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3069/3069172.png", width=80)
    st.sidebar.error("Imagem 'macaco.jpg' não encontrada na pasta 'src'")

# Cria os botões para navegar entre o relatório individual e a evolução do paciente
modo = st.sidebar.radio("Tipo de Análise:", ["Relatório de Sessão", "Evolução do Paciente"])
st.sidebar.divider() # Adiciona uma linha de separação visual no menu

# --- MODO 1: RELATÓRIO INDIVIDUAL DA SESSÃO ---
if modo == "Relatório de Sessão":
    st.sidebar.header("Filtros") # Título da seção de filtros no menu
    df_sessoes = carregar_lista_sessoes() # Busca a lista de sessões disponíveis no banco

    if not df_sessoes.empty: # Se houver dados registrados no banco...
        # Cria a lista formatada "ID - Criança (Data)" para o menu de escolha
        opcoes = df_sessoes.apply(lambda x: f"{x['id_sessao']} - {x['id_crianca']} ({x['data']})", axis=1).tolist()
        escolha = st.sidebar.selectbox("Escolha a Sessão:", opcoes) # Cria a caixa de seleção
        id_selecionado = escolha.split(" - ")[0] # Extrai o número do ID da escolha feita
        nome_paciente = escolha.split(" - ")[1].split(" (")[0] # Extrai o nome da criança
    else:
        # Se o banco estiver vazio, avisa o usuário e para o programa
        st.warning("Nenhuma sessão encontrada. Importe dados primeiro.")
        st.stop()

    # Busca os dados reais de laser e logs de ações da sessão que foi selecionada
    df_laser, df_acoes = buscar_dados_sessao(id_selecionado)

    # Exibe o título do relatório principal
    st.title(f"- Relatório Individual: {nome_paciente} interação")

    # SEÇÃO DE MÉTRICAS (CARTÕES NO TOPO)
    st.subheader(" Indicadores de Performance")
    c1, c2, c3, c4 = st.columns(4) # Cria 4 colunas para exibir os números de destaque
    # Calcula a soma dos tempos usando o último registro do laser como o fim da sessão
    df_tempos = calcular_duracao_engajamento(df_acoes, df_laser['timestamp'].max())
    mapa_tempos = df_tempos.set_index('nome_comando')['duracao'].to_dict() # Facilita a busca dos valores
    
    # Preenche cada cartão com os tempos de engajamento e a distância média
    with c1: st.metric("Engajamento ALTO", f"{mapa_tempos.get('alta', 0):.1f}s")
    with c2: st.metric("Engajamento MÉDIO", f"{mapa_tempos.get('media', 0):.1f}s")
    with c3: st.metric("Engajamento BAIXO", f"{mapa_tempos.get('baixa', 0):.1f}s")
    with c4: st.metric("Proximidade Média", f"{df_laser['distancia_mm'].mean():.2f} px")

    st.divider() # Linha decorativa para separar as seções

    # SEÇÃO DE GRÁFICOS (LADO A LADO)
    col_grafico, col_pizza = st.columns([2, 1]) # O gráfico de linha usa 2/3 da largura, a pizza usa 1/3
    
    with col_pizza: # Coluna da Direita: Gráfico de Pizza (Plotly)
        st.write("### % de Engajamento")
        # Cria a pizza com cores fixas (Verde, Amarelo e Vermelho)
        fig_pizza = px.pie(df_tempos, values='duracao', names='nome_comando', color='nome_comando',
                           color_discrete_map={'alta': '#28a745', 'media': '#ffc107', 'baixa': '#dc3545'})
        fig_pizza.update_layout(margin=dict(t=0, b=0, l=0, r=0)) # Remove margens brancas desnecessárias
        st.plotly_chart(fig_pizza, width='stretch') # Desenha o gráfico na tela

    with col_grafico: # Coluna da Esquerda: Gráfico de Linha (Tendência)
        st.subheader("Proximidade ao Castor (Tendência)")
        # Calcula a média móvel de 50 pontos para suavizar o gráfico e tirar ruídos
        df_laser['distancia_suave'] = df_laser['distancia_mm'].rolling(window=50, min_periods=1).mean()
        # Plota a linha usando amostragem (1 a cada 10) para o app não travar com muitos dados
        st.line_chart(df_laser.iloc[::10, :].set_index('timestamp')['distancia_suave'])

    # SEÇÃO DE OBSERVAÇÕES (Onde o terapeuta escreve a análise)
    st.subheader(" Observações Clínicas")
    # Cria a caixa de texto grande onde você escreve seus comentários
    obs = st.text_area("Notas sobre o comportamento do paciente nesta sessão:", 
                       placeholder="Ex: Demonstrou boa evolução no contato visual...")
    if st.button("Salvar Observações"): 
        # Exibe uma mensagem de confirmação verde na tela
        st.success("Observação salva temporariamente para o download!")

    st.divider() # Linha decorativa

    # SEÇÃO DA TABELA E DOWNLOAD
    st.subheader(" Log de Eventos e Download")
    col_tabela, col_botao = st.columns([4, 1]) # Tabela ocupa a maior parte da tela
    
    with col_botao: # Lado Direito: Botão para baixar o arquivo
        # ATUALIZADO: Agora passamos a tabela E a sua observação para a função
        dados_csv = converter_para_csv(df_acoes, obs) 
        st.download_button(label="+ Baixar Log (CSV)", data=dados_csv, 
                           file_name=f"relatorio_sessao_{id_selecionado}.csv", mime="text/csv", width='stretch')

    with col_tabela: # Exibe a tabela de logs formatada
        df_view = df_acoes.copy()
        # Aplica cores nas linhas e formata o tempo para aparecer com 3 casas na tela
        st.dataframe(df_view.style.map(aplicar_cores, subset=['nome_comando'])
                     .format({"timestamp": "{:.3f}"}), width='stretch')

# --- MODO 2: PÁGINA DE EVOLUÇÃO (PLANEJAMENTO DA SEMANA 4) ---
elif modo == "Evolução do Paciente":
    st.title(" Evolução Histórica")
    st.info("Funcionalidade em desenvolvimento para a Semana 4.")
    st.write("Nesta tela, será possível comparar o progresso da criança entre diferentes datas.")
    # Exemplo de seletor que será programado na próxima semana
    st.selectbox("Selecione o Paciente para análise comparativa:", ["Daniel", "Outros..."])