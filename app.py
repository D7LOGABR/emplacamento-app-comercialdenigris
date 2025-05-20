import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta
from collections import Counter
import os
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(
    page_title="Emplacamentos De Nigris",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilo CSS Customizado ---
st.markdown("""
<style>
    /* Ajustar padding do container principal */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    /* Estilo para os cards de informação */
    .info-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #0055a4; /* Azul De Nigris */
    }
    .info-card .label {
        font-weight: bold;
        color: #003366; /* Azul escuro De Nigris */
        display: block;
        margin-bottom: 3px;
    }
    .info-card .value {
        color: #333;
    }
    /* Títulos */
    h1, h2, h3 {
        color: #003366; /* Azul escuro De Nigris */
    }
    /* Botão de busca */
    .stButton>button {
        background-color: #0055a4; /* Azul De Nigris */
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #003366;
        color: white;
    }
    /* Mensagens de erro/info */
    .stAlert p {
        font-size: 1rem; /* Ajustar tamanho da fonte nas mensagens */
    }
    /* Estilo para métricas de resumo */
    .stMetric {
        background-color: #e9ecef;
        border-radius: 8px;
        padding: 10px 15px;
        border-left: 5px solid #6c757d; /* Cinza */
    }
</style>
""", unsafe_allow_html=True)

# --- Constantes e Caminhos ---
DATA_DIR = "data"
DEFAULT_EXCEL_FILE = os.path.join(DATA_DIR, "EMPLACAMENTO ANUAL - CAMINHÕES.xlsx")
LOGO_COLOR_PATH = os.path.join(DATA_DIR, "logo_denigris_colorido.png")
LOGO_WHITE_PATH = os.path.join(DATA_DIR, "logo_denigris_branco.png")

# --- Nomes das Colunas Opcionais (Definidos Globalmente) ---
NOME_COLUNA_ENDERECO = "ENDEREÇO COMPLETO"
NOME_COLUNA_TELEFONE = "TELEFONE1" # <<< Nome da coluna de telefone definido

# --- Funções de Carregamento de Dados ---
def load_data(file_path_or_buffer):
    """Carrega e pré-processa os dados do arquivo Excel."""
    try:
        df = pd.read_excel(file_path_or_buffer)

        # Limpeza e conversão de tipos (com dayfirst=True)
        df["Data emplacamento"] = pd.to_datetime(df["Data emplacamento"], errors="coerce", dayfirst=True)
        df["CNPJ CLIENTE"] = df["CNPJ CLIENTE"].astype(str).str.strip()
        df["NOME DO CLIENTE"] = df["NOME DO CLIENTE"].astype(str).str.strip()

        # Processar colunas opcionais usando nomes globais
        if NOME_COLUNA_ENDERECO in df.columns:
            df[NOME_COLUNA_ENDERECO] = df[NOME_COLUNA_ENDERECO].astype(str).str.strip()
        else:
            df[NOME_COLUNA_ENDERECO] = "N/A"

        if NOME_COLUNA_TELEFONE in df.columns and NOME_COLUNA_TELEFONE != "TELEFONE_PENDENTE":
            df[NOME_COLUNA_TELEFONE] = df[NOME_COLUNA_TELEFONE].astype(str).str.strip()
        else:
            # Criar coluna vazia se não existir ou se o nome não foi substituído
            df[NOME_COLUNA_TELEFONE] = "N/A"

        # Garantir que as colunas para o detalhamento existam
        if "Chassi" not in df.columns:
            df["Chassi"] = "N/A"
        else:
            df["Chassi"] = df["Chassi"].astype(str).str.strip()
            
        if "Modelo" not in df.columns:
            df["Modelo"] = "N/A"
        else:
            df["Modelo"] = df["Modelo"].astype(str).str.strip()
            
        if "Concessionária" not in df.columns:
            df["Concessionária"] = "N/A"
        else:
            df["Concessionária"] = df["Concessionária"].astype(str).str.strip()

        df["CNPJ_NORMALIZED"] = df["CNPJ CLIENTE"].str.replace(r"[.\\/-]", "", regex=True)
        df["Ano"] = df["Data emplacamento"].dt.year
        df["Mes"] = df["Data emplacamento"].dt.month

        # Remover linhas onde 'Ano' é NaN (resultante de datas inválidas)
        df.dropna(subset=["Ano"], inplace=True)
        df["Ano"] = df["Ano"].astype(int)

        return df
    except FileNotFoundError:
        st.error(f"Erro: Arquivo Excel padrão não encontrado em {DEFAULT_EXCEL_FILE}. Faça o upload de um arquivo.")
        return None
    except Exception as e:
        file_info = "arquivo carregado" if isinstance(file_path_or_buffer, BytesIO) else os.path.basename(str(file_path_or_buffer))
        st.error(f"Erro ao carregar ou processar o arquivo Excel ({file_info}): {e}")
        return None

# --- Funções Auxiliares ---
def get_modes(series):
    cleaned_series = series.dropna().astype(str)
    if cleaned_series.empty:
        return ["N/A"]
    counts = Counter(cleaned_series)
    if not counts:
        return ["N/A"]
    max_count = counts.most_common(1)[0][1]
    modes = sorted([item for item, count in counts.items() if count == max_count])
    return modes

def format_list(items):
    if not items or items == ["N/A"]:
        return "N/A"
    return ", ".join(map(str, items))

def calculate_next_purchase_prediction(valid_purchase_dates):
    if not valid_purchase_dates or len(valid_purchase_dates) < 2:
        return "Previsão não disponível (histórico insuficiente).", None

    valid_purchase_dates.sort()
    last_purchase_date = valid_purchase_dates[-1]
    intervals_months = []
    for i in range(1, len(valid_purchase_dates)):
        delta = relativedelta(valid_purchase_dates[i], valid_purchase_dates[i-1])
        months_diff = delta.years * 12 + delta.months
        days_diff = delta.days
        if months_diff > 0:
            intervals_months.append(months_diff)
        elif months_diff == 0 and days_diff > 0:
             intervals_months.append(0.5)

    if not intervals_months:
         return "Previsão não disponível (compras muito próximas ou única).", last_purchase_date

    avg_interval_months = sum(intervals_months) / len(intervals_months)
    if avg_interval_months < 1:
        avg_interval_months = 1

    predicted_next_date = last_purchase_date + relativedelta(months=int(round(avg_interval_months)))

    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    predicted_month_year = f"{meses[predicted_next_date.month - 1]} de {predicted_next_date.year}"
    prediction_text = f"Próxima compra provável em: **{predicted_month_year}**"

    return prediction_text, predicted_next_date

def get_sales_pitch(last_purchase_date, predicted_next_date, total_purchases):
    today = pd.Timestamp.now().normalize()
    if not last_purchase_date:
        return "Primeira vez? 🤔 Sem histórico de compras registrado para este cliente."

    if not isinstance(last_purchase_date, pd.Timestamp):
        last_purchase_date = pd.to_datetime(last_purchase_date)

    months_since_last = relativedelta(today, last_purchase_date).years * 12 + relativedelta(today, last_purchase_date).months
    last_purchase_str = last_purchase_date.strftime("%d/%m/%Y")

    if predicted_next_date and isinstance(predicted_next_date, pd.Timestamp):
        months_to_next = relativedelta(predicted_next_date, today).years * 12 + relativedelta(predicted_next_date, today).months
        days_to_next = relativedelta(predicted_next_date, today).days
        predicted_month_year = f"{["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][predicted_next_date.month - 1]} de {predicted_next_date.year}"

        if months_to_next < 0 or (months_to_next == 0 and days_to_next < 0):
            return f"🚨 **Atenção!** A compra prevista para **{predicted_month_year}** pode estar próxima ou já passou! Última compra em {last_purchase_str}. Contato urgente!"
        elif months_to_next <= 2:
            return f"📈 **Oportunidade Quente!** Próxima compra prevista para **{predicted_month_year}**. Ótimo momento para contato! Última compra em {last_purchase_str}."
        elif months_to_next <= 6:
            return f"🗓️ **Planeje-se!** Próxima compra prevista para **{predicted_month_year}**. Prepare sua abordagem! Última compra em {last_purchase_str}."
        else:
            return f"⏳ Compra prevista para **{predicted_month_year}**. Mantenha o relacionamento aquecido! Última compra em {last_purchase_str}."
    else:
        if months_since_last >= 18:
            return f"🚨 Alerta de sumiço! Faz {months_since_last} meses desde a última compra ({last_purchase_str}). Hora de reativar esse cliente! 📞"
        elif months_since_last >= 12:
            return f"👀 E aí, sumido! Faz {months_since_last} meses desde a última compra ({last_purchase_str}). Que tal um alô para esse cliente?"
        elif months_since_last >= 6:
            return f"⏳ Já se passaram {months_since_last} meses... ({last_purchase_str}). Bom momento para um follow-up e mostrar as novidades!"
        elif total_purchases > 3:
             return f"👍 Cliente fiel ({total_purchases} compras)! Última compra em {last_purchase_str}. Mantenha o bom trabalho!"
        else:
            return f"✅ Compra recente ({last_purchase_str}). Ótimo para fortalecer o relacionamento!"

