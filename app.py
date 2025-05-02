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

# --- Estilo CSS Customizado (Opcional, para refinamentos) ---
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

def load_data(file_path_or_buffer):
    """Carrega e pré-processa os dados do arquivo Excel."""
    try:
        df = pd.read_excel(file_path_or_buffer)

        # Limpeza e conversão de tipos
        df["Data emplacamento"] = pd.to_datetime(df["Data emplacamento"], errors="coerce", dayfirst=True)
        df["CNPJ CLIENTE"] = df["CNPJ CLIENTE"].astype(str).str.strip()
        df["NOME DO CLIENTE"] = df["NOME DO CLIENTE"].astype(str).str.strip()
        df["CNPJ_NORMALIZED"] = df["CNPJ CLIENTE"].str.replace(r"[.\\/-]", "", regex=True)
        df["Ano"] = df["Data emplacamento"].dt.year
        df["Mes"] = df["Data emplacamento"].dt.month
        # Remover linhas onde a data não pôde ser convertida (NaT)
        # df.dropna(subset=["Data emplacamento"], inplace=True)
        return df
    except FileNotFoundError:
        st.error(f"Erro: Arquivo Excel padrão não encontrado em {DEFAULT_EXCEL_FILE}. Faça o upload de um arquivo.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo Excel: {e}")
        return None

# --- Funções Auxiliares ---
def get_modes(series):
    """Retorna a moda (ou modas em caso de empate) de uma série."""
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
    """Formata uma lista para exibição."""
    if not items or items == ["N/A"]:
        return "N/A"
    return ", ".join(map(str, items))

def calculate_next_purchase_prediction(valid_purchase_dates):
    """Calcula a previsão da próxima compra (Mês/Ano)."""
    if not valid_purchase_dates or len(valid_purchase_dates) < 2:
        return "Previsão não disponível (histórico insuficiente).", None

    valid_purchase_dates.sort()
    last_purchase_date = valid_purchase_dates[-1]
    intervals_months = []
    for i in range(1, len(valid_purchase_dates)):
        # Usar relativedelta para cálculo mais preciso de meses
        delta = relativedelta(valid_purchase_dates[i], valid_purchase_dates[i-1])
        months_diff = delta.years * 12 + delta.months
        intervals_months.append(months_diff if months_diff > 0 else 1) # Mínimo 1 mês

    if not intervals_months:
         return "Previsão não disponível (apenas 1 compra).", last_purchase_date

    avg_interval_months = sum(intervals_months) / len(intervals_months)
    # Arredondar para o inteiro mais próximo
    predicted_next_date = last_purchase_date + relativedelta(months=int(round(avg_interval_months)))

    # Formatar previsão como Mês de Ano (em português)
    meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
    predicted_month_year = f"{meses[predicted_next_date.month - 1]} de {predicted_next_date.year}"
    prediction_text = f"Próxima compra provável em: **{predicted_month_year}**"

    return prediction_text, predicted_next_date

def get_sales_pitch(last_purchase_date, predicted_next_date, total_purchases):
    """Gera uma frase de vendas com base nas datas."""
    today = pd.Timestamp.now().normalize()
    if not last_purchase_date:
        return "Primeira vez? 🤔 Sem histórico de compras registrado para este cliente."

    months_since_last = relativedelta(today, last_purchase_date).years * 12 + relativedelta(today, last_purchase_date).months
    last_purchase_str = last_purchase_date.strftime("%d/%m/%Y")

    if predicted_next_date:
        months_to_next = relativedelta(predicted_next_date, today).years * 12 + relativedelta(predicted_next_date, today).months
        predicted_month_year = f"{['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'][predicted_next_date.month - 1]} de {predicted_next_date.year}"

        if months_to_next <= 0: # Já passou ou é este mês
            return f"🚨 **Atenção!** A compra prevista para **{predicted_month_year}** pode estar próxima ou já passou! Última compra em {last_purchase_str}. Contato urgente!"
        elif months_to_next <= 2:
            return f"📈 **Oportunidade Quente!** Próxima compra prevista para **{predicted_month_year}**. Ótimo momento para contato! Última compra em {last_purchase_str}."
        elif months_to_next <= 6:
            return f"🗓️ **Planeje-se!** Próxima compra prevista para **{predicted_month_year}**. Prepare sua abordagem! Última compra em {last_purchase_str}."
        else:
            return f"⏳ Compra prevista para **{predicted_month_year}**. Mantenha o relacionamento aquecido! Última compra em {last_purchase_str}."
    else: # Sem previsão, usar tempo desde a última compra
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

