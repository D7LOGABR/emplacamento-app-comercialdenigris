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
</style>
""", unsafe_allow_html=True)

# --- Constantes e Caminhos ---
DATA_DIR = "data"
DEFAULT_EXCEL_FILE = os.path.join(DATA_DIR, "EMPLACAMENTO ANUAL - CAMINHÕES.xlsx")
LOGO_COLOR_PATH = os.path.join(DATA_DIR, "logo_denigris_colorido.png")
LOGO_WHITE_PATH = os.path.join(DATA_DIR, "logo_denigris_branco.png")

# --- Funções de Carregamento e Cache de Dados ---
@st.cache_data(ttl=3600) # Cache por 1 hora
def load_data(file_path_or_buffer):
    """Carrega e pré-processa os dados do arquivo Excel."""
    try:
        df = pd.read_excel(file_path_or_buffer)

        # Limpeza e conversão de tipos (com dayfirst=True)
        df["Data emplacamento"] = pd.to_datetime(df["Data emplacamento"], errors="coerce", dayfirst=True)
        df["CNPJ CLIENTE"] = df["CNPJ CLIENTE"].astype(str).str.strip()
        df["NOME DO CLIENTE"] = df["NOME DO CLIENTE"].astype(str).str.strip()
        # Adicionar tratamento para colunas de endereço e telefone (se existirem)
        if "ENDEREÇO COMPLETO" in df.columns:
            df["ENDEREÇO COMPLETO"] = df["ENDEREÇO COMPLETO"].astype(str).str.strip()
        # Adicionar aqui a coluna de telefone quando o nome for confirmado
        # Exemplo: if "NOME_COLUNA_TELEFONE" in df.columns:
        #             df["NOME_COLUNA_TELEFONE"] = df["NOME_COLUNA_TELEFONE"].astype(str).str.strip()

        df["CNPJ_NORMALIZED"] = df["CNPJ CLIENTE"].str.replace(r"[.\\/-]", "", regex=True)
        df["Ano"] = df["Data emplacamento"].dt.year
        df["Mes"] = df["Data emplacamento"].dt.month
        return df
    except FileNotFoundError:
        st.error(f"Erro: Arquivo Excel padrão não encontrado em {DEFAULT_EXCEL_FILE}. Faça o upload de um arquivo.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo Excel: {e}")
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
        intervals_months.append(months_diff if months_diff > 0 else 1)

    if not intervals_months:
         return "Previsão não disponível (apenas 1 compra).", last_purchase_date

    avg_interval_months = sum(intervals_months) / len(intervals_months)
    predicted_next_date = last_purchase_date + relativedelta(months=int(round(avg_interval_months)))

    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    predicted_month_year = f"{meses[predicted_next_date.month - 1]} de {predicted_next_date.year}"
    prediction_text = f"Próxima compra provável em: **{predicted_month_year}**"

    return prediction_text, predicted_next_date

def get_sales_pitch(last_purchase_date, predicted_next_date, total_purchases):
    today = pd.Timestamp.now().normalize()
    if not last_purchase_date:
        return "Primeira vez? 🤔 Sem histórico de compras registrado para este cliente."

    months_since_last = relativedelta(today, last_purchase_date).years * 12 + relativedelta(today, last_purchase_date).months
    last_purchase_str = last_purchase_date.strftime("%d/%m/%Y")

    if predicted_next_date:
        months_to_next = relativedelta(predicted_next_date, today).years * 12 + relativedelta(predicted_next_date, today).months
        predicted_month_year = f"{["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][predicted_next_date.month - 1]} de {predicted_next_date.year}"

        if months_to_next <= 0:
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
            return f"👍 Cliente fiel na área! Última compra em {last_purchase_str}. Mantenha o relacionamento aquecido!"
        else:
            return f"✅ Compra recente ({last_purchase_str}). Ótimo para fortalecer o relacionamento!"

# --- Interface Principal --- 

# --- Cabeçalho ---
col1_header, col2_header = st.columns([1, 3])
with col1_header:
    if os.path.exists(LOGO_COLOR_PATH):
        st.image(LOGO_COLOR_PATH, width=250)
    else:
        st.warning("Logo não encontrado.")
with col2_header:
    st.title("Consulta de Emplacamentos")
    st.markdown("**Ferramenta interna De Nigris** - Busque por cliente e veja o histórico e oportunidades.")

st.divider()

# --- Upload e Carregamento de Dados com Gerenciamento de Estado ---
st.sidebar.header("Atualizar Dados")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"], key="file_uploader")

# Inicializar estado da sessão se necessário
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False
if "current_data_source_key" not in st.session_state:
    st.session_state["current_data_source_key"] = None
if "dataframe" not in st.session_state:
    st.session_state["dataframe"] = None

data_source_key = None
data_to_load = None

if uploaded_file is not None:
    data_source_key = uploaded_file.name
    data_to_load = BytesIO(uploaded_file.getvalue())
    st.sidebar.success(f"Arquivo selecionado: {uploaded_file.name}")
elif os.path.exists(DEFAULT_EXCEL_FILE):
    data_source_key = "default"
    data_to_load = DEFAULT_EXCEL_FILE
    st.sidebar.info(f"Usando arquivo padrão: {os.path.basename(DEFAULT_EXCEL_FILE)}")
else:
    st.error("Nenhum arquivo de dados disponível. Faça o upload de um arquivo Excel ou certifique-se que o arquivo padrão existe.")
    st.stop()

# Carregar dados apenas se a fonte mudou ou não foram carregados ainda
if data_source_key != st.session_state["current_data_source_key"] or not st.session_state["data_loaded"]:
    if data_to_load:
        st.session_state["dataframe"] = load_data(data_to_load)
        st.session_state["current_data_source_key"] = data_source_key
        st.session_state["data_loaded"] = True
        if st.session_state["dataframe"] is not None:
            st.sidebar.success("Dados carregados com sucesso!")
        else:
            st.session_state["data_loaded"] = False
            st.sidebar.error("Falha ao carregar dados.")

df_full = st.session_state["dataframe"]

if df_full is None:
    st.warning("Os dados não puderam ser carregados. Verifique o arquivo ou a mensagem de erro acima.")
    st.stop()

# --- Barra de Busca e Filtros --- 
st.subheader("Buscar Cliente")
search_query = st.text_input("Digite o Nome ou CNPJ do cliente:", "", key="search_input")
search_button = st.button("Buscar", key="search_button")

st.sidebar.header("Filtros Gerais (Opcional)")
all_brands = sorted(df_full["Marca"].dropna().unique())
selected_brands = st.sidebar.multiselect("Filtrar por Marca:", all_brands)

all_segments = sorted(df_full["Segmento"].dropna().unique())
selected_segments = st.sidebar.multiselect("Filtrar por Segmento:", all_segments)

df_filtered = df_full.copy()
if selected_brands:
    df_filtered = df_filtered[df_filtered["Marca"].isin(selected_brands)]
if selected_segments:
    df_filtered = df_filtered[df_filtered["Segmento"].isin(selected_segments)]

# --- Exibição dos Resultados --- 
st.divider()

if search_button and search_query:
    st.subheader(f"Resultados para: {search_query}")
    query_normalized = search_query.replace(".", "").replace("/", "").replace("-", "")
    mask = (
        df_filtered["NOME DO CLIENTE"].str.contains(search_query, case=False, na=False) |
        df_filtered["CNPJ_NORMALIZED"].str.contains(query_normalized, case=False, na=False)
    )
    results_df = df_filtered[mask]

    if results_df.empty:
        st.warning("Cliente não encontrado na base de dados (ou nos filtros aplicados).")
    else:
        unique_cnpjs = results_df["CNPJ_NORMALIZED"].unique()

        if len(unique_cnpjs) > 1:
            st.info(f"Múltiplos clientes encontrados para \"{search_query}\". Exibindo o primeiro encontrado.")
            # Poderia listar os clientes aqui para seleção, mas vamos simplificar por enquanto
            target_cnpj_normalized = unique_cnpjs[0]
        elif len(unique_cnpjs) == 1:
            target_cnpj_normalized = unique_cnpjs[0]
        else:
             st.warning("Não foi possível identificar um CNPJ único para o cliente.")
             st.stop()

        client_df = results_df[results_df["CNPJ_NORMALIZED"] == target_cnpj_normalized].copy()

        if not client_df.empty:
            # Pegar dados do registro mais recente para informações estáticas
            latest_record = client_df.sort_values(by="Data emplacamento", ascending=False).iloc[0]
            client_name = latest_record["NOME DO CLIENTE"]
            client_cnpj_formatted = latest_record["CNPJ CLIENTE"] # Usar o CNPJ original formatado
            city_str = latest_record["NO_CIDADE"] if "NO_CIDADE" in latest_record and pd.notna(latest_record["NO_CIDADE"]) else "N/A"

            # Calcular estatísticas
            total_plated = len(client_df)
            last_plate_date_obj = client_df["Data emplacamento"].dropna().max()
            last_plate_date_str = last_plate_date_obj.strftime("%d/%m/%Y") if pd.notna(last_plate_date_obj) else "N/A"
            most_frequent_model = get_modes(client_df["Modelo"])
            most_frequent_brand = get_modes(client_df["Marca"])
            most_frequent_segment = get_modes(client_df["Segmento"])
            most_frequent_dealer = get_modes(client_df["Concessionário"])

            # --- Exibição dos Detalhes do Cliente --- 
            st.markdown(f"### Detalhes de: {client_name}")

            # Extrair informações adicionais (Endereço e Telefone - placeholder)
            client_address = latest_record["ENDEREÇO COMPLETO"] if "ENDEREÇO COMPLETO" in latest_record and pd.notna(latest_record["ENDEREÇO COMPLETO"]) else "N/A"
            # !!! CONFIRMAR NOME DA COLUNA DE TELEFONE COM O USUÁRIO !!!
            NOME_COLUNA_TELEFONE = "TELEFONE_PENDENTE" # Substituir pelo nome correto quando confirmado
            client_phone = latest_record[NOME_COLUNA_TELEFONE] if NOME_COLUNA_TELEFONE in latest_record and pd.notna(latest_record[NOME_COLUNA_TELEFONE]) else "N/A"

            col1_info, col2_info = st.columns(2)
            with col1_info:
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Nome do Cliente:</span>
                    <span class="value">{client_name}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">CNPJ:</span>
                    <span class="value">{client_cnpj_formatted}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Endereço Completo:</span>
                    <span class="value">{client_address}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Modelo(s) Mais Comprado(s):</span>
                    <span class="value">{format_list(most_frequent_model)}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Concessionária(s) Mais Frequente(s):</span>
                    <span class="value">{format_list(most_frequent_dealer)}</span>
                </div>
                """, unsafe_allow_html=True)

            with col2_info:
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Cidade:</span>
                    <span class="value">{city_str}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Telefone:</span>
                    <span class="value">{client_phone}</span>
                </div>
                """, unsafe_allow_html=True) # Telefone adicionado aqui
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Total Emplacado (na base):</span>
                    <span class="value">{total_plated}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Último Emplacamento:</span>
                    <span class="value">{last_plate_date_str}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Marca(s) Mais Comprada(s):</span>
                    <span class="value">{format_list(most_frequent_brand)}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Segmento(s) Mais Comprado(s):</span>
                    <span class="value">{format_list(most_frequent_segment)}</span>
                </div>
                """, unsafe_allow_html=True)

            st.divider()

            # --- Histórico e Oportunidade --- 
            st.markdown("### Histórico e Oportunidade")

            # Filtrar datas válidas para cálculo e gráfico
            valid_dates_df = client_df.dropna(subset=["Data emplacamento"])
            valid_purchase_dates = valid_dates_df["Data emplacamento"].tolist()

            prediction_text, predicted_date_obj = calculate_next_purchase_prediction(valid_purchase_dates)
            sales_pitch = get_sales_pitch(last_plate_date_obj, predicted_date_obj, total_plated)

            st.info(sales_pitch)
            st.markdown(f"**{prediction_text}**")

            # --- Gráfico de Histórico --- 
            if not valid_dates_df.empty:
                history_agg = valid_dates_df.copy()
                history_agg["Ano-Mês"] = history_agg["Data emplacamento"].dt.to_period("M").astype(str)
                purchases_per_month = history_agg.groupby("Ano-Mês").size().reset_index(name="Quantidade")
                purchases_per_month.sort_values("Ano-Mês", inplace=True)

                fig = px.bar(
                    purchases_per_month, 
                    x="Ano-Mês", 
                    y="Quantidade", 
                    title="Histórico de Emplacamentos (por Mês)",
                    labels={"Ano-Mês": "Mês", "Quantidade": "Nº de Emplacamentos"},
                    text="Quantidade"
                )
                fig.update_layout(
                    xaxis_title="",
                    yaxis_title="Quantidade",
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis={'type': 'category'}
                )
                fig.update_traces(
                    marker_color='#0055a4',
                    marker_line_color='#003366',
                    marker_line_width=1.5, 
                    opacity=0.8,
                    textposition='outside'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("Ver Tabela de Dados do Histórico"):
                    st.dataframe(client_df[['Data emplacamento', 'Marca', 'Modelo', 'Segmento', 'Concessionário']].sort_values(by="Data emplacamento", ascending=False), use_container_width=True)
            else:
                st.warning("Não há dados de emplacamento válidos para gerar o histórico gráfico.")
        else:
            st.warning("Não foram encontrados registros para o CNPJ identificado.")
else:
    # Mensagem inicial ou quando a busca está vazia
    st.info("Digite o nome ou CNPJ do cliente acima e clique em 'Buscar' para ver os detalhes.")

# --- Rodapé (Opcional) ---
st.sidebar.divider()
st.sidebar.markdown("Desenvolvido por Gabriel Lopes 💡")
