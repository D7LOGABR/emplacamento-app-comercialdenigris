import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta
from collections import Counter
import os
from io import BytesIO

# --- Configuração da Página ---
st.set_page_config(
    page_title="Emplacamentos Comercial De Nigris",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Estilo CSS Customizado ---
st.markdown("""
<style>
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
    }
    .info-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #0055a4;
    }
    .info-card .label {
        font-weight: bold;
        color: #003366;
        display: block;
        margin-bottom: 3px;
    }
    .info-card .value {
        color: #333;
    }
    h1, h2, h3 {
        color: #003366;
    }
    .stButton>button {
        background-color: #0055a4;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {
        background-color: #003366;
        color: white;
    }
    .stAlert p {
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Constantes e Caminhos ---
DATA_DIR = "data"
DEFAULT_EXCEL_FILE = os.path.join(DATA_DIR, "EMPLACAMENTO ANUAL - CAMINHÕES.xlsx")
LOGO_COLOR_PATH = os.path.join(DATA_DIR, "logo_denigris_colorido.png")
LOGO_WHITE_PATH = os.path.join(DATA_DIR, "logo_denigris_branco.png")

# --- Funções de Carregamento e Cache de Dados ---
def load_data(file_path_or_buffer):
    """Carrega e pré-processa os dados do arquivo Excel."""
    try:
        df = pd.read_excel(file_path_or_buffer)
        df["Data emplacamento"] = pd.to_datetime(df["Data emplacamento"], errors="coerce", dayfirst=True)
        df["CNPJ CLIENTE"] = df["CNPJ CLIENTE"].astype(str).str.strip()
        df["NOME DO CLIENTE"] = df["NOME DO CLIENTE"].astype(str).str.strip()
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
        predicted_month_year = f"{['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][predicted_next_date.month - 1]} de {predicted_next_date.year}"

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
col1_header, col2_header = st.columns([1, 3])
with col1_header:
    if os.path.exists(LOGO_COLOR_PATH):
        st.image(LOGO_COLOR_PATH, width=250)
    else:
        st.warning("Logo não encontrado.")
with col2_header:
    st.title("Consulta de Emplacamentos")
    st.markdown("**Ferramenta interna Comercial De Nigris** - Busque por cliente, placa ou CNPJ e veja o histórico e oportunidades.")

st.divider()

# --- Upload na Sidebar ---
st.sidebar.header("Atualizar Dados")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

if "last_uploaded_file_name" not in st.session_state:
    st.session_state["last_uploaded_file_name"] = None

if uploaded_file is not None:
    if uploaded_file.name != st.session_state["last_uploaded_file_name"]:
        st.session_state["last_uploaded_file_name"] = uploaded_file.name
        df_full = load_data(BytesIO(uploaded_file.getvalue()))
        st.sidebar.success(f"Usando novo arquivo: {uploaded_file.name}")
    else:
        st.sidebar.info(f"Arquivo já carregado: {uploaded_file.name}")
        df_full = load_data(BytesIO(uploaded_file.getvalue()))
else:
    if not os.path.exists(DEFAULT_EXCEL_FILE):
        st.error("Nenhum arquivo de dados disponível. Faça o upload de um arquivo Excel.")
        st.stop()
    df_full = load_data(DEFAULT_EXCEL_FILE)
    st.sidebar.info(f"Usando arquivo padrão: {os.path.basename(DEFAULT_EXCEL_FILE)}")

if df_full is None:
    st.stop()

# --- Barra de Busca e Filtros ---
st.subheader("Buscar Cliente, Placa ou CNPJ")
search_query = st.text_input("Digite o Nome, CNPJ ou Placa do cliente:", "", key="search_input")
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

st.divider()

if search_button and search_query:
    st.subheader(f"Resultados para: {search_query}")
    query_normalized = search_query.replace(".", "").replace("/", "").replace("-", "")
    # Busca por Nome, CNPJ (normalizado) ou PLACA
    mask = (
        df_filtered["NOME DO CLIENTE"].str.contains(search_query, case=False, na=False) |
        df_filtered["CNPJ_NORMALIZED"].str.contains(query_normalized, case=False, na=False) |
        df_filtered["PLACA"].str.contains(search_query, case=False, na=False)
    )
    results_df = df_filtered[mask]

    if results_df.empty:
        st.warning("Cliente ou placa não encontrado na base de dados (ou nos filtros aplicados).")
    else:
        unique_cnpjs = results_df["CNPJ_NORMALIZED"].unique()
        if len(unique_cnpjs) > 1:
            st.info(f"Múltiplos clientes encontrados para '{search_query}'. Exibindo o primeiro:")

        client_cnpj_normalized = unique_cnpjs[0]
        client_data_df = df_filtered[df_filtered["CNPJ_NORMALIZED"] == client_cnpj_normalized].copy()

        if client_data_df.empty:
            st.error("Erro inesperado ao buscar dados completos do cliente.")
        else:
            client_data_df.sort_values("Data emplacamento", ascending=False, inplace=True)
            latest_record = client_data_df.iloc[0]
            client_name = latest_record["NOME DO CLIENTE"]
            client_cnpj_formatted = latest_record["CNPJ CLIENTE"]
            city = latest_record["NO_CIDADE"]
            city_str = city if pd.notna(city) else "N/A"

            total_plated = len(client_data_df)
            valid_dates_df = client_data_df.dropna(subset=["Data emplacamento"])
            valid_purchase_dates = valid_dates_df["Data emplacamento"].tolist()
            last_plate_date_obj = valid_dates_df["Data emplacamento"].max() if not valid_dates_df.empty else None
            last_plate_date_str = last_plate_date_obj.strftime("%d/%m/%Y") if last_plate_date_obj else "N/A"

            most_frequent_model = get_modes(client_data_df["Modelo"])
            most_frequent_brand = get_modes(client_data_df["Marca"])
            most_frequent_dealer = get_modes(client_data_df["Concessionário"])
            most_frequent_segment = get_modes(client_data_df["Segmento"])

            st.markdown(f"### Detalhes de: {client_name}")
            col1_info, col2_info = st.columns(2)
            with col1_info:
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">CNPJ:</span>
                    <span class="value">{client_cnpj_formatted}</span>
                </div>
                """, unsafe_allow_html=True)
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Cidade:</span>
                    <span class="value">{city_str}</span>
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
                
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">CNPJ:</span>
                    <span class="value">{client_cnpj}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Endereço:</span>
                    <span class="value">{client_address}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Modelo(s) Mais Comprado(s):</span>
                    <span class="value">{format_list(preferred_models)}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Concessionária(s) Mais Frequente(s):</span>
                    <span class="value">{format_list(preferred_concessionarias)}</span>
                </div>
                """, unsafe_allow_html=True)
                
            with col_right:
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Cidade:</span>
                    <span class="value">{client_city}</span>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"""
                <div class="info-card">
                    <span class="label">Telefone:</span>
                    <span class="value">{client_phone}</span>
                </div>
                """, unsafe_allow_html=True)
                
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
                    <span class="value">{format_list(preferred_brands)}</span>
                </div>
                """, unsafe_allow_html=True)
            
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
            detail_df = client_df_sorted[["Data emplacamento", "Chassi", "Modelo", NOME_COLUNA_CONCESSIONARIO]].copy()
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
st.sidebar.caption("© Comercial De Nigris")