# --- Cabeçalho e Upload ---
col1_header, col2_header = st.columns([1, 3])
with col1_header:
    if os.path.exists(LOGO_COLOR_PATH):
        st.image(LOGO_COLOR_PATH, width=250) # Logo maior
    else:
        st.warning("Logo não encontrado.")
with col2_header:
    st.title("Consulta de Emplacamentos")
    st.markdown("**Ferramenta interna De Nigris** - Busque por cliente e veja o histórico e oportunidades.")

st.divider()

# --- Upload na Sidebar ---
st.sidebar.header("Atualizar Dados")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"])

# Determinar qual arquivo usar (upload ou padrão)
data_source = DEFAULT_EXCEL_FILE
if uploaded_file is not None:
    # Para usar o arquivo carregado, precisamos lê-lo em memória
    data_source = BytesIO(uploaded_file.getvalue())
    st.sidebar.success(f"Usando arquivo carregado: {uploaded_file.name}")
    # Limpar cache se um novo arquivo for carregado
    # Nota: Streamlit pode não limpar o cache automaticamente só com isso.
    # Uma abordagem mais robusta envolveria gerenciar o estado do arquivo.
    
elif not os.path.exists(DEFAULT_EXCEL_FILE):
    st.error("Nenhum arquivo de dados disponível. Faça o upload de um arquivo Excel na barra lateral.")
    st.stop() # Interrompe a execução se não houver dados
else:
    st.sidebar.info(f"Usando arquivo padrão: {os.path.basename(DEFAULT_EXCEL_FILE)}")

# Carregar os dados
df_full = load_data(data_source)

if df_full is None:
    st.stop() # Interrompe se o carregamento falhar

# --- Barra de Busca e Filtros --- 
st.subheader("Buscar Cliente")
search_query = st.text_input("Digite o Nome ou CNPJ do cliente:", "", key="search_input")
search_button = st.button("Buscar", key="search_button")

st.sidebar.header("Filtros Gerais (Opcional)")
# Adicionar filtros gerais aqui se necessário (ex: por marca, segmento, período)
# Exemplo:
all_brands = sorted(df_full["Marca"].dropna().unique())
selected_brands = st.sidebar.multiselect("Filtrar por Marca:", all_brands)

all_segments = sorted(df_full["Segmento"].dropna().unique())
selected_segments = st.sidebar.multiselect("Filtrar por Segmento:", all_segments)

