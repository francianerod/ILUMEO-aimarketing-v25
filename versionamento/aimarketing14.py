# ------------------------------------------------------------------------------------------------------------- 
# ILUMEO - AI Marketing + ETL Automático
# Versão FINAL — Fluxo Único
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
# ESTADOS
# -------------------------------------------------------------------------------------------------------------
if "json_etl" not in st.session_state:
    st.session_state["json_etl"] = ""

if "insights" not in st.session_state:
    st.session_state["insights"] = ""

if "conteudo" not in st.session_state:
    st.session_state["conteudo"] = ""


# -------------------------------------------------------------------------------------------------------------
# IA — INSIGHTS (usando JSON do ETL)
# -------------------------------------------------------------------------------------------------------------
def gerar_insights(json_text):

    agent = Agent(
        role="Analista de Mercado Sênior",
        goal="Extrair insights estratégicos e manchetáveis do JSON da pesquisa.",
        backstory="Especialista em comportamento do consumidor, varejo e fast fashion."
    )

    task = Task(
        description=(
            "Aqui está o JSON completo da pesquisa.\n"
            "Analise profundamente a estrutura e gere INSIGHTS claros, estratégicos,\n"
            "humanizados, manchetáveis e úteis para marketing.\n\n"
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
        "Linkedin": "Transforme os insights em um post profissional, humano e persuasivo para LinkedIn.",
        "Blog": "Transforme os insights em um artigo estruturado com título e subtítulos.",
        "OnePage": "Resuma os insights em bullets executivos com até 12 palavras cada.",
        "Notícias": "Transforme os insights em uma notícia jornalística objetiva e informativa."
    }

    agent = Agent(
        role="Redator Especialista em Dados e IA",
        goal="Transformar insights analíticos em conteúdo claro, humano e de alto impacto.",
        backstory="Copywriter experiente em inteligência de mercado e comportamento do consumidor."
    )

    task = Task(
        description=prompts[formato] + "\n\nINSIGHTS:\n" + insights,
        expected_output="Texto final pronto para publicação.",
        agent=agent
    )

    crew = Crew(agents=[agent], tasks=[task])
    result = crew.kickoff()

    return result.raw


# -------------------------------------------------------------------------------------------------------------
# INTERFACE — FLUXO ÚNICO
# -------------------------------------------------------------------------------------------------------------
def main():
    st.title("📊 ILUMEO — AI Marketing com ETL Automático")

    st.markdown(
        "Faça upload de um **arquivo Excel (.xlsx)** da pesquisa. O sistema irá:\n"
        "1. Executar o **ETL ILUMEO**\n"
        "2. Gerar automaticamente um **JSON estruturado da pesquisa**\n"
        "3. Extrair **Insights via IA**\n"
        "4. Gerar conteúdo final no formato que você escolher\n"
    )

    arquivo = st.file_uploader("Envie o arquivo Excel da pesquisa", type=["xlsx"])

    if arquivo:

        with st.spinner("🔄 Processando arquivo via ETL ILUMEO..."):
            os.makedirs("temp", exist_ok=True)
            caminho = os.path.join("temp", arquivo.name)

            with open(caminho, "wb") as f:
                f.write(arquivo.getbuffer())

            try:
                # Executa o ETL oficial
                df, t_simples, t_multi, t_matriz, t_nota = executar_etl(caminho)

                # Lê o JSON gerado
                with open("resultado_pesquisa.json", "r", encoding="utf-8") as f:
                    st.session_state["json_etl"] = f.read()

                st.success("ETL concluído! JSON carregado com sucesso.")

            except Exception as e:
                st.error(f"Erro durante ETL: {e}")
                return

        # INSIGHTS AUTOMÁTICOS
        with st.spinner("🧠 Gerando insights da pesquisa..."):
            st.session_state["insights"] = gerar_insights(st.session_state["json_etl"])

        st.markdown("### 🧠 Insights da Pesquisa")
        st.markdown(st.session_state["insights"])

        st.markdown("---")
        st.markdown("### ✍️ Escolha o formato do conteúdo final")

        formato = st.radio("Formato", FORMATS, horizontal=True)

        if st.button("Gerar Conteúdo Final"):
            with st.spinner("✍️ Criando conteúdo final com IA..."):
                st.session_state["conteudo"] = gerar_conteudo(
                    st.session_state["insights"], formato
                )

        if st.session_state["conteudo"]:
            st.markdown("### 📝 Conteúdo Final")
            st.markdown(st.session_state["conteudo"])


if __name__ == "__main__":
    main()