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

    /* Fonte */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #222;
    }

    /* Cor ILUMEO */
    :root {
        --primary: #0088cc;
        --secondary: #00a8e8;
    }

    /* Botões */
    .stButton button {
        background-color: var(--primary);
        color: white;
        border-radius: 8px;
        padding: 0.6em 1.2em;
        border: none;
        font-weight: 600;
    }
    .stButton button:hover {
        background-color: var(--secondary);
        color: white;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #f6faff;
        border-right: 1px solid #e0e6ed;
    }

    /* Títulos */
    h1, h2, h3 {
        font-weight: 700;
        color: var(--primary) !important;
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

    st.title("📊 ILUMEO — AI Marketing com ETL Automático")

    st.markdown(
        "Upload → ETL → JSON → Insights → Conteúdo Final\n"
        "**Fluxo 100% automático.**"
    )

    # --------------------------------------------------------------
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