# Aplicar filtros gerais (se selecionados)
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
        # Agrupar pelo CNPJ para tratar múltiplos resultados da busca inicial
        unique_cnpjs = results_df["CNPJ_NORMALIZED"].unique()

        if len(unique_cnpjs) > 1:
            st.info(f"Múltiplos clientes encontrados para '{search_query}'. Exibindo o primeiro:")
            # Poderia adicionar lógica para selecionar qual cliente exibir

        client_cnpj_normalized = unique_cnpjs[0]
        # Usar o DataFrame filtrado (df_filtered) para obter os dados completos do cliente
        client_data_df = df_filtered[df_filtered["CNPJ_NORMALIZED"] == client_cnpj_normalized].copy()

        if client_data_df.empty:
            st.error("Erro inesperado ao buscar dados completos do cliente.")
        else:
            # --- Processamento de Dados do Cliente Encontrado ---
            client_data_df.sort_values("Data emplacamento", ascending=False, inplace=True)
            latest_record = client_data_df.iloc[0]

            client_name = latest_record["NOME DO CLIENTE"]
            client_cnpj_formatted = latest_record["CNPJ CLIENTE"]
            city = latest_record["NO_CIDADE"]
            city_str = city if pd.notna(city) else "N/A"

            total_plated = len(client_data_df)
            
            # Trabalhar apenas com datas válidas para cálculos de data
            valid_dates_df = client_data_df.dropna(subset=["Data emplacamento"])
            valid_purchase_dates = valid_dates_df["Data emplacamento"].tolist()
            
            last_plate_date_obj = valid_dates_df["Data emplacamento"].max() if not valid_dates_df.empty else None
            last_plate_date_str = last_plate_date_obj.strftime("%d/%m/%Y") if last_plate_date_obj else "N/A"

            # Calcular modas usando todos os dados do cliente
            most_frequent_model = get_modes(client_data_df["Modelo"])
            most_frequent_brand = get_modes(client_data_df["Marca"])
            most_frequent_dealer = get_modes(client_data_df["Concessionário"])
            most_frequent_segment = get_modes(client_data_df["Segmento"])

            # --- Exibição dos Detalhes do Cliente --- 
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

            st.divider()

            # --- Histórico e Oportunidade --- 
            st.markdown("### Histórico e Oportunidade")

            # Calcular Previsão e Frase de Vendas
            prediction_text, predicted_date_obj = calculate_next_purchase_prediction(valid_purchase_dates)
            sales_pitch = get_sales_pitch(last_plate_date_obj, predicted_date_obj, total_plated)

            st.info(sales_pitch) # Usar st.info para destaque
            st.markdown(f"**{prediction_text}**")

            # --- Gráfico de Histórico --- 
            if not valid_dates_df.empty:
                # Agrupar por Ano-Mês para gráfico de linha do tempo
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
                    plot_bgcolor='rgba(0,0,0,0)', # Fundo transparente
                    xaxis={'type': 'category'} # Tratar eixo X como categoria
                )
                fig.update_traces(
                    marker_color='#0055a4', # Cor das barras
                    marker_line_color='#003366',
                    marker_line_width=1.5, 
                    opacity=0.8,
                    textposition='outside'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Tabela com detalhes (opcional, pode ser colocada em expander)
                with st.expander("Ver Tabela Detalhada do Histórico"):
                    st.dataframe(client_data_df[["Data emplacamento", "Marca", "Modelo", "Segmento", "Concessionário"]].sort_values("Data emplacamento", ascending=False), use_container_width=True)

            else:
                st.warning("Não há histórico de compras com datas válidas para exibir o gráfico.")

elif search_button and not search_query:
    st.warning("Por favor, digite um nome ou CNPJ para buscar.")
else:
    # Mensagem inicial ou visão geral
    st.markdown("### Visão Geral da Base")
    st.info("Utilize a busca acima para encontrar um cliente específico ou os filtros na barra lateral para explorar os dados.")
    
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Total de Registros", len(df_full))
    col_b.metric("Clientes Únicos (por CNPJ)", df_full["CNPJ_NORMALIZED"].nunique())
    if not df_full.empty and pd.notna(df_full["Data emplacamento"].max()):
        last_update_date = df_full["Data emplacamento"].max().strftime("%d/%m/%Y")
        col_c.metric("Último Emplacamento na Base", last_update_date)
    else:
        col_c.metric("Último Emplacamento na Base", "N/A")

    # Gráfico geral (ex: Top 5 Marcas)
    if not df_filtered.empty:
        st.markdown("#### Top 5 Marcas (Filtro Aplicado)")
        top_brands = df_filtered["Marca"].value_counts().nlargest(5).reset_index()
        top_brands.columns = ["Marca", "Quantidade"]
        fig_top_brands = px.bar(top_brands, x="Marca", y="Quantidade", title="Top 5 Marcas", text="Quantidade")
        fig_top_brands.update_layout(xaxis_title="", yaxis_title="Quantidade", plot_bgcolor='rgba(0,0,0,0)')
        fig_top_brands.update_traces(marker_color='#0055a4', textposition='outside')
        st.plotly_chart(fig_top_brands, use_container_width=True)

# --- Rodapé (Opcional) ---
st.sidebar.divider()
st.sidebar.markdown("Desenvolvido por Gabriel Lopes")

