# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing com Análise Automática via CrewAI (CSV e Excel)
# Autora: Franciane Rodrigues
# Descrição:
# Aplicação web que permite conversar com uma assistente de marketing e gerar automaticamente tabelas de
# frequências absolutas e relativas a partir de pesquisas survey (CSV ou Excel).
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
            role="Analista de Dados de Pesquisas Survey",
            goal=(
                "Interpretar automaticamente uma base de dados de pesquisa survey, "
                "identificando perguntas, alternativas e variáveis associadas. "
                "Gerar tabelas de frequência absoluta e relativa para cada pergunta do dataset, "
                "organizando os resultados de forma tabular e padronizada."
            ),
            backstory=(
                "Você é um analista de dados especializado em tabulação de pesquisas. "
                "Seu papel é identificar perguntas e categorias, calcular frequências absolutas e relativas, "
                "e gerar tabelas bem formatadas que reflitam a distribuição das respostas. "
                "As perguntas podem incluir variáveis numéricas (0–10), múltipla escolha ou categóricas."
            ),
            tools=[ferramenta_dados],
            llm=llm,
            verbose=True
        )

        tarefa_analista = Task(
            description=(
                "Analise a base de pesquisa fornecida. "
                "Identifique automaticamente as colunas que representam perguntas e alternativas (como marcas ou categorias). "
                "Agrupe colunas que pertencem a um mesmo bloco de perguntas. "
                "Para cada pergunta, gere uma tabela separada com as colunas:\n"
                "| Alternativa | Frequência (n) | Frequência Relativa (%) |\n\n"
                "Calcule distribuições para perguntas numéricas e contagens para perguntas categóricas. "
                "Inclua também tabelas de variáveis sociodemográficas (como estado, gênero, idade). "
                "Não inclua textos interpretativos — apenas tabelas formatadas da seguinte forma:\n\n"
                "#### Pergunta: [Texto da Pergunta]\n"
                "| Alternativa | Frequência (n) | Frequência Relativa (%) |\n"
                "|--------------|----------------|--------------------------|\n"
                "| Categoria A | 35 | 17.5% |\n"
                "| Categoria B | 68 | 34.0% |\n"
                "| Categoria C | 50 | 25.0% |\n\n"
                "Garanta que todas as perguntas identificadas no dataset tenham uma tabela correspondente, "
                "com percentuais somando aproximadamente 100%."
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
    st.subheader("Upload de Arquivo para Análise")

    tipo_arquivo = st.selectbox("Selecione o tipo de arquivo:", TIPOS_ARQUIVOS)

    if tipo_arquivo == "Planilha (.xlsx)":
        arquivo = st.file_uploader("Faça o upload do arquivo Excel", type=["xlsx"])
    else:
        arquivo = st.file_uploader("Faça o upload do arquivo CSV", type=["csv"])

    if arquivo is not None:
        st.success(f"✅ Arquivo '{arquivo.name}' carregado com sucesso!")

        os.makedirs("temp", exist_ok=True)
        caminho_temp = os.path.join("temp", arquivo.name)

        with open(caminho_temp, "wb") as f:
            f.write(arquivo.getbuffer())

        try:
            # Converte qualquer formato em CSV antes de enviar ao CrewAI
            if arquivo.name.lower().endswith(".xlsx"):
                df = pd.read_excel(caminho_temp)
                nome_csv = arquivo.name.replace(".xlsx", ".csv")
            else:
                df = pd.read_csv(caminho_temp)
                nome_csv = arquivo.name.replace(".csv", "_converted.csv")

            caminho_csv = os.path.join("temp", nome_csv)
            df.to_csv(caminho_csv, index=False)

            st.info("Arquivo convertido automaticamente para CSV")
            st.success("Arquivo pronto para análise automática.")
            st.dataframe(df.head())

            if st.button("Executar Análise"):
                with st.spinner("Executando análise automatizada..."):
                    resultado = analisar_dados_com_crewai(caminho_csv)
                    st.markdown("### Resultado da Análise Automática")
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