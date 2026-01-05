# ------------------------------------------------------------------------------------------------------------- 
# ILUMEO - AI Marketing + ETL Automático
# Versão FINAL — Fluxo Único + Sidebar + Branding
# -------------------------------------------------------------------------------------------------------------

import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from crewai import Agent, Task, Crew

# ETL OFICIAL
from versionamento.etl_ilumeo import executar_etl  


# -------------------------------------------------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------------------------------------------------
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="ILUMEO - AI Marketing", layout="wide")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FORMATS = ["Linkedin", "Blog", "OnePage", "Notícias"]


# -------------------------------------------------------------------------------------------------------------
# CSS — PERSONALIZAÇÃO ILUMEO
# -------------------------------------------------------------------------------------------------------------
st.markdown("""
<style>

    /* Fonte padrão */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #333333;
    }

    /* Variáveis de cor ILUMEO */
    :root {
        --ilumeo-orange: #FF8A00;
        --sidebar-bg: #F7F7F7;
        --text-dark: #333333;
        --text-light: #666666;
        --border-soft: #E6E6E6;
    }

    /* Fundo geral (claro, igual ao site) */
    body {
        background-color: white !important;
        color: var(--text-dark) !important;
    }

    /* Sidebar clara */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-soft);
        padding-top: 2rem;
    }

    /* Títulos */
    h1, h2, h3 {
        font-weight: 700 !important;
        color: var(--ilumeo-orange) !important;
    }

    /* Textos suaves */
    p, label, span {
        color: var(--text-light) !important;
        font-weight: 400;
    }

    /* Botões — estilo ILUMEO */
    .stButton button {
        background-color: var(--ilumeo-orange) !important;
        color: white !important;
        border-radius: 6px !important;
        padding: 0.55rem 1.2rem !important;
        font-weight: 600 !important;
        border: none !important;
    }

    .stButton button:hover {
        background-color: #ff9c26 !important;
        color: white !important;
    }

    /* Caixa de upload */
    .stFileUploader {
        background-color: white !important;
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        padding: 10px;
    }

    /* Separadores */
    hr {
        border: 0;
        border-top: 1px solid var(--border-soft);
        margin: 2rem 0;
    }

</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------------------------------------------------
# ESTADOS
# -------------------------------------------------------------------------------------------------------------
if "json_etl" not in st.session_state:
    st.session_state["json_etl"] = ""

if "insights" not in st.session_state:
    st.session_state["insights"] = ""

if "conteudo" not in st.session_state:
    st.session_state["conteudo"] = ""


# -------------------------------------------------------------------------------------------------------------
# IA — INSIGHTS
# -------------------------------------------------------------------------------------------------------------
def gerar_insights(json_text):

    agent = Agent(
        role="Analista de Mercado Sênior",
        goal="Extrair insights estratégicos do JSON da pesquisa.",
        backstory="Especialista em comportamento do consumidor, varejo e fast fashion."
    )

    task = Task(
        description=(
            "Aqui está o JSON completo da pesquisa.\n"
            "Analise profundamente e gere INSIGHTS claros, estratégicos, humanos e acionáveis.\n\n"
            f"{json_text}"
        ),
        expected_output="Insights estratégicos e acionáveis.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()

    return result.raw


# -------------------------------------------------------------------------------------------------------------
# IA — GERAÇÃO DO CONTEÚDO FINAL
# -------------------------------------------------------------------------------------------------------------
def gerar_conteudo(insights, formato):

    prompts = {
        "Linkedin": "Transforme os insights em um post para LinkedIn, com tom humano e profissional.",
        "Blog": "Transforme os insights em um artigo com título e subtítulos.",
        "OnePage": "Resuma os insights em bullets objetivos (máx 12 palavras).",
        "Notícias": "Transforme os insights em uma notícia jornalística objetiva."
    }

    agent = Agent(
        role="Redator Especialista em Dados e IA",
        goal="Transformar insights analíticos em conteúdo humano e de impacto.",
        backstory="Copywriter especializado em comportamento do consumidor e BI."
    )

    task = Task(
        description=prompts[formato] + "\n\nINSIGHTS:\n" + insights,
        expected_output="Texto final pronto.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()

    return result.raw


# -------------------------------------------------------------------------------------------------------------
# SIDEBAR — LOGO + UPLOAD
# -------------------------------------------------------------------------------------------------------------
def sidebar():

    st.image("logo.png", width=170)
    st.markdown("### 📂 Enviar arquivo Excel")
    st.markdown("Envie uma planilha **.xlsx** para iniciar a análise completa.")

    return st.file_uploader("Upload", type=["xlsx"])


# -------------------------------------------------------------------------------------------------------------
# TELA PRINCIPAL — FLUXO ÚNICO
# -------------------------------------------------------------------------------------------------------------
def main():

    with st.sidebar:
        arquivo = sidebar()

    st.title("📊 ILUMEO — AI Marketing")

    st.markdown(
        "Aqui, a inteligência artificial transforma seus dados em insights e conteúdos para comunicação!\n"
        
    )

    # --------S------------------------------------------------------
    # UPLOAD → ETL → JSON
    # --------------------------------------------------------------
    if arquivo:

        with st.spinner("🔄 Rodando ETL ILUMEO..."):
            os.makedirs("temp", exist_ok=True)
            caminho = os.path.join("temp", arquivo.name)

            with open(caminho, "wb") as f:
                f.write(arquivo.getbuffer())

            try:
                executar_etl(caminho)

                with open("resultado_pesquisa.json", "r", encoding="utf-8") as f:
                    st.session_state["json_etl"] = f.read()

                st.success("ETL concluído! JSON carregado.")

            except Exception as e:
                st.error(f"Erro durante o ETL: {e}")
                return
        
        # --------------------------------------------------------------
        # JSON → INSIGHTS
        # --------------------------------------------------------------
        with st.spinner("🧠 Gerando insights..."):
            st.session_state["insights"] = gerar_insights(st.session_state["json_etl"])

        st.subheader("🧠 Insights da Pesquisa")
        st.markdown(st.session_state["insights"])

        st.markdown("---")
        st.subheader("✍️ Conteúdo Final")

        formato = st.radio("Escolha o formato", FORMATS, horizontal=True)

        if st.button("Gerar Conteúdo Final"):
            with st.spinner("✍️ Criando conteúdo..."):
                st.session_state["conteudo"] = gerar_conteudo(
                    st.session_state["insights"], formato
                )

        if st.session_state["conteudo"]:
            st.markdown("### 📝 Resultado Final")
            st.markdown(st.session_state["conteudo"])


if __name__ == "__main__":
    main()