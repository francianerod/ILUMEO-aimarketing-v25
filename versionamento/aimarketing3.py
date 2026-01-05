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
def analisar_dados_com_crewai(caminho_csv: str):
    try:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        ferramenta_dados = CSVSearchTool(caminho_csv)

        analista = Agent(
            role="Analista de Dados de Pesquisas Survey com foco em Marcas",
            goal=(
                "Interpretar automaticamente uma base de dados de pesquisa survey, "
                "identificando as perguntas, as marcas avaliadas e suas respectivas respostas ou notas. "
                "Gerar tabelas de frequência e percentual separadas para cada pergunta e marca, "
                "de modo a representar claramente como cada marca foi avaliada nas diferentes dimensões da pesquisa."
                ),
            backstory=(
                "Você é um analista de dados especializado em tabulação de pesquisas de marketing e comportamento do consumidor. "
                "Você entende que cada pergunta pode ter várias colunas associadas, normalmente uma para cada marca ou categoria, "
                "e que as respostas podem estar em formato de múltipla escolha ou em escala (por exemplo, 0 a 10). "
                "Seu papel é organizar esses dados em tabelas de frequência absolutas e relativas, agrupando corretamente "
                "as marcas e as perguntas correspondentes."
                      ),
            tools=[ferramenta_dados],
            llm=llm,
            verbose=True
        )

        tarefa_analista = Task(
            description=(
            "Analise a base de dados de uma pesquisa survey. "
            "Identifique automaticamente todas as perguntas e variáveis representadas nas colunas do dataset, "
            "agrupando aquelas que pertençam a um mesmo bloco de perguntas (por exemplo, conjuntos de colunas que compartilham o mesmo enunciado). "
            "Para cada pergunta, gere uma tabela de frequências separada, apresentando os valores ou categorias observadas e suas contagens.\n\n"
            "Cada tabela deve conter as seguintes colunas:\n"
            "| Alternativa | Frequência (n) | Frequência Relativa (%) |\n\n"
            "Quando as respostas forem numéricas (por exemplo, escalas de 0 a 10), calcule a distribuição de valores, "
            "indicando quantas vezes cada valor foi selecionado. "
            "Quando as respostas forem categóricas (por exemplo, múltipla escolha, texto ou opção única), "
            "conte quantas vezes cada alternativa aparece. "
            "Se houver colunas relacionadas entre si (como diferentes opções de uma mesma questão), trate-as como parte da mesma pergunta.\n\n"
            "Perguntas sociodemográficas (por exemplo, idade, gênero, estado, escolaridade) também devem ter suas próprias tabelas de frequência. "
            "Apresente apenas tabelas — não produza explicações, interpretações ou análises narrativas. "
            "Siga rigorosamente o formato abaixo:\n\n"
            "#### Pergunta: [Texto ou nome da coluna ou grupo de colunas]\n"
            "| Alternativa | Frequência (n) | Frequência Relativa (%) |\n"
            "|--------------|----------------|--------------------------|\n"
            "| Categoria A | 35 | 17.5% |\n"
            "| Categoria B | 68 | 34.0% |\n"
            "| Categoria C | 50 | 25.0% |\n\n"
            "Garanta que cada pergunta identificada no dataset possua uma tabela correspondente, "
            "com percentuais arredondados e somando aproximadamente 100%."
            ),
            expected_output=(
                             "Tabelas de frequência para cada pergunta identificada no dataset, "
                             "seguindo o formato especificado, sem explicações adicionais."
                             ),
            agent=analista
        )

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
        <h2 style='margin-bottom:0; color:black;'>💬 ILUMEO - Projeto AI Marketing</h2>
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

    arquivo = st.file_uploader("Faça o upload do arquivo CSV ou Excel", type=["csv", "xlsx"])

    if arquivo is not None:
        st.success(f"✅ Arquivo '{arquivo.name}' carregado com sucesso!")

        os.makedirs("temp", exist_ok=True)
        caminho_temp = os.path.join("temp", arquivo.name)

        with open(caminho_temp, "wb") as f:
            f.write(arquivo.getbuffer())

        try:
            # 🔄 Sempre converte o arquivo para CSV, independentemente do formato
            if arquivo.name.lower().endswith(".xlsx"):
                df = pd.read_excel(caminho_temp)
            else:
                df = pd.read_csv(caminho_temp)

            caminho_csv = os.path.join("temp", arquivo.name.replace(".xlsx", ".csv").replace(".csv", "_converted.csv"))
            df.to_csv(caminho_csv, index=False)

            st.info("🔄 Arquivo convertido automaticamente para CSV antes da análise.")
            st.dataframe(df.head())

            if st.button("🚀 Executar Análise com CrewAI"):
                with st.spinner("Executando análise automatizada..."):
                    resultado = analisar_dados_com_crewai(caminho_csv)
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