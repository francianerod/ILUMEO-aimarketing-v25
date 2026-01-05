# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing com Análise Automática
# Autora: Franciane Rodrigues
# -------------------------------------------------------------------------------------------------------------

import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from crewai import Agent, Task, Crew
from crewai_tools import CSVSearchTool
from langchain_openai import ChatOpenAI

# -------------------------------------------------------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# -------------------------------------------------------------------------------------------------------------
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
st.set_page_config(page_title="ILUMEO - AI Marketing", layout="wide")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TIPOS_ARQUIVOS = ["Planilha (.xlsx)", "Texto (.csv)"]
TIPOS_ANALISE = ["Linkedin", "Blog", "OnePage", "Notícias"]

# -------------------------------------------------------------------------------------------------------------
# FUNÇÃO DE ANÁLISE AUTOMÁTICA (CrewAI)
# -------------------------------------------------------------------------------------------------------------
def analisar_dados_com_crewai(caminho_csv: str):
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        ferramenta_dados = CSVSearchTool(caminho_csv)

        analista = Agent(
            role="Analista de Dados de Pesquisas Survey",
            goal=("Gerar tabelas de frequência absoluta e relativa para cada pergunta da pesquisa."),
            backstory=("Você é um analista de dados especializado em tabulação de pesquisas. "
                       "Identifique perguntas, alternativas e variáveis no dataset e apresente resultados "
                       "em tabelas bem formatadas, com frequências absolutas e relativas."
                       ),
            tools=[ferramenta_dados],
            llm=llm,
            verbose=True
        )

        tarefa_analista = Task(
            description=(
                 "Analise o CSV e gere tabelas no formato:\n\n"
                "#### Pergunta: [Texto da Pergunta]\n"
                "| Alternativa | Frequência (n) | Frequência Relativa (%) |\n"
                "|--------------|----------------|--------------------------|\n"
                "| Categoria A | 35 | 17.5% |\n"
                "| Categoria B | 68 | 34.0% |\n\n"
                "Inclua perguntas categóricas, numéricas e variáveis sociodemográficas."
                        ),
            expected_output=("Tabelas de frequência padronizadas, sem explicações extras."),
            agent=analista
        )

        crew = Crew(agents=[analista], tasks=[tarefa_analista], verbose=True)
        resultado = crew.kickoff()

        # TRATAMENTO DO RETORNO
        if hasattr(resultado, "raw") and resultado.raw:
            return f"**Resultado da Análise Automática**\n\n{resultado.raw}"
        elif isinstance(resultado, dict) and "raw" in resultado:
            return f"**Resultado da Análise Automática**\n\n{resultado['raw']}"
        elif hasattr(resultado, "tasks_output"):
            return f"**Resultado da Análise Automática**\n\n{resultado.tasks_output[0].raw}"
        else:
            return f"**Resultado da Análise Automática**\n\n{str(resultado)}"

    except Exception as e:
        return f"⚠️ Erro ao executar CrewAI: {e}"
    

# -------------------------------------------------------------------------------------------------------------
# NOVA ETAPA: GERAÇÃO DE INSIGHTS
# -------------------------------------------------------------------------------------------------------------
def gerar_insights(texto_tabelas: str):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.5)

    redator = Agent(
        role="Especialista em Insights de Pesquisa",
        goal=("Interpretar as tabelas e extrair os principais padrões estratégicos."),
        backstory=("Você transforma tabulações de pesquisas em insights acionáveis, claros e executáveis."),
        llm=llm,
        verbose=True
    )

    tarefa = Task(
        description=(
            "Analise as tabelas e gere insights organizados em tópicos, "
            "destacando tendências, padrões e hipóteses relevantes. Não repita as tabelas."
        ),
        expected_output="Lista clara de insights em tópicos.",
        agent=redator
    )

    retorno = Crew(agents=[redator], tasks=[tarefa], verbose=True).kickoff(inputs={"tabelas": texto_tabelas})
    return retorno.raw if hasattr(retorno, "raw") else str(retorno)