# --- Interface Principal --- 

# --- Cabeçalho ---
col1_header, col2_header = st.columns([1, 3])
with col1_header:
    if os.path.exists(LOGO_COLOR_PATH):
        st.image(LOGO_COLOR_PATH, width=250)
    else:
        st.warning("Logo colorido não encontrado.")
with col2_header:
    st.title("Consulta de Emplacamentos")
    st.markdown("**Ferramenta interna De Nigris** - Busque por cliente ou veja o resumo geral.")

st.divider()

# --- Upload e Carregamento de Dados (NOVA LÓGICA DE PERSISTÊNCIA) ---
st.sidebar.header("Atualizar Dados")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"], key="file_uploader")

# Inicializar estado da sessão
if "dataframe" not in st.session_state:
    st.session_state["dataframe"] = None
if "data_source_info" not in st.session_state: # Armazena info sobre a fonte (nome do arquivo ou 'default')
    st.session_state["data_source_info"] = None
if "uploaded_file_content" not in st.session_state: # Armazena o CONTEÚDO do arquivo carregado
    st.session_state["uploaded_file_content"] = None

needs_reload = False
data_to_process = None
current_source_info = None

# 1. Verificar se um NOVO arquivo foi carregado
if uploaded_file is not None:
    uploaded_content = BytesIO(uploaded_file.getvalue())
    uploaded_info = f"uploaded_{uploaded_file.name}_{uploaded_file.size}"
    
    # Se for diferente do que está na memória ou se não há nada na memória
    if uploaded_info != st.session_state.get("data_source_info"):
        st.session_state["uploaded_file_content"] = uploaded_content # Guarda o conteúdo
        st.session_state["data_source_info"] = uploaded_info
        data_to_process = st.session_state["uploaded_file_content"]
        needs_reload = True
        st.sidebar.success(f"Arquivo 	'{uploaded_file.name}'	 pronto para carregar.")
    else:
        # Mesmo arquivo, usar o conteúdo já guardado se precisar recarregar
        data_to_process = st.session_state["uploaded_file_content"]
        current_source_info = st.session_state["data_source_info"]
        if st.session_state.get("dataframe") is None: # Se o dataframe não está carregado por algum motivo
            needs_reload = True

