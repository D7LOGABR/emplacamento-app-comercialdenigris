# 🛠️ Bloco de imports
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

# --- Função para carregar dados ---
def load_data(file_path_or_buffer):
    try:
        df = pd.read_excel(file_path_or_buffer)
        # Normaliza nome da coluna PLACA
        placa_colunas = ["PLACA", "Placa", "placa", "PLACA VEÍCULO", "Placa Veículo"]
        for col in placa_colunas:
            if col in df.columns:
                df.rename(columns={col: "PLACA"}, inplace=True)
                break
        if "PLACA" not in df.columns:
            df["PLACA"] = "N/A"
        df["PLACA"] = df["PLACA"].astype(str).str.strip().str.upper()

        df["Data emplacamento"] = pd.to_datetime(df["Data emplacamento"], errors="coerce", dayfirst=True)
        df["CNPJ CLIENTE"] = df["CNPJ CLIENTE"].astype(str).str.strip()
        df["NOME DO CLIENTE"] = df["NOME DO CLIENTE"].astype(str).str.strip()
        df["CNPJ_NORMALIZED"] = df["CNPJ CLIENTE"].str.replace(r"[.\\/-]", "", regex=True)
        df["Ano"] = df["Data emplacamento"].dt.year
        df["Mes"] = df["Data emplacamento"].dt.month
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return None

# --- Funções auxiliares ---
def get_modes(series):
    cleaned = series.dropna().astype(str)
    if cleaned.empty:
        return ["N/A"]
    contagem = Counter(cleaned)
    max_count = contagem.most_common(1)[0][1]
    return sorted([k for k, v in contagem.items() if v == max_count])

def format_list(lst):
    return ", ".join(lst) if lst and lst != ["N/A"] else "N/A"

def calculate_next_purchase_prediction(dates):
    if len(dates) < 2:
        return "Previsão não disponível (histórico insuficiente).", None
    dates.sort()
    intervals = [
        relativedelta(dates[i], dates[i-1]).years * 12 + relativedelta(dates[i], dates[i-1]).months or 1
        for i in range(1, len(dates))
    ]
    avg_months = round(sum(intervals) / len(intervals))
    next_date = dates[-1] + relativedelta(months=avg_months)
    nome_mes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    return f"Próxima compra provável em: **{nome_mes[next_date.month-1]} de {next_date.year}**", next_date

def get_sales_pitch(last_date, predicted_date, total):
    hoje = pd.Timestamp.now().normalize()
    if not last_date:
        return "Primeira vez? 🤔 Sem histórico de compras registrado para este cliente."
    meses_desde = relativedelta(hoje, last_date).years * 12 + relativedelta(hoje, last_date).months
    data_str = last_date.strftime("%d/%m/%Y")
    if predicted_date:
        meses_ate = relativedelta(predicted_date, hoje).years * 12 + relativedelta(predicted_date, hoje).months
        nome_mes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        desc = f"{nome_mes[predicted_date.month-1]} de {predicted_date.year}"
        if meses_ate <= 0:
            return f"🚨 **Atenção!** A compra prevista para **{desc}** pode estar próxima ou já passou! Última compra em {data_str}."
        elif meses_ate <= 2:
            return f"📈 **Oportunidade Quente!** Próxima compra prevista para **{desc}**. Última compra em {data_str}."
        elif meses_ate <= 6:
            return f"🗓️ **Planeje-se!** Próxima compra prevista para **{desc}**. Última compra em {data_str}."
        else:
            return f"⏳ Compra prevista para **{desc}**. Última compra em {data_str}."
    else:
        if meses_desde >= 18:
            return f"🚨 Alerta de sumiço! Faz {meses_desde} meses desde a última compra ({data_str})."
        elif meses_desde >= 12:
            return f"👀 E aí, sumido! Faz {meses_desde} meses desde a última compra ({data_str})."
        elif meses_desde >= 6:
            return f"⏳ Já se passaram {meses_desde} meses... Última compra em {data_str}."
        elif total > 3:
            return f"👍 Cliente fiel! Última compra em {data_str}."
        else:
            return f"✅ Compra recente ({data_str})."

# --- Interface Principal ---
col1, col2 = st.columns([1, 3])
with col1:
    if os.path.exists(LOGO_COLOR_PATH):
        st.image(LOGO_COLOR_PATH, width=250)
