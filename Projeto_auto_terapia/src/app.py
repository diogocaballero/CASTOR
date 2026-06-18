import streamlit as st          # Importa o Streamlit para construir a interface web interativa
import sqlite3                  # Importa o driver para ler o banco de dados 'terapia.db'
import pandas as pd             # Importa o Pandas para organizar os dados em tabelas e fazer cálculos
import plotly.express as px     # Importa o Plotly para criar o gráfico de pizza moderno e interativo
import os                       # Importa a biblioteca do sistema para verificar caminhos de arquivos
from fpdf import FPDF           # Importa o FPDF2 para fazer a geração automatizada do PDF clínico
from io import BytesIO          # Importa o BytesIO para manipular o PDF na memória RAM sem gerar lixo no disco

# Configura as definições da página (título que aparece na aba do navegador e layout em tela cheia)
st.set_page_config(page_title="Castor - Sistema de Relatórios", layout="wide")

# --- CLASSE DE CONFIGURAÇÃO VISUAL DO PDF (TEXTO PURO REVISADO) ---
class PDF_Clinico(FPDF):
    def header(self):
        # Configura o cabeçalho superior em texto puro centralizado
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(26, 54, 93) # Azul Escuro Institucional
        self.cell(0, 10, "PROJETO CASTOR - RELATORIO CLINICO AUTOMATICO", align="C")
        self.ln(10)
        
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(113, 128, 150) # Cinza Neutro
        self.cell(0, 5, "Laboratorio de Tecnologia Assistiva e Pesquisa Aplicada - UFES", align="C")
        self.ln(5)
        
        self.line(10, 31, 200, 31) # Linha divisória fina abaixo do cabeçalho
        self.ln(10) # Avança o espaçamento

    def footer(self):
        # Configura o rodapé com numeração automática de páginas
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(113, 128, 150)
        self.cell(0, 10, f"Projeto Castor - Relatorio Gerado Automaticamente - Pagina {self.page_no()}/{{nb}}", align="C")

# --- BLOCO DE BUSCA DE DADOS (USANDO CACHE PARA VELOCIDADE) ---

@st.cache_data # Diz ao Streamlit para guardar os dados na memória RAM e não ler o banco toda hora
def carregar_lista_sessoes():
    conn = sqlite3.connect('data/terapia.db') # Abre a conexão com o banco de dados SQLite
    # --- AJUSTE RELACIONAL (JOIN) ---
    # Buscamos o nome na tabela 'pacientes' fazendo a junção relacional com a tabela 'sessoes'
    query = """
        SELECT s.id_sessao, p.nome AS nome_paciente, s.nivel_interacao, s.data 
        FROM sessoes s
        JOIN pacientes p ON s.id_paciente = p.id_paciente
        ORDER BY s.id_sessao DESC
    """
    df = pd.read_sql(query, conn) # Transforma o resultado do banco em uma tabela do Pandas
    conn.close() # Fecha a conexão para liberar o arquivo do banco
    return df # Devolve a lista de sessões para o menu lateral

@st.cache_data # Cache para carregar a lista de pacientes única para a tela de evolução
def carregar_lista_pacientes():
    conn = sqlite3.connect('data/terapia.db')
    query = "SELECT id_paciente, nome FROM pacientes ORDER BY nome ASC"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data # Cache para carregar o histórico de evolução de uma criança ao longo do tempo
