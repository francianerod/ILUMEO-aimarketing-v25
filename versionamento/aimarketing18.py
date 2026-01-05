# ------------------------------------------------------------------------------------------------------------- 
# ILUMEO - AI Marketing + ETL Automático
# Versão FINAL — Logs + Tabelas + Insights + Conteúdo
# -------------------------------------------------------------------------------------------------------------

import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from crewai import Agent, Task, Crew

# ETL OFICIAL
from etl_ilumeo1 import executar_etl   # <<< ATENÇÃO: usa etl_ilumeo1


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

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #333333;
    }

    :root {
        --ilumeo-orange: #FF8A00;
        --sidebar-bg: #F7F7F7;
        --text-dark: #333333;
        --text-light: #666666;
        --border-soft: #E6E6E6;
    }

    body {
        background-color: white !important;
        color: var(--text-dark) !important;
    }

    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-soft);
        padding-top: 2rem;
    }

    h1, h2, h3 {
        font-weight: 700 !important;
        color: var(--ilumeo-orange) !important;
    }

    p, label, span {
        color: var(--text-light) !important;
        font-weight: 400;
    }

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

    .stFileUploader {
        background-color: white !important;
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        padding: 10px;
    }

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
defaults = {
    "json_etl": "",
    "insights": "",
    "conteudo": "",
    #"formato_atual": "Linkedin",
    "etl_logs": [],
    "t_simples": {},
    "t_multi": {},
    "t_matriz": {},
    "t_nota": {}
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -------------------------------------------------------------------------------------------------------------
# IA — INSIGHTS
# -------------------------------------------------------------------------------------------------------------
def gerar_insights(json_text):

    agent = Agent(
        role="Analista de Mercado Sênior",
        goal="Extrair insights estratégicos do JSON da pesquisa.",
        backstory="Especialista em comportamento do consumidor, varejo e análise de frequencia."
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
        "Linkedin": (
            "Transforme os insights em um post institucional para LinkedIn. "
            "Use abertura direta, parágrafos curtos, linguagem clara e foco em dados e achados. "
            "Inclua 1 CTA suave. Evite exageros e tom coach."
        ),

        "Blog": (
            "Transforme os insights em um artigo curto e profissional com título claro, "
            "introdução objetiva e subtítulos organizados. "
            "Mostre dados, interpretações e implicações práticas."
        ),

        "OnePage": (
            "Transforme os insights em um OnePage profissional no formato de fichas executivas. "
            "Use apenas bullets extremamente curtos (máximo 12 palavras). "
            "Nada de parágrafos ou narrativa. Apenas fatos objetivos. "
            "Organize em blocos: Dados Principais, Achados, Destaques, Implicações. "
            "Finalize com 1 CTA curto."
        ),

        "Notícias": (
            "Transforme os insights em uma notícia objetiva, factual e neutra, estilo release. "
            "Evite opinião e adjetivos desnecessários."
        )
    }

    agent = Agent(
        role="Redator Especialista em Dados e IA",
        goal="Transformar insights analíticos em conteúdo claro, profissional e de impacto.",
        backstory="Especialista em marketing, dados e comunicação para negócios."
    )

    task = Task(
        description=prompts[formato] + "\n\nINSIGHTS A SEREM TRANSFORMADOS:\n" + insights,
        expected_output="Conteúdo final pronto, claro e adequado ao formato.",
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

    st.markdown("Aqui, a Inteligência Artificial transforma seus dados em **tabelas, insights e conteúdos**.\n")

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
                df, t_simples, t_multi, t_matriz, t_nota, logs = executar_etl(caminho)

                st.session_state["etl_logs"] = logs
                st.session_state["t_simples"] = t_simples
                st.session_state["t_multi"] = t_multi
                st.session_state["t_matriz"] = t_matriz
                st.session_state["t_nota"] = t_nota

                with open("resultado_pesquisa.json", "r", encoding="utf-8") as f:
                    st.session_state["json_etl"] = f.read()

                st.success("ETL concluído! JSON carregado.")

            except Exception as e:
                st.error(f"Erro durante o ETL: {e}")
                return

        # LOGS
        st.subheader("📄 Log da Execução do ETL")
        with st.expander("Ver detalhes"):
            for linha in st.session_state["etl_logs"]:
                st.markdown(f"- {linha}")

        # TABELAS
        st.subheader("📊 Tabelas de Frequência")

        with st.expander("🟦 Perguntas Simples"):
            for pergunta, tabela in st.session_state["t_simples"].items():
                st.markdown(f"### {pergunta}")
                st.dataframe(tabela)

        with st.expander("🟧 Multirresposta"):
            for pergunta, tabela in st.session_state["t_multi"].items():
                st.markdown(f"### {pergunta}")
                st.dataframe(tabela)

        with st.expander("🟩 Matriz (Texto)"):
            for pergunta, meios in st.session_state["t_matriz"].items():
                st.markdown(f"## {pergunta}")
                for meio, tabela in meios.items():
                    st.markdown(f"**{meio}**")
                    st.dataframe(tabela)

        with st.expander("🟪 Matriz (Nota)"):
            for pergunta, marcas in st.session_state["t_nota"].items():
                st.markdown(f"## {pergunta}")
                for marca, tabela in marcas.items():
                    st.markdown(f"**{marca}**")
                    st.dataframe(tabela)

        # --------------------------------------------------------------
        # JSON → INSIGHTS
        # --------------------------------------------------------------
        with st.spinner("🧠 Gerando insights..."):
             st.session_state["insights"] = gerar_insights(st.session_state["json_etl"])

        st.subheader("🧠 Insights da Pesquisa")
        st.markdown(st.session_state["insights"])

        st.markdown("---")
        st.subheader("✍️ Conteúdo Final")

        # ===============================
        # 1) PRIMEIRA SELEÇÃO DO FORMATO
        # ===============================
        if not st.session_state["conteudo"]:

            formato_inicial = st.radio(
                "Escolha o formato do conteúdo:",
                FORMATS,
                horizontal=True,
                key="escolha_inicial"
            )

            if st.button("Gerar Conteúdo"):
                with st.spinner(f"✍️ Gerando conteúdo no formato {formato_inicial}..."):
                    st.session_state["conteudo"] = gerar_conteudo(
                        st.session_state["insights"],
                        formato_inicial
                    )
                    st.session_state["formato_atual"] = formato_inicial

                # Forçar scroll suave para baixo
                st.rerun()

        # ===============================
        # 2) EXIBIR CONTEÚDO UMA ÚNICA VEZ
        # ===============================
        if st.session_state["conteudo"]:

            st.markdown(st.session_state["conteudo"])

            st.markdown("---")
            st.subheader("🔄 Escrever em outro formato")

            # ===============================
            # 3) NOVA ESCOLHA DE FORMATO
            # ===============================
            novo_formato = st.radio(
                "Selecione outro formato:",
                FORMATS,
                index=FORMATS.index(st.session_state["formato_atual"]),
                horizontal=True,
                key="escolha_reescrita"
            )

            if st.button("Reescrever neste formato"):
                with st.spinner(f"🔄 Reescrevendo conteúdo no formato {novo_formato}..."):
                    st.session_state["conteudo"] = gerar_conteudo(
                        st.session_state["insights"],
                        novo_formato
                    )
                    st.session_state["formato_atual"] = novo_formato

                st.rerun()


if __name__ == "__main__":
    main()