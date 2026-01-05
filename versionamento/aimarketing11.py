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
# Tratamento de dados
# -------------------------------------------------------------------------------------------------------------

# PEGAR OS DADOS DA DELFOS - 11/11/2025
# CRIAR UM REPO PARA TODAS AS FERRAMENTAS DE AI MARKETING
# 
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
# ESTADO PERSISTENTE (HISTÓRICO)
# -------------------------------------------------------------------------------------------------------------
if "historico_tabelas" not in st.session_state:
    st.session_state["historico_tabelas"] = []

if "historico_insights" not in st.session_state:
    st.session_state["historico_insights"] = []

if "historico_conteudos" not in st.session_state:
    st.session_state["historico_conteudos"] = []

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
                "Inclua variáveis categóricas e sociodemográficas."
            ),
            expected_output="Tabelas prontas.",
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
        goal="Extrair significados estratégicos a partir dos dados.",
        backstory="Você transforma números em interpretações de negócio.",
        llm=llm,
        verbose=True
    )

    tarefa = Task(
        description="Analise as tabelas e gere insights organizados em tópicos. Não repita as tabelas.",
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
        Escreva como post de LinkedIn:
        - Comece com uma frase de impacto
        - Linguagem humana e próxima
        - Parágrafos curtos
        - Finalize com CTA leve
        """,
        "Blog": """
        Escreva como Artigo de Blog:
        - Crie título e subtítulos
        - Explique os insights em seções claras
        - Conclua com síntese e implicações práticas
        """,
        "OnePage": """
        Escreva como OnePage Executiva:
        - Título curto
        - Liste insights como bullets objetivos
        - Cada bullet até 12 palavras
        """,
        "Notícias": """
        Escreva como Notícia Jornalística:
        - Tom neutro e impessoal
        - Parágrafo 1: fato principal
        - Parágrafo 2: dados que sustentam
        - Parágrafo 3: desdobramentos
        """
    }

    formatador = Agent(
        role="Copywriter Especializado",
        goal=f"Adaptar insights para o formato {formato}.",
        backstory="Você domina comunicação estratégica.",
        llm=llm,
        verbose=True
    )

    tarefa = Task(
        description=prompts_formatos[formato] + "\n\nINSIGHTS:\n" + insights,
        expected_output=f"Texto final no estilo {formato}.",
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
        <h2 style='margin-bottom:0; color:black;'> ILUMEO - AI Marketing</h2>
        <hr style='border: 2px solid #FFA500; border-radius: 5px; margin-top: 5px;'>
        <p style='font-size:16px; color:#333;'>
        Olá! Seja bem-vindo(a) ao <strong>ILUMEO - AI Marketing</strong>.<br>
        Aqui, a inteligência artificial transforma seus dados em <em>insights estratégicos</em> e conteúdos prontos para comunicação.<br>
        Envie sua planilha ou arquivo CSV ao lado para começar a análise automática!
        """,
        unsafe_allow_html=True
    )

    # Exibir pré-visualização da base
    if "df" in st.session_state:
        st.dataframe(st.session_state["df"].head())

        if st.button("🚀 Executar Análise"):
            with st.spinner("Gerando tabulação..."):
                tabelas = analisar_dados_com_crewai(st.session_state["caminho_csv"])
                st.session_state["tabelas"] = tabelas
                st.session_state["historico_tabelas"].append(tabelas)

    # Exibir histórico de tabelas
    for i, tabela in enumerate(st.session_state["historico_tabelas"]):
        st.markdown(f"### 📊 Tabulação {i+1}")
        st.markdown(tabela)

    # Insights
    if "tabelas" in st.session_state:
        if st.button("🧠 Gerar Insights"):
            with st.spinner("Interpretando..."):
                insights = gerar_insights(st.session_state["tabelas"])
                st.session_state["insights"] = insights
                st.session_state["historico_insights"].append(insights)

    for i, insight in enumerate(st.session_state["historico_insights"]):
        st.markdown(f"### 🔍 Insights {i+1}")
        st.markdown(insight)

    # Conteúdos
    if "insights" in st.session_state:
        st.markdown("### 🎨 Selecione o Formato")
        formato = st.radio("Formato:", TIPOS_ANALISE, horizontal=True)

        if st.button("✍️ Gerar Conteúdo Final"):
            with st.spinner("Transformando..."):
                texto = formatar_conteudo(st.session_state["insights"], formato)
                st.session_state["conteudo_final"] = texto
                st.session_state["historico_conteudos"].append({"formato": formato, "texto": texto})

        if "conteudo_final" in st.session_state:
            st.info("Você pode escolher outro formato acima e gerar novamente sem reprocessar 😉")

    for i, item in enumerate(st.session_state["historico_conteudos"]):
        st.markdown(f"### 📝 Conteúdo {i+1} — Formato: {item['formato']}")
        st.markdown(item["texto"])

# -------------------------------------------------------------------------------------------------------------
# SIDEBAR (UPLOAD)
# -------------------------------------------------------------------------------------------------------------
def sidebar():
    st.image("logo.png", width=180)

    arquivo = st.file_uploader("Envie o arquivo:", type=["xlsx", "csv"])

    if arquivo:
        os.makedirs("temp", exist_ok=True)
        caminho = os.path.join("temp", arquivo.name)
        with open(caminho, "wb") as f:
            f.write(arquivo.getbuffer())

        df = pd.read_excel(caminho) if arquivo.name.endswith(".xlsx") else pd.read_csv(caminho)
        caminho_csv = caminho.replace(".xlsx", ".csv")
        df.to_csv(caminho_csv, index=False)

        st.session_state.update({"arquivo_carregado": arquivo, "df": df, "caminho_csv": caminho_csv})
        st.success("✅ Arquivo carregado e convertido com sucesso")

# -------------------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------------------
def main():
    with st.sidebar:
        sidebar()
    pagina_chat()

if __name__ == "__main__":
    main()