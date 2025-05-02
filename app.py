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
UPLOADED_TEMP_FILE = "/tmp/streamlit_uploaded_data.xlsx" # Local temporário para o arquivo carregado

# --- Funções de Carregamento de Dados ---
def load_data(file_path_or_buffer):
    """Carrega e pré-processa os dados do arquivo Excel."""
    try:
        df = pd.read_excel(file_path_or_buffer)

        # Limpeza e conversão de tipos (com dayfirst=True)
        df["Data emplacamento"] = pd.to_datetime(df["Data emplacamento"], errors="coerce", dayfirst=True)
        df["CNPJ CLIENTE"] = df["CNPJ CLIENTE"].astype(str).str.strip()
        df["NOME DO CLIENTE"] = df["NOME DO CLIENTE"].astype(str).str.strip()

        # Colunas opcionais (Endereço e Telefone)
        NOME_COLUNA_ENDERECO = "ENDEREÇO COMPLETO"
        NOME_COLUNA_TELEFONE = "TELEFONE1" # <<< Substitua "TELEFONE1" pelo nome real da coluna no Excel

        if NOME_COLUNA_ENDERECO in df.columns:
            df[NOME_COLUNA_ENDERECO] = df[NOME_COLUNA_ENDERECO].astype(str).str.strip()
        else:
            df[NOME_COLUNA_ENDERECO] = "N/A"

        if NOME_COLUNA_TELEFONE in df.columns and NOME_COLUNA_TELEFONE != "TELEFONE1":
            df[NOME_COLUNA_TELEFONE] = df[NOME_COLUNA_TELEFONE].astype(str).str.strip()
        else:
            # Criar coluna vazia se não existir ou se o nome não foi substituído
            df[NOME_COLUNA_TELEFONE] = "N/A"

        df["CNPJ_NORMALIZED"] = df["CNPJ CLIENTE"].str.replace(r"[.\\/-]", "", regex=True)
        df["Ano"] = df["Data emplacamento"].dt.year
        df["Mes"] = df["Data emplacamento"].dt.month

        # Remover linhas onde 'Ano' é NaN (resultante de datas inválidas)
        df.dropna(subset=["Ano"], inplace=True)
        df["Ano"] = df["Ano"].astype(int)

        return df
    except FileNotFoundError:
        # Este erro só deve ocorrer se o arquivo Excel (padrão ou temp) não for encontrado
        st.error(f"Erro: Arquivo Excel não encontrado em {file_path_or_buffer}. Verifique o caminho ou faça upload.")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar ou processar o arquivo Excel ({os.path.basename(str(file_path_or_buffer))}): {e}")
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
        # Calcular diferença em meses corretamente
        delta = relativedelta(valid_purchase_dates[i], valid_purchase_dates[i-1])
        months_diff = delta.years * 12 + delta.months
        # Adicionar também a diferença em dias para desempate (evitar intervalo 0 se compras no mesmo mês)
        days_diff = delta.days
        if months_diff > 0:
            intervals_months.append(months_diff)
        elif months_diff == 0 and days_diff > 0: # Compras no mesmo mês, mas dias diferentes
             intervals_months.append(0.5) # Usar um valor pequeno > 0
        # Ignorar se for exatamente a mesma data

    if not intervals_months:
         return "Previsão não disponível (compras muito próximas ou única).", last_purchase_date

    avg_interval_months = sum(intervals_months) / len(intervals_months)

    # Evitar previsão muito curta se intervalo médio for < 1 mês
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

    # Certificar que last_purchase_date é um Timestamp
    if not isinstance(last_purchase_date, pd.Timestamp):
        last_purchase_date = pd.to_datetime(last_purchase_date)

    months_since_last = relativedelta(today, last_purchase_date).years * 12 + relativedelta(today, last_purchase_date).months
    last_purchase_str = last_purchase_date.strftime("%d/%m/%Y")

    if predicted_next_date and isinstance(predicted_next_date, pd.Timestamp):
        months_to_next = relativedelta(predicted_next_date, today).years * 12 + relativedelta(predicted_next_date, today).months
        days_to_next = relativedelta(predicted_next_date, today).days # Considerar dias

        predicted_month_year = f"{["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"][predicted_next_date.month - 1]} de {predicted_next_date.year}"

        # Ajuste para considerar dias quando meses for 0
        if months_to_next < 0 or (months_to_next == 0 and days_to_next < 0):
            return f"🚨 **Atenção!** A compra prevista para **{predicted_month_year}** pode estar próxima ou já passou! Última compra em {last_purchase_str}. Contato urgente!"
        elif months_to_next <= 2:
            return f"📈 **Oportunidade Quente!** Próxima compra prevista para **{predicted_month_year}**. Ótimo momento para contato! Última compra em {last_purchase_str}."
        elif months_to_next <= 6:
            return f"🗓️ **Planeje-se!** Próxima compra prevista para **{predicted_month_year}**. Prepare sua abordagem! Última compra em {last_purchase_str}."
        else:
            return f"⏳ Compra prevista para **{predicted_month_year}**. Mantenha o relacionamento aquecido! Última compra em {last_purchase_str}."
    else:
        # Fallback se não houver previsão
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