def buscar_historico_paciente(id_paciente):
    conn = sqlite3.connect('data/terapia.db')
    # Coleta a média de proximidade e o total de eventos de cada sessão daquele paciente específico
    query = f"""
        SELECT s.id_sessao, s.data, s.nivel_interacao,
               (SELECT AVG(distancia_mm) FROM sensor_laser WHERE id_sessao = s.id_sessao) as distancia_media,
               (SELECT COUNT(*) FROM acoes_robo WHERE id_sessao = s.id_sessao) as total_eventos
        FROM sessoes s
        WHERE s.id_paciente = {id_paciente}
        ORDER BY s.id_sessao ASC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data # Cache para os dados pesados (milhares de registros do laser e das ações)
def buscar_dados_sessao(id_sessao):
    conn = sqlite3.connect('data/terapia.db') # Abre o banco novamente
    df_laser = pd.read_sql(f"SELECT timestamp, distancia_mm FROM sensor_laser WHERE id_sessao = {id_sessao}", conn)
    df_laser['timestamp'] = pd.to_numeric(df_laser['timestamp']).round(3)
    df_acoes = pd.read_sql(f"SELECT timestamp, nome_comando FROM acoes_robo WHERE id_sessao = {id_sessao}", conn)
    df_acoes['timestamp'] = pd.to_numeric(df_acoes['timestamp']) # Mantém como número para cálculos
    conn.close() # Fecha a conexão
    return df_laser, df_acoes # Retorna os dois conjuntos de dados para os gráficos

# --- BLOCO DE LÓGICA DE CÁLCULOS E ESTILIZAÇÃO ---

def aplicar_cores(val):
    if val == 'alta': return 'background-color: #d4edda; color: #155724' # Verde (Engajamento bom)
    if val == 'media': return 'background-color: #fff3cd; color: #856404' # Amarelo (Atenção)
    if val == 'baixa': return 'background-color: #f8d7da; color: #721c24' # Vermelho (Engajamento baixo)
    return 'background-color: #e2e3e5; color: #383d41'

def calcular_duracao_engajamento(df, fim_sessao):
    if df.empty:
        return pd.DataFrame(columns=['nome_comando', 'duracao'])
    df = df.sort_values('timestamp').copy()
    df['proximo_ts'] = df['timestamp'].shift(-1).fillna(fim_sessao)
    df['duracao'] = df['proximo_ts'] - df['timestamp']
    return df.groupby('nome_comando')['duracao'].sum().reset_index()

@st.cache_data # Cache para preparar o arquivo de download sem travar o aplicativo
def converter_para_csv(df, observacao):
    df_export = df.copy()
    df_export['timestamp'] = df_export['timestamp'].round(3) # Arredonda o tempo para 3 casas
    csv_tabela = df_export.to_csv(index=False)
    cabecalho = f"RELATORIO DE SESSAO CASTOR\n"
    cabecalho += f"OBSERVACAO CLINICA: {observacao}\n"
    cabecalho += "-"*40 + "\n"
    return (cabecalho + csv_tabela).encode('utf-8')

# --- FUNÇÃO DE GERAÇÃO EXCLUSIVA DO RELATÓRIO PDF ---
def converter_para_pdf(df_acoes, mapa_tempos, nome_paciente, nivel_sessao, data, prox_media, unidade, observacao):
    pdf = PDF_Clinico()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # 1. MÓDULO: DADOS DE IDENTIFICAÇÃO
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 82, 130) # Azul Médio
    pdf.cell(0, 8, "1. Identificacao do Paciente e da Sessao")
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(45, 55, 72)
    
    pdf.cell(95, 6, f"Nome do Paciente: {nome_paciente}")
    pdf.cell(95, 6, f"Data da Terapia: {data}")
    pdf.ln(6)
    pdf.cell(95, 6, f"Diagnostico Clinico Geral: {nivel_sessao.upper()}")
    pdf.cell(95, 6, f"Proximidade Fisica Media: {prox_media:.2f} {unidade}")
    pdf.ln(12)

    # 2. MÓDULO: TEMPOS DE ENGAJAMENTO COMPUTADOS
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 82, 130)
    pdf.cell(0, 8, "2. Distribuicao Temporal de Estados Detectados")
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(45, 55, 72)
    
    for estado, segundos in mapa_tempos.items():
        pdf.cell(0, 6, f" - Tempo Total em Estado '{estado.upper()}': {segundos:.1f} segundos")
        pdf.ln(6)
    pdf.ln(6)

    # 3. MÓDULO: OBSERVAÇÕES E NOTAS DO TERAPEUTA
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(44, 82, 130)
    pdf.cell(0, 8, "3. Consideracoes Clinicas e Anotacoes")
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(45, 55, 72)
    
    texto_obs = observacao if observacao.strip() else "Nenhuma nota clinica registrada para este encontro."
    texto_clean = texto_obs.replace('“', '"').replace('’', '"').replace('—', '-')
    
    # CORREÇÃO DEFINITIVA: Trocado 'txt=' por 'text=' conforme a nova regra v2.7.6 do fpdf2
    pdf.multi_cell(0, 6, text=texto_clean)
    pdf.ln(15)

    # 4. MÓDULO: CAMPO DE ASSINATURA REGULAMENTAR
    pdf.set_y(-40)
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(0, 4, "_________________________________________________________", align="C")
    pdf.ln(5)
    pdf.cell(0, 5, "Assinatura do Terapeuta Ocupacional Responsavel", align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 4, "UFES - Nucleo de Desenvolvimento em Roboterapia Assistiva", align="C")

    return BytesIO(pdf.output())

# --- CONSTRUÇÃO DA INTERFACE VISUAL (UI) ---

CAMINHO_MACACO = os.path.join("src", "macaco.jpg")
st.sidebar.title("Menu do Sistema")

if os.path.exists(CAMINHO_MACACO):
    st.sidebar.image(CAMINHO_MACACO, width=150)
else:
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3069/3069172.png", width=80)
    st.sidebar.error("Imagem 'macaco.jpg' não encontrada na pasta 'src'")

modo = st.sidebar.radio("Tipo de Análise:", ["Relatório de Sessão", "Evolução do Paciente"])
st.sidebar.divider()

# --- MODO 1: RELATÓRIO INDIVIDUAL DA SESSÃO ---
if modo == "Relatório de Sessão":
    st.sidebar.header("Filtros")
    df_sessoes = carregar_lista_sessoes()

    if not df_sessoes.empty:
        opcoes = df_sessoes.apply(lambda x: f"{x['id_sessao']} - Paciente: {x['nome_paciente']} | Nível: {x['nivel_interacao']} ({x['data']})", axis=1).tolist()
        escolha = st.sidebar.selectbox("Escolha a Sessão:", opcoes)
        id_selecionado = choice = escolha.split(" - ")[0]
        nome_paciente = escolha.split("Paciente: ")[1].split(" |")[0]
        classificacao_clinica = escolha.split("Nível: ")[1].split(" (")[0]
    else:
        st.warning("Nenhuma sessão encontrada. Importe dados primeiro.")
        st.stop()

    df_laser, df_acoes = buscar_dados_sessao(id_selecionado)
    st.title(f" Relatório Individual: {nome_paciente} -> Sessão Avaliada como '{classificacao_clinica.upper()}'")

    st.subheader(" Indicadores de Performance da Sessão")
    fim_da_sessao_ts = df_laser['timestamp'].max() if not df_laser.empty else 0
    df_tempos = calcular_duracao_engajamento(df_acoes, fim_da_sessao_ts)
    mapa_tempos = df_tempos.set_index('nome_comando')['duracao'].to_dict()

    categorias_reais = list(mapa_tempos.keys())
    total_cartoes = len(categorias_reais) + 1
    colunas_dinamicas = st.columns(total_cartoes)

    for idx, categoria in enumerate(categorias_reais):
        with colunas_dinamicas[idx]:
            st.metric(label=f"Tempo: {categoria.upper()}", value=f"{mapa_tempos[categoria]:.1f}s")

    with colunas_dinamicas[-1]:
        media_distancia = df_laser['distancia_mm'].mean() if not df_laser.empty else 0
        unidade_medida = "cm" if media_distancia < 500 else "px"
        st.metric("Proximidade Média", f"{media_distancia:.2f} {unidade_medida}")

    st.divider()

    col_grafico, col_pizza = st.columns([2, 1])
    
    with col_pizza:
        st.write("### % de Distribuição da Sessão")
        if not df_tempos.empty:
            fig_pizza = px.pie(df_tempos, values='duracao', names='nome_comando', color='nome_comando',
                               color_discrete_map={'alta': '#28a745', 'media': '#ffc107', 'baixa': '#dc3545'})
            fig_pizza.update_layout(margin=dict(t=0, b=0, l=0, r=0))
            st.plotly_chart(fig_pizza, width='stretch') 
        else:
            st.info("Nenhum evento registrado nesta sessão para gerar análise de pizza.")

    with col_grafico:
        st.subheader("Proximidade ao Castor (Tendência Adaptativa)")
        if not df_laser.empty:
            total_linhas = len(df_laser)
            tamanho_janela = 50 if total_linhas > 1000 else 5
            passo_amostragem = 10 if total_linhas > 5000 else 1
            
            df_laser['distancia_suave'] = df_laser['distancia_mm'].rolling(window=tamanho_janela, min_periods=1).mean()
            st.line_chart(df_laser.iloc[::passo_amostragem, :].set_index('timestamp')['distancia_suave'])
        else:
            st.warning("Sem dados de telemetria laser localizados para esta sessão.")

    st.subheader(" Observações Clínicas")
    obs = st.text_area("Notas sobre o comportamento do paciente nesta sessão:", placeholder="Ex: Demonstrou boa evolução no contato visual...")
    if st.button("Salvar Observações"): 
        st.success("Observação salva temporariamente para o download!")

    st.divider()

    st.subheader(" Log de Eventos e Downloads de Relatórios")
    col_tabela, col_botoes_export = st.columns([4, 1])
    
    with col_botoes_export:
        if not df_acoes.empty:
            dados_csv = converter_para_csv(df_acoes, obs) 
            st.download_button(label="⬇️ Baixar Log (CSV)", data=dados_csv, 
                               file_name=f"relatorio_sessao_{id_selecionado}.csv", mime="text/csv", width='stretch')
            st.write("")
            
            data_atual_sessao = df_sessoes.loc[df_sessoes['id_sessao'] == int(id_selecionado), 'data'].values[0]
            
            dados_pdf = converter_para_pdf(
                df_acoes, mapa_tempos, nome_paciente, 
                classificacao_clinica, data_atual_sessao, 
                media_distancia, unidade_medida, obs
            )
            
            st.download_button(label="📄 Exportar Relatório (PDF)", data=dados_pdf,
                               file_name=f"Relatorio_Clinico_Sessao_{id_selecionado}.pdf", mime="application/pdf", width='stretch')
        else:
            st.write("Sem logs disponíveis.")

    with col_tabela:
        if not df_acoes.empty:
            df_view = df_acoes.copy()
            st.dataframe(df_view.style.map(aplicar_cores, subset=['nome_comando'])
                         .format({"timestamp": "{:.3f}"}), width='stretch')
        else:
            st.info("Nenhum log de ações registrado no banco de dados para esta sessão.")

# --- MODO 2: PÁGINA DE EVOLUÇÃO ---
elif modo == "Evolução do Paciente":
    st.title(" Relatório de Evolução do Paciente")
    st.markdown("Acompanhamento longitudinal das métricas de aproximação física e engajamento clínico.")
    
    df_pacientes = carregar_lista_pacientes()
    
    if not df_pacientes.empty:
        dict_pacientes = df_pacientes.set_index('nome')['id_paciente'].to_dict()
        nome_selecionado = st.selectbox("Selecione o Paciente para análise comparativa histórica:", list(dict_pacientes.keys()))
        id_paciente_alvo = dict_pacientes[nome_selecionado]
        
        df_historico = buscar_historico_paciente(id_paciente_alvo)
        
        if not df_historico.empty:
            df_historico['Sessão'] = "Sessão " + df_historico['id_sessao'].astype(str) + " \n(" + df_historico['nivel_interacao'] + ")"
            col_ev1, col_ev2 = st.columns(2)
            
            with col_ev1:
                st.subheader(" Evolução da Proximidade Média")
                fig_dist = px.line(
                    df_historico, x='Sessão', y='distancia_media', markers=True,
                    title="Tendência de Distância Média ao Castor (Valores menores = maior aproximação)",
                    labels={'distancia_media': 'Distância Média Corporal', 'Sessão': 'Histórico de Testes'}
                )
                fig_dist.update_traces(line=dict(color='#636EFA', width=3))
                st.plotly_chart(fig_dist, width='stretch')
                
            with col_ev2:
                st.subheader(" Frequência de Interações Totais")
                fig_events = px.bar(
                    df_historico, x='Sessão', y='total_eventos', text_auto=True,
                    title="Volume de Ações de Engajamento por Encontro",
                    labels={'total_eventos': 'Quantidade de Eventos', 'Sessão': 'Histórico de Testes'},
                    color='nivel_interacao',
                    color_discrete_map={'baixa': '#dc3545', 'media': '#ffc107', 'alta': '#28a745'}
                )
                st.plotly_chart(fig_events, width='stretch')
                
            st.subheader(" Resumo Histórico de Encontros")
            st.dataframe(df_historico[['id_sessao', 'data', 'nivel_interacao', 'distancia_media', 'total_eventos']].rename(
                columns={'id_sessao': 'ID da Sessão', 'data': 'Data da Terapia', 'nivel_interacao': 'Avaliação', 'distancia_media': 'Distância Média', 'total_eventos': 'Total de Ações'}
            ), width='stretch')
        else:
            st.info(f"O paciente '{nome_selecionado}' ainda não possui sessões registradas com métricas completas.")
    else:
        st.warning("Nenhum paciente cadastrado no banco de dados. Execute o importador primeiro.")