# 2. Se nenhum arquivo foi carregado, decidir qual usar
else:
    if st.session_state.get("uploaded_file_content") is not None:
        # Usar o conteúdo carregado anteriormente
        data_to_process = st.session_state["uploaded_file_content"]
        current_source_info = st.session_state["data_source_info"]
        if st.session_state.get("dataframe") is None:
            needs_reload = True
            st.sidebar.info("Usando arquivo carregado anteriormente.")
        # else: # Já está carregado, não precisa fazer nada
        #     pass 
    elif os.path.exists(DEFAULT_EXCEL_FILE):
        # Usar o arquivo padrão
        data_to_process = DEFAULT_EXCEL_FILE
        current_source_info = "default"
        # Se estávamos usando um arquivo carregado, limpar o conteúdo da memória
        if st.session_state.get("data_source_info") != "default":
            st.session_state["uploaded_file_content"] = None
            st.session_state["data_source_info"] = "default"
            needs_reload = True # Precisa recarregar o default
            st.sidebar.info(f"Usando arquivo padrão: {os.path.basename(DEFAULT_EXCEL_FILE)}")
        elif st.session_state.get("dataframe") is None:
             needs_reload = True # Carregar o default pela primeira vez
             st.sidebar.info(f"Usando arquivo padrão: {os.path.basename(DEFAULT_EXCEL_FILE)}")
    else:
        # Nenhum arquivo disponível
        st.error("Nenhum arquivo de dados disponível. Faça o upload de um arquivo Excel ou certifique-se que o arquivo padrão existe.")
        st.stop()

# 3. Carregar os dados se necessário
if needs_reload and data_to_process is not None:
    # Rebobinar o BytesIO antes de ler novamente
    if isinstance(data_to_process, BytesIO):
        data_to_process.seek(0)
    st.session_state["dataframe"] = load_data(data_to_process)
    if st.session_state["dataframe"] is not None:
        st.sidebar.success("Dados carregados/atualizados!")
        st.rerun() # Força o rerender para UI refletir a mudança
    else:
        st.sidebar.error("Falha ao carregar/atualizar dados.")
        # Limpar estado se o carregamento falhar
        st.session_state["dataframe"] = None
        st.session_state["data_source_info"] = None
        st.session_state["uploaded_file_content"] = None