# --- Upload e Carregamento de Dados com Gerenciamento de Estado ---
st.sidebar.header("Atualizar Dados")
uploaded_file = st.sidebar.file_uploader("Selecione o arquivo Excel (.xlsx)", type=["xlsx"], key="file_uploader")

# Inicializar estado da sessão se necessário
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False
if "uploaded_file_path" not in st.session_state:
    st.session_state["uploaded_file_path"] = None # Armazena o caminho do arquivo temporário
if "dataframe" not in st.session_state:
    st.session_state["dataframe"] = None

data_to_load = None
load_trigger = None # Para saber se precisamos carregar/recarregar

# 1. Verificar se um NOVO arquivo foi carregado
if uploaded_file is not None:
    try:
        # Salvar o conteúdo do arquivo carregado no caminho temporário
        with open(UPLOADED_TEMP_FILE, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Se o salvamento foi bem-sucedido, atualizar o estado
        if st.session_state.get("uploaded_file_path") != UPLOADED_TEMP_FILE or not st.session_state.get("data_loaded"):
            st.session_state["uploaded_file_path"] = UPLOADED_TEMP_FILE
            data_to_load = UPLOADED_TEMP_FILE
            load_trigger = "new_upload"
            st.sidebar.success(f"Arquivo 	'{uploaded_file.name}	' carregado e salvo temporariamente.")
        else:
             # Mesmo arquivo carregado novamente, não precisa recarregar se já carregado
             data_to_load = st.session_state["uploaded_file_path"]
             if not st.session_state.get("data_loaded"):
                 load_trigger = "reload_uploaded"
    except Exception as e:
        st.sidebar.error(f"Erro ao salvar o arquivo carregado: {e}")
        # Tentar continuar com o que estava antes ou o padrão
        if st.session_state.get("uploaded_file_path") and os.path.exists(st.session_state["uploaded_file_path"]):
             data_to_load = st.session_state["uploaded_file_path"]
             if not st.session_state.get("data_loaded"):
                 load_trigger = "reload_uploaded_fallback"
        elif os.path.exists(DEFAULT_EXCEL_FILE):
             data_to_load = DEFAULT_EXCEL_FILE
             if not st.session_state.get("data_loaded"):
                 load_trigger = "load_default_fallback"
        else:
             data_to_load = None

# 2. Se nenhum arquivo novo foi carregado, decidir qual usar
if data_to_load is None: # Só entra aqui se uploaded_file is None ou se o upload falhou/era repetido
    if st.session_state.get("uploaded_file_path") and os.path.exists(st.session_state["uploaded_file_path"]):
        # Usar o arquivo temporário salvo anteriormente, se existir
        data_to_load = st.session_state["uploaded_file_path"]
        if not st.session_state.get("data_loaded"):
            load_trigger = "reload_existing_uploaded"
            st.sidebar.info("Usando arquivo carregado anteriormente.")
    elif os.path.exists(DEFAULT_EXCEL_FILE):
        # Usar o arquivo padrão
        data_to_load = DEFAULT_EXCEL_FILE
        # Se estávamos usando um arquivo carregado antes, limpar o caminho
        if st.session_state.get("uploaded_file_path") is not None:
             st.session_state["uploaded_file_path"] = None
        if not st.session_state.get("data_loaded"):
             load_trigger = "load_default"
             st.sidebar.info(f"Usando arquivo padrão: {os.path.basename(DEFAULT_EXCEL_FILE)}")
    else:
        # Nenhum arquivo disponível
        st.error("Nenhum arquivo de dados disponível. Faça o upload de um arquivo Excel ou certifique-se que o arquivo padrão existe.")
        st.stop()

# 3. Carregar os dados se necessário
if load_trigger and data_to_load:
    st.session_state["dataframe"] = load_data(data_to_load)
    st.session_state["data_loaded"] = True
    if st.session_state["dataframe"] is not None:
        st.sidebar.success("Dados carregados/atualizados!")
        # Forçar rerender pode não ser necessário aqui, mas pode ajudar
        # st.experimental_rerun()
    else:
        st.session_state["data_loaded"] = False # Marcar como falha
        st.sidebar.error("Falha ao carregar/atualizar dados.")
        # Limpar o caminho se o carregamento do arquivo temporário falhar
        if data_to_load == st.session_state.get("uploaded_file_path"):
            st.session_state["uploaded_file_path"] = None

# Usar o dataframe do estado da sessão
df_full = st.session_state.get("dataframe")

if df_full is None or df_full.empty:
    st.warning("Os dados não puderam ser carregados ou estão vazios. Verifique o arquivo ou a mensagem de erro acima.")
    st.stop()

# --- PAINEL DE RESUMO INICIAL ---
st.subheader("Resumo Geral da Base de Dados")

# Calcular estatísticas gerais do df_full
total_emplacamentos = len(df_full)
total_clientes_unicos = df_full["CNPJ_NORMALIZED"].nunique()
primeiro_ano = df_full["Ano"].min()
ultimo_ano = df_full["Ano"].max()

col_resumo1, col_resumo2, col_resumo3 = st.columns(3)
with col_resumo1:
    st.metric(label="Total de Emplacamentos Registrados", value=f"{total_emplacamentos:,}".replace(",", "."))
with col_resumo2:
    st.metric(label="Total de Clientes Únicos", value=f"{total_clientes_unicos:,}".replace(",", "."))
with col_resumo3:
    st.metric(label="Período Coberto", value=f"{primeiro_ano} - {ultimo_ano}")

st.markdown("#### Emplacamentos por Ano")
emplacamentos_por_ano = df_full["Ano"].value_counts().sort_index()
if not emplacamentos_por_ano.empty:
    st.bar_chart(emplacamentos_por_ano)
else:
    st.info("Não há dados de emplacamento por ano para exibir.")

st.markdown("#### Emplacamentos por Marca e Ano")
emplacamentos_marca_ano = df_full.groupby(["Ano", "Marca"]).size().reset_index(name="Quantidade")
if not emplacamentos_marca_ano.empty:
    # Pivotar para formato wide para possível visualização ou tabela
    pivot_marca_ano = emplacamentos_marca_ano.pivot(index="Marca", columns="Ano", values="Quantidade").fillna(0).astype(int)
    st.dataframe(pivot_marca_ano, use_container_width=True)

    # Gráfico opcional (pode ficar muito poluído com muitas marcas/anos)
    # fig_marca_ano = px.bar(emplacamentos_marca_ano, x='Ano', y='Quantidade', color='Marca',
    #                        title='Emplacamentos por Marca ao Longo dos Anos', barmode='group')
    # st.plotly_chart(fig_marca_ano, use_container_width=True)
else:
    st.info("Não há dados de emplacamento por marca e ano para exibir.")

st.divider() # Divisor entre resumo e busca

# --- Barra de Busca e Filtros --- 
st.subheader("Buscar Cliente Específico")
search_query = st.text_input("Digite o Nome ou CNPJ do cliente:", "", key="search_input")
search_button = st.button("Buscar", key="search_button")

st.sidebar.header("Filtros Gerais (Afetam a Busca)")
all_brands = sorted(df_full["Marca"].dropna().unique())
selected_brands = st.sidebar.multiselect("Filtrar por Marca:", all_brands)

all_segments = sorted(df_full["Segmento"].dropna().unique())
selected_segments = st.sidebar.multiselect("Filtrar por Segmento:", all_segments)

df_filtered = df_full.copy() # Começa com tudo

# Aplica filtros SE eles foram selecionados
if selected_brands:
    df_filtered = df_filtered[df_filtered["Marca"].isin(selected_brands)]
if selected_segments:
    df_filtered = df_filtered[df_filtered["Segmento"].isin(selected_segments)]

# --- Exibição dos Resultados da Busca --- 

if search_button and search_query:
    st.markdown(f"### Resultados da Busca por: '{search_query}'")
    # Normaliza a query para busca em CNPJ
    query_normalized = ''.join(filter(str.isdigit, str(search_query)))

    mask = (
        df_filtered["NOME DO CLIENTE"].str.contains(search_query, case=False, na=False)
    )
    # Adiciona busca por CNPJ normalizado apenas se a query parecer um CNPJ
    if query_normalized and len(query_normalized) > 5: # Heurística simples
         mask = mask | df_filtered["CNPJ_NORMALIZED"].str.contains(query_normalized, case=False, na=False)

    results_df = df_filtered[mask]

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
            # Ordenar por data para pegar o registro mais recente para dados cadastrais
            client_df_sorted = client_df.sort_values(by="Data emplacamento", ascending=False)
            latest_record = client_df_sorted.iloc[0]

            # Pegar dados do registro mais recente
            client_name = latest_record["NOME DO CLIENTE"]
            client_cnpj_formatted = latest_record["CNPJ CLIENTE"]
            city_str = latest_record["NO_CIDADE"] if "NO_CIDADE" in latest_record and pd.notna(latest_record["NO_CIDADE"]) else "N/A"
            client_address = latest_record[NOME_COLUNA_ENDERECO]
            client_phone = latest_record[NOME_COLUNA_TELEFONE]

            # Calcular estatísticas de todo o histórico do cliente
            total_plated = len(client_df)
            last_plate_date_obj = client_df["Data emplacamento"].dropna().max()
            last_plate_date_str = last_plate_date_obj.strftime("%d/%m/%Y") if pd.notna(last_plate_date_obj) else "N/A"
            most_frequent_model = get_modes(client_df["Modelo"])
            most_frequent_brand = get_modes(client_df["Marca"])
            most_frequent_segment = get_modes(client_df["Segmento"])
            most_frequent_dealer = get_modes(client_df["Concessionário"])

            st.markdown(f"#### Detalhes de: {client_name}")

            col1_info, col2_info = st.columns(2)
            with col1_info:
                st.markdown(f"""<div class="info-card"><span class="label">Nome do Cliente:</span><span class="value">{client_name}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">CNPJ:</span><span class="value">{client_cnpj_formatted}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Endereço:</span><span class="value">{client_address}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Modelo(s) Mais Comprado(s):</span><span class="value">{format_list(most_frequent_model)}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Concessionária(s) Mais Frequente(s):</span><span class="value">{format_list(most_frequent_dealer)}</span></div>""", unsafe_allow_html=True)

            with col2_info:
                st.markdown(f"""<div class="info-card"><span class="label">Cidade:</span><span class="value">{city_str}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Telefone:</span><span class="value">{client_phone}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Total Emplacado (na base):</span><span class="value">{total_plated}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Último Emplacamento:</span><span class="value">{last_plate_date_str}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Marca(s) Mais Comprada(s):</span><span class="value">{format_list(most_frequent_brand)}</span></div>""", unsafe_allow_html=True)
                st.markdown(f"""<div class="info-card"><span class="label">Segmento(s) Mais Comprado(s):</span><span class="value">{format_list(most_frequent_segment)}</span></div>""", unsafe_allow_html=True)

            st.divider()

            # --- Gráfico e Previsão ---
            st.markdown("#### Histórico e Previsão de Compra")

            # Preparar dados para o gráfico (contagem por mês/ano)
            client_df['AnoMes'] = client_df['Data emplacamento'].dt.to_period('M')
            purchase_history = client_df.groupby('AnoMes').size().reset_index(name='Quantidade')
            purchase_history['AnoMes'] = purchase_history['AnoMes'].astype(str) # Converter para string para Plotly

            if not purchase_history.empty:
                fig = px.bar(purchase_history, x='AnoMes', y='Quantidade', title=f'Histórico de Compras de {client_name}',
                             labels={'AnoMes': 'Mês/Ano', 'Quantidade': 'Nº de Emplacamentos'},
                             color_discrete_sequence=px.colors.qualitative.Pastel)
                fig.update_layout(xaxis_title="Período", yaxis_title="Quantidade Emplacada")
                st.plotly_chart(fig, use_container_width=True)

                # --- Previsão ---
                valid_dates = client_df["Data emplacamento"].dropna().tolist()
                prediction_text, predicted_date_obj = calculate_next_purchase_prediction(valid_dates)
                st.info(prediction_text)

                # --- Frase de Vendas ---
                sales_pitch = get_sales_pitch(last_plate_date_obj, predicted_date_obj, total_plated)
                st.success(f"💡 **Insight de Vendas:** {sales_pitch}")

            else:
                st.warning("Não há histórico de compras suficiente para gerar gráfico ou previsão.")
        else:
            st.warning("Cliente encontrado, mas sem registros de emplacamento válidos.")
elif search_button and not search_query:
    st.warning("Por favor, digite um nome ou CNPJ para buscar.")
else:
    # Se nenhuma busca foi feita, apenas o resumo geral é exibido (já está acima)
    st.info("Digite um nome ou CNPJ acima para buscar detalhes de um cliente específico.")

# --- Rodapé (Opcional) ---
st.sidebar.divider()
if os.path.exists(LOGO_WHITE_PATH):
    st.sidebar.image(LOGO_WHITE_PATH, use_column_width=True)
else:
    st.sidebar.warning("Logo branco não encontrado.")
st.sidebar.caption("© De Nigris Distribuidora")
