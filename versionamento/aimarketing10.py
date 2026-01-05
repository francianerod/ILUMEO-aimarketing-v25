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
# FUNÇÃO: ANÁLISE AUTOMÁTICA
# -------------------------------------------------------------------------------------------------------------
def analisar_dados_com_crewai(caminho_csv: str):
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        ferramenta_dados = CSVSearchTool(caminho_csv)

        analista = Agent(
            role="Analista de Dados de Pesquisas Survey",
            goal="Gerar tabelas de frequência absoluta e relativa para cada pergunta da pesquisa.",
            backstory=(
                "Você é um analista de dados especializado em pesquisas. "
                "Sua missão é tabular resultados com rigor estatístico e clareza visual."
            ),
            tools=[ferramenta_dados],
            llm=llm,
            verbose=True
        )

        tarefa = Task(
            description=(
                "Analise o CSV e gere tabelas no formato:\n\n"
                "#### Pergunta: [Texto da Pergunta]\n"
                "| Alternativa | Frequência (n) | Frequência Relativa (%) |\n"
                "|--------------|----------------|--------------------------|\n\n"
                "Inclua variáveis categóricas, numéricas e sociodemográficas."
            ),
            expected_output="Tabelas de frequência padronizadas.",
            agent=analista
        )

        crew = Crew(agents=[analista], tasks=[tarefa], verbose=True)
        resultado = crew.kickoff()
        return resultado.raw if hasattr(resultado, "raw") else str(resultado)

    except Exception as e:
        return f"⚠️ Erro ao executar CrewAI: {e}"

# -------------------------------------------------------------------------------------------------------------
# FUNÇÃO: GERAR INSIGHTS
# -------------------------------------------------------------------------------------------------------------
def gerar_insights(texto_tabelas: str):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    redator = Agent(
        role="Especialista em Insights de Pesquisa",
        goal="Extrair significados estratégicos a partir dos dados tabulados.",
        backstory="Você traduz números em interpretações acionáveis.",
        llm=llm,
        verbose=True
    )

    tarefa = Task(
        description=(
            "Analise as tabelas e gere insights claros em tópicos. "
            "Não repita as tabelas, interprete-as."
        ),
        expected_output="Lista de insights estratégicos.",
        agent=redator
    )

    resultado = Crew(agents=[redator], tasks=[tarefa], verbose=True).kickoff(inputs={"tabelas": texto_tabelas})
    return resultado.raw if hasattr(resultado, "raw") else str(resultado)

# -------------------------------------------------------------------------------------------------------------
# FUNÇÃO: FORMATAR TEXTO FINAL POR ESTILO
# -------------------------------------------------------------------------------------------------------------
def formatar_conteudo(insights: str, formato: str):
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    prompts_formatos = {
        "Linkedin": """
        Transforme os insights a seguir em um post no estilo LinkedIn:
        - Comece com uma frase de impacto
        - Linguagem humana e próxima
        - Frases curtas
        - Finalize com CTA leve (ex: "E você, o que pensa sobre isso?")
        """,

        "Blog": """
        Transforme os insights a seguir em um artigo de blog:
        - Título chamativo
        - Introdução contextualizando a análise
        - Divida os insights em seções claras com subtítulos
        - Conclua com uma síntese e implicações práticas
        """,

        "OnePage": """
        Transforme os insights a seguir em uma OnePage executiva:
        - Título objetivo
        - Liste os principais insights como bullets concisos
        - Cada bullet com no máximo 12 palavras
        - Não inclua contextualização ou CTA
        """,

        "Notícias": """
        Transforme os insights a seguir em uma notícia jornalística:
        - Tom neutro e impessoal
        - Parágrafo 1: fato central
        - Parágrafo 2: dados que sustentam
        - Parágrafo 3: possíveis desdobramentos
        - Não use opinião ou CTA
        """
    }

    formatador = Agent(
        role="Copywriter Especializado",
        goal=f"Transformar insights no formato {formato}.",
        backstory="Você adapta textos para diferentes estilos narrativos garantindo clareza e propósito.",
        llm=llm,
        verbose=True
    )

    tarefa = Task(
        description=prompts_formatos[formato] + "\n\nINSIGHTS:\n" + insights,
        expected_output=f"Texto final formatado como {formato}.",
        agent=formatador
    )

    crew = Crew(agents=[formatador], tasks=[tarefa], verbose=True)
    resultado = crew.kickoff()

    return resultado.raw if hasattr(resultado, "raw") else str(resultado)

# -------------------------------------------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# -------------------------------------------------------------------------------------------------------------
def pagina_chat():
    st.markdown(
        """
        <h2 style='margin-bottom:0; color:black;'>💬 ILUMEO - AI Marketing</h2>
        <hr style='border: 2px solid #FFA500; border-radius: 5px; margin-top: 5px;'>
        """,
        unsafe_allow_html=True
    )

    if "arquivo_carregado" in st.session_state:
        st.success(f"📂 Arquivo carregado: **{st.session_state['arquivo_carregado'].name}**")

    if "df" in st.session_state:
        st.dataframe(st.session_state["df"].head())

        if st.button("Executar Análise"):
            with st.spinner("Tabulando dados..."):
                st.session_state["tabelas"] = analisar_dados_com_crewai(st.session_state["caminho_csv"])
            st.markdown("### Tabulação")
            st.markdown(st.session_state["tabelas"])

    if "tabelas" in st.session_state:
        if st.button("Gerar Insights"):
            with st.spinner("Interpretando resultados..."):
                st.session_state["insights"] = gerar_insights(st.session_state["tabelas"])
        if "insights" in st.session_state:
            st.markdown("### Insights Identificados")
            st.markdown(st.session_state["insights"])

    if "insights" in st.session_state:
        st.markdown("---")
        st.markdown("### Escolha o Formato do Conteúdo")
        formato = st.radio("Formato:", TIPOS_ANALISE, horizontal=True)

        if st.button("Gerar Conteúdo Final"):
            with st.spinner("Convertendo insights em texto..."):
                 st.session_state["conteudo_final"] = formatar_conteudo(st.session_state["insights"], formato)
            st.markdown("### Conteúdo Final")
            st.markdown(st.session_state["conteudo_final"])
            st.info("Você pode trocar o formato acima sem reprocessar nada!")

# -------------------------------------------------------------------------------------------------------------
# SIDEBAR (UPLOAD)
# -------------------------------------------------------------------------------------------------------------
def sidebar():
    st.image("logo.png", width=180)
    #st.subheader("Upload")
    arquivo = st.file_uploader("Envie o arquivo:", type=["xlsx", "csv"])

    if arquivo:
        os.makedirs("temp", exist_ok=True)
        caminho = os.path.join("temp", arquivo.name)
        with open(caminho, "wb") as f: f.write(arquivo.getbuffer())

        df = pd.read_excel(caminho) if arquivo.name.endswith(".xlsx") else pd.read_csv(caminho)
        caminho_csv = caminho.replace(".xlsx", ".csv")
        df.to_csv(caminho_csv, index=False)

        st.session_state.update({"arquivo_carregado": arquivo, "df": df, "caminho_csv": caminho_csv})
        st.success("✅ Arquivo carregado e convertido!")

# -------------------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------------------
def main():
    with st.sidebar:
        sidebar()
    pagina_chat()

if __name__ == "__main__":
    main()