# Usar o dataframe do estado da sessão
df_full = st.session_state.get("dataframe")

if df_full is None or df_full.empty:
    st.warning("Os dados não puderam ser carregados ou estão vazios. Verifique o arquivo ou a mensagem de erro acima.")
    st.stop()

# --- Barra de Busca e Filtros --- 
st.subheader("Buscar Cliente Específico")
search_query = st.text_input("Digite o Nome ou CNPJ do cliente:", "", key="search_input")
search_button = st.button("Buscar", key="search_button")

st.sidebar.header("Filtros Gerais (Afetam Busca e Resumo)")
all_brands = sorted(df_full["Marca"].dropna().unique())
selected_brands = st.sidebar.multiselect("Filtrar por Marca:", all_brands)

all_segments = sorted(df_full["Segmento"].dropna().unique())
selected_segments = st.sidebar.multiselect("Filtrar por Segmento:", all_segments)

# Aplicar filtros ao DataFrame principal ANTES de qualquer cálculo
df_display = df_full.copy()
if selected_brands:
    df_display = df_display[df_display["Marca"].isin(selected_brands)]
if selected_segments:
    df_display = df_display[df_display["Segmento"].isin(selected_segments)]

# --- Exibição dos Resultados da Busca --- 
st.divider()

if search_button and search_query:
    st.markdown(f"### Resultados da Busca por: '{search_query}'")
    query_normalized = ''.join(filter(str.isdigit, str(search_query)))

    mask = (
        df_display["NOME DO CLIENTE"].str.contains(search_query, case=False, na=False)
    )
    if query_normalized and len(query_normalized) > 5:
         mask = mask | df_display["CNPJ_NORMALIZED"].str.contains(query_normalized, case=False, na=False)

    results_df = df_display[mask]

    if results_df.empty:
        st.warning("Cliente não encontrado na base de dados (considerando os filtros aplicados, se houver).")
    else:
        unique_cnpjs = results_df["CNPJ_NORMALIZED"].unique()

        if len(unique_cnpjs) > 1:
            st.info(f"Múltiplos clientes encontrados para \"{search_query}\". Exibindo o primeiro encontrado: {results_df.iloc[0]['NOME DO CLIENTE']} ({results_df.iloc[0]['CNPJ CLIENTE']}).")
            target_cnpj_normalized = unique_cnpjs[0]
        elif len(unique_cnpjs) == 1:
            target_cnpj_normalized = unique_cnpjs[0]
        else:
             st.warning("Não foi possível identificar um CNPJ único para o cliente.")
             st.stop()

        client_df = results_df[results_df["CNPJ_NORMALIZED"] == target_cnpj_normalized].copy()

        if not client_df.empty:
            client_df_sorted = client_df.sort_values(by="Data emplacamento", ascending=False)
            latest_record = client_df_sorted.iloc[0]
            
            client_name = latest_record["NOME DO CLIENTE"]
            client_cnpj = latest_record["CNPJ CLIENTE"]
            client_address = latest_record.get(NOME_COLUNA_ENDERECO, "N/A")
            client_phone = latest_record.get(NOME_COLUNA_TELEFONE, "N/A")
            
            st.subheader(f"Detalhes do Cliente: {client_name}")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"<div class='info-card'><span class='label'>CNPJ:</span><span class='value'>{client_cnpj}</span></div>", unsafe_allow_html=True)
                st.markdown(f"<div class='info-card'><span class='label'>Endereço:</span><span class='value'>{client_address}</span></div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='info-card'><span class='label'>Telefone:</span><span class='value'>{client_phone}</span></div>", unsafe_allow_html=True)
                
                # Calcular estatísticas
                total_plated = len(client_df_sorted)
                first_plate_date = client_df_sorted["Data emplacamento"].min()
                last_plate_date = client_df_sorted["Data emplacamento"].max()
                
                first_plate_date_str = first_plate_date.strftime("%d/%m/%Y") if pd.notna(first_plate_date) else "N/A"
                last_plate_date_str = last_plate_date.strftime("%d/%m/%Y") if pd.notna(last_plate_date) else "N/A"
                last_plate_date_obj = last_plate_date if pd.notna(last_plate_date) else None
                
                st.markdown(f"<div class='info-card'><span class='label'>Total de Emplacamentos:</span><span class='value'>{total_plated}</span></div>", unsafe_allow_html=True)
            
            st.markdown("#### Previsão e Insights")
            
            valid_dates = client_df["Data emplacamento"].dropna().tolist()
            prediction_text, predicted_date_obj = calculate_next_purchase_prediction(valid_dates)
            sales_pitch = get_sales_pitch(last_plate_date_obj, predicted_date_obj, total_plated)
            
            col_pred, col_insight = st.columns(2)
            with col_pred:
                st.info(prediction_text)
            with col_insight:
                st.success(f"💡 {sales_pitch}")
                
            st.markdown("#### Histórico de Compras")
            # Preparar dados para o gráfico
            client_df['AnoMes'] = client_df['Data emplacamento'].dt.to_period('M')
            purchase_history = client_df.groupby('AnoMes').size().reset_index(name='Quantidade')
            purchase_history['AnoMes'] = purchase_history['AnoMes'].astype(str)

            if not purchase_history.empty:
                fig = px.bar(purchase_history, x='AnoMes', y='Quantidade', title=f'Histórico de Compras de {client_name}',
                             labels={'AnoMes': 'Mês/Ano', 'Quantidade': 'Nº de Emplacamentos'},
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(xaxis_title="Período", yaxis_title="Quantidade Emplacada")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Não há histórico de compras suficiente para gerar gráfico.")
            
            # NOVA SEÇÃO: Lista detalhada de emplacamentos com chassi, modelo e concessionária
            st.markdown("#### Detalhamento dos Emplacamentos")
            
            # Preparar DataFrame para exibição
            detail_df = client_df_sorted[["Data emplacamento", "Chassi", "Modelo", "Concessionária"]].copy()
            detail_df["Data emplacamento"] = detail_df["Data emplacamento"].dt.strftime("%d/%m/%Y")
            detail_df.columns = ["Data", "Chassi", "Modelo", "Concessionária"]
            
            # Exibir tabela detalhada
            st.dataframe(detail_df, use_container_width=True)
            
        else:
            st.warning("Cliente encontrado, mas sem registros de emplacamento válidos.")
elif search_button and not search_query:
    st.warning("Por favor, digite um nome ou CNPJ para buscar.")
else:
    # Se nenhuma busca foi feita, exibir o resumo geral
    st.divider()
    st.subheader("Resumo Geral da Base de Dados (Considerando Filtros)")

    # Calcular estatísticas gerais do df_display (DataFrame filtrado)
    total_emplacamentos_display = len(df_display)
    total_clientes_unicos_display = df_display["CNPJ_NORMALIZED"].nunique()
    
    if not df_display.empty:
        primeiro_ano_display = int(df_display["Ano"].min())
        ultimo_ano_display = int(df_display["Ano"].max())
    else:
        primeiro_ano_display = "N/A"
        ultimo_ano_display = "N/A"

    col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
    with col_resumo1:
        st.metric(label="Total de Emplacamentos (Filtro)", value=f"{total_emplacamentos_display:,}".replace(",", "."))
    with col_resumo2:
        st.metric(label="Total de Clientes Únicos (Filtro)", value=f"{total_clientes_unicos_display:,}".replace(",", "."))
    with col_resumo3:
        st.metric(label="Período Coberto (Filtro)", value=f"{primeiro_ano_display} - {ultimo_ano_display}")

    st.markdown("#### Emplacamentos por Ano (Filtro)")
    emplacamentos_por_ano_display = df_display['Ano'].value_counts().sort_index()
    if not emplacamentos_por_ano_display.empty:
        st.bar_chart(emplacamentos_por_ano_display)
    else:
        st.info("Não há dados de emplacamento por ano para exibir com os filtros aplicados.")

    st.markdown("#### Emplacamentos por Marca e Ano (Filtro)")
    emplacamentos_marca_ano_display = df_display.groupby(["Ano", "Marca"]).size().reset_index(name="Quantidade")
    if not emplacamentos_marca_ano_display.empty:
        pivot_marca_ano_display = emplacamentos_marca_ano_display.pivot(index="Marca", columns="Ano", values="Quantidade").fillna(0).astype(int)
        st.dataframe(pivot_marca_ano_display, use_container_width=True)
    else:
        st.info("Não há dados de emplacamento por marca e ano para exibir com os filtros aplicados.")

# --- Rodapé (Opcional) ---
st.sidebar.divider()
if os.path.exists(LOGO_WHITE_PATH):
    st.sidebar.image(LOGO_WHITE_PATH, use_container_width=True)
else:
    st.sidebar.warning("Logo branco não encontrado.")
st.sidebar.caption("© De Nigris Distribuidora")