with col2:
    st.title("Consulta de Emplacamentos")
    st.markdown("Ferramenta interna **Comercial De Nigris** – Busque por cliente, placa ou CNPJ.")

st.divider()

# --- Upload de arquivo ---
st.sidebar.header("📤 Atualizar Dados")
uploaded_file = st.sidebar.file_uploader("Arquivo Excel (.xlsx)", type=["xlsx"])
if "last_uploaded_file_name" not in st.session_state:
    st.session_state["last_uploaded_file_name"] = None

if uploaded_file:
    if uploaded_file.name != st.session_state["last_uploaded_file_name"]:
        st.session_state["last_uploaded_file_name"] = uploaded_file.name
    df_full = load_data(BytesIO(uploaded_file.getvalue()))
    st.sidebar.success(f"Usando arquivo: {uploaded_file.name}")
else:
    if not os.path.exists(DEFAULT_EXCEL_FILE):
        st.error("Arquivo padrão não encontrado.")
        st.stop()
    df_full = load_data(DEFAULT_EXCEL_FILE)
    st.sidebar.info("Usando arquivo padrão")

if df_full is None:
    st.stop()

# --- Filtros ---
st.sidebar.header("🔍 Filtros")
marca_opcoes = sorted(df_full["Marca"].dropna().unique())
segmento_opcoes = sorted(df_full["Segmento"].dropna().unique())
marcas_selecionadas = st.sidebar.multiselect("Filtrar por Marca:", marca_opcoes)
segmentos_selecionados = st.sidebar.multiselect("Filtrar por Segmento:", segmento_opcoes)

df_filtered = df_full.copy()
if marcas_selecionadas:
    df_filtered = df_filtered[df_filtered["Marca"].isin(marcas_selecionadas)]
if segmentos_selecionados:
    df_filtered = df_filtered[df_filtered["Segmento"].isin(segmentos_selecionados)]

# --- Barra de Busca ---
st.subheader("🔎 Buscar Cliente, Placa ou CNPJ")
search_query = st.text_input("Digite o Nome, CNPJ ou Placa:", "")
search_button = st.button("Buscar")

if search_button and search_query:
    query_norm = search_query.replace(".", "").replace("/", "").replace("-", "").upper()
    mask = (
        df_filtered["NOME DO CLIENTE"].str.contains(search_query, case=False, na=False) |
        df_filtered["CNPJ_NORMALIZED"].str.contains(query_norm, na=False) |
        df_filtered["PLACA"].str.contains(query_norm, na=False)
    )
    results_df = df_filtered[mask]

    if results_df.empty:
        st.warning("Nenhum resultado encontrado.")
    else:
        st.success(f"{len(results_df)} registro(s) encontrado(s).")
        st.dataframe(results_df)

elif search_button and not search_query:
    st.warning("Por favor, digite um nome, CNPJ ou placa para buscar.")

else:
    # --- Resumo Geral ---
    st.divider()
    st.subheader("📊 Resumo Geral")
    df_display = df_filtered.copy()
    total_emplacamentos = len(df_display)
    clientes_unicos = df_display["CNPJ_NORMALIZED"].nunique()
    anos = df_display["Ano"].dropna()
    primeiro_ano = int(anos.min()) if not anos.empty else "N/A"
    ultimo_ano = int(anos.max()) if not anos.empty else "N/A"

    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Emplacamentos", f"{total_emplacamentos:,}".replace(",", "."))
    col2.metric("Clientes Únicos", f"{clientes_unicos:,}".replace(",", "."))
    col3.metric("Período", f"{primeiro_ano} - {ultimo_ano}")

    st.markdown("#### Emplacamentos por Ano")
    chart_ano = df_display["Ano"].value_counts().sort_index()
    st.bar_chart(chart_ano)

    st.markdown("#### Emplacamentos por Marca e Ano")
    marca_ano = df_display.groupby(["Ano", "Marca"]).size().reset_index(name="Qtd")
    if not marca_ano.empty:
        tabela = marca_ano.pivot(index="Marca", columns="Ano", values="Qtd").fillna(0).astype(int)
        st.dataframe(tabela, use_container_width=True)
    else:
        st.info("Sem dados para exibir.")

# --- Rodapé ---
st.sidebar.divider()
if os.path.exists(LOGO_WHITE_PATH):
    st.sidebar.image(LOGO_WHITE_PATH, use_container_width=True)
st.sidebar.caption("© Comercial De Nigris")