# -------------------------------------------------------------------------------------------------------------
# NOVA ETAPA: FORMATAR TEXTO FINAL CONFORME ESCOLHA DO USUÁRIO
# -------------------------------------------------------------------------------------------------------------
def formatar_conteudo(insights: str, formato: str):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

    formatador = Agent(
        role="Copywriter Especializado",
        goal=f"Transformar insights no formato {formato}.",
        backstory="Você domina copywriting estratégico e adaptação para diferentes formatos.",
        llm=llm,
        verbose=True
    )

    tarefa = Task(
        description=(
            f"Transforme os insights no formato **{formato}**:\n\n"
            "- Linkedin: storytelling + CTA\n"
            "- Blog: explicativo + seções\n"
            "- OnePage: objetivo + tópicos curtos\n"
            "- Notícias: texto jornalístico neutro\n"
        ),
        expected_output=f"Texto final adaptado para formato {formato}.",
        agent=formatador
    )

    retorno = Crew(agents=[formatador], tasks=[tarefa], verbose=True).kickoff(inputs={"insights": insights})
    return retorno.raw if hasattr(retorno, "raw") else str(retorno)


# -------------------------------------------------------------------------------------------------------------
# CHAT INTERATIVO
# -------------------------------------------------------------------------------------------------------------
def pagina_chat():
    st.markdown("## ILUMEO - Projeto AI Marketing")
    st.markdown("---")

    if "arquivo_carregado" in st.session_state:
        st.success(f"✅ Arquivo **{st.session_state['arquivo_carregado'].name}** carregado com sucesso!")

    # Exibe dados pré-visualizados
    if "df" in st.session_state:
        st.info("✅ Arquivo pronto para análise.")
        st.dataframe(st.session_state["df"].head())

        if st.button("Executar Análise com CrewAI"):
            with st.spinner("Executando análise..."):
                resultado = analisar_dados_com_crewai(st.session_state["caminho_csv"])
                st.session_state["tabelas"] = resultado
                st.markdown("### 📊 Resultado da Tabulação")
                st.markdown(resultado)

    # Gerar insights
    if "tabelas" in st.session_state:
        if st.button("Gerar Insights Automáticos"):
            with st.spinner("Interpretando dados..."):
                insights = gerar_insights(st.session_state["tabelas"])
                st.session_state["insights"] = insights
                st.markdown("### 🔍 Principais Insights")
                st.markdown(insights)

    # Escolha do formato + conteúdo final
    if "insights" in st.session_state:
        st.markdown("---")
        st.markdown("### Escolha o Formato do Conteúdo")

        formato = st.radio("Formato desejado:", TIPOS_ANALISE, horizontal=True)

        if st.button("Gerar Conteúdo Final"):
            with st.spinner("Formatando..."):
                conteudo = formatar_conteudo(st.session_state["insights"], formato)
                st.session_state["conteudo_final"] = conteudo
                st.markdown("### Conteúdo Final")
                st.markdown(conteudo)

        if "conteudo_final" in st.session_state:
            st.info("Você pode escolher outro formato acima e gerar novamente sem reprocessar 😉")

# -------------------------------------------------------------------------------------------------------------
# SIDEBAR - Upload com seleção de tipo de arquivo
# -------------------------------------------------------------------------------------------------------------
def sidebar():
    st.image("logo.png", width=180)
    st.subheader("Upload de Arquivo para Análise")

    tipo_arquivo = st.selectbox("Tipo de arquivo:", TIPOS_ARQUIVOS)

    arquivo = st.file_uploader("Envie o arquivo:", type=["xlsx", "csv"])

    if arquivo is not None:
        os.makedirs("temp", exist_ok=True)
        caminho_temp = os.path.join("temp", arquivo.name)

        with open(caminho_temp, "wb") as f:
            f.write(arquivo.getbuffer())

        try:
            if arquivo.name.lower().endswith(".xlsx"):
                df = pd.read_excel(caminho_temp)
                nome_csv = arquivo.name.replace(".xlsx", ".csv")
            else:
                df = pd.read_csv(caminho_temp)
                nome_csv = arquivo.name.replace(".csv", "_convertido.csv")

            caminho_csv = os.path.join("temp", nome_csv)
            df.to_csv(caminho_csv, index=False)

            st.session_state["arquivo_carregado"] = arquivo
            st.session_state["df"] = df
            st.session_state["caminho_csv"] = caminho_csv

            st.success("✅ Arquivo carregado e convertido!")
        except Exception as e:
            st.error(f"⚠️ Erro: {e}")

# -------------------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------------------
def main():
    with st.sidebar:
        sidebar()
    pagina_chat()

if __name__ == "__main__":
    main()