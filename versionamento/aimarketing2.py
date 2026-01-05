# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing com Análise Automática via CrewAI (CSV e Excel)
# Autora: Franciane Rodrigues
# Descrição:
# Aplicação web que permite conversar com uma assistente de marketing e gerar automaticamente análises
# competitivas de marcas a partir de arquivos CSV ou Excel (.xlsx).
# -------------------------------------------------------------------------------------------------------------

import os
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# CrewAI e ferramentas
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

# -------------------------------------------------------------------------------------------------------------
# FUNÇÃO PARA RESPOSTA DO CHAT ILUMEO
# -------------------------------------------------------------------------------------------------------------
def gerar_resposta(mensagens):
    try:
        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": m[0], "content": m[1]} for m in mensagens]
        )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"⚠️ Erro ao conectar com a OpenAI: {e}"

# -------------------------------------------------------------------------------------------------------------
# FUNÇÃO DE ANÁLISE AUTOMÁTICA (CrewAI)
# -------------------------------------------------------------------------------------------------------------
def analisar_dados_com_crewai(caminho_arquivo: str, tipo_arquivo: str):
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

        # Seleciona a ferramenta correta
        if tipo_arquivo.lower().endswith(".csv"):
            ferramenta_dados = CSVSearchTool(caminho_arquivo)
       # else:
        #    ferramenta_dados = DataSearchTool(caminho_arquivo)

        # Define o agente analista
        analista = Agent(
            role="Analista de Pesquisas e Competitividade de Marcas",
            goal=(
                "Explorar bases de pesquisa (CSV ou XLSX) contendo respostas sobre percepção, lembrança, "
                "preferência, satisfação ou uso de diferentes marcas. Calcular frequências, médias e proporções, "
                "gerando análises comparativas entre as marcas e insights executivos."
            ),
            backstory=(
                "Você é um analista sênior especializado em estudos de marcas e comportamento do consumidor. "
                "Seu trabalho é transformar dados brutos de pesquisa em inteligência competitiva, "
                "destacando marcas líderes, equilíbrio entre gêneros e padrões regionais."
            ),
            tools=[ferramenta_dados],
            llm=llm,
            verbose=True
        )

        # Define a tarefa principal
        tarefa_analista = Task(
            description=(
                "Analise a base de pesquisa e gere uma análise comparativa entre as marcas avaliadas. "
                "Detecte automaticamente as colunas que representam múltiplas opções de resposta, notas numéricas "
                "e variáveis binárias de uso. Considere colunas de gênero ('sexo', 'genero', 'gênero') e estado ('UF', 'estado'). "
                "Monte tabelas e uma narrativa executiva destacando as marcas líderes e oportunidades de crescimento."
            ),
            expected_output=(
                "1️⃣ **Tabela Geral de Marcas** com colunas: Marca | % Menção | Média da Nota | % Uso/Contato.\n"
                "2️⃣ **Tabela Comparativa por Gênero** (Homens vs. Mulheres) com diferença absoluta e relativa.\n"
                "3️⃣ **Tabela por Estado (UF)** com ranking e destaque das top e bottom 5 marcas.\n"
                "4️⃣ **Principais Insights e Recomendações Estratégicas** com linguagem executiva."
            ),
            agent=analista
        )

        # Executa a crew
        crew = Crew(agents=[analista], tasks=[tarefa_analista], verbose=True)
        resultado = crew.kickoff()

        return resultado

    except Exception as e:
        return f"⚠️ Erro ao executar CrewAI: {e}"

# -------------------------------------------------------------------------------------------------------------
# PÁGINA DE CHAT
# -------------------------------------------------------------------------------------------------------------
def pagina_chat():
    st.markdown(
        """
        <h2 style='margin-bottom:0; color:black;'>💬 ILUMEO - Projeto AI Marketing com CrewAI</h2>
        <hr style='border: 2px solid #FFA500; border-radius: 5px; margin-top: 5px;'>
        """,
        unsafe_allow_html=True
    )

    mensagens = st.session_state.get(
        'mensagens',
        [('assistant', 'Olá! Sou sua Assistente de IA em Marketing da ILUMEO. Como posso ajudar você hoje?')]
    )

    for msg in mensagens:
        with st.chat_message(msg[0]):
            st.markdown(msg[1])

    input_usuario = st.chat_input("Digite sua mensagem aqui...")
    if input_usuario:
        mensagens.append(('user', input_usuario))
        with st.chat_message("user"):
            st.markdown(input_usuario)

        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = gerar_resposta(mensagens)
                st.markdown(resposta)

        mensagens.append(('assistant', resposta))
        st.session_state['mensagens'] = mensagens

# -------------------------------------------------------------------------------------------------------------
# SIDEBAR - Upload e Análise de Arquivo
# -------------------------------------------------------------------------------------------------------------
def sidebar():
    st.image("logo.png", width=180)
    st.subheader("📂 Upload de Arquivo para Análise")

    tipo_arquivo = st.selectbox("Selecione o tipo de arquivo:", TIPOS_ARQUIVOS)

    if tipo_arquivo == "Planilha (.xlsx)":
        arquivo = st.file_uploader("Faça o upload do arquivo Excel", type=["xlsx"])
    else:
        arquivo = st.file_uploader("Faça o upload do arquivo CSV", type=["csv"])

    if arquivo is not None:
        st.success(f"✅ Arquivo '{arquivo.name}' carregado com sucesso!")

        # Cria caminho temporário
        os.makedirs("temp", exist_ok=True)
        caminho_temp = os.path.join("temp", arquivo.name)

        with open(caminho_temp, "wb") as f:
            f.write(arquivo.getbuffer())

        try:
            if tipo_arquivo == "Planilha (.xlsx)":
                df = pd.read_excel(caminho_temp)
            else:
                df = pd.read_csv(caminho_temp)

            st.dataframe(df.head())

            if st.button("🚀 Executar Análise com CrewAI"):
                with st.spinner("Executando análise automatizada..."):
                    resultado = analisar_dados_com_crewai(caminho_temp, arquivo.name)
                    st.markdown("### 📊 Resultado da Análise Automática")
                    st.write(resultado)

        except Exception as e:
            st.error(f"Erro ao processar o arquivo: {e}")

# -------------------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------------------
def main():
    pagina_chat()
    with st.sidebar:
        sidebar()

if __name__ == "__main__":
    main()