# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing com Tabulação + Insights
# Versão FINAL — Franciane Rodrigues
# -------------------------------------------------------------------------------------------------------------

import os
import json
import re
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from crewai import Agent, Task, Crew

# -------------------------------------------------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------------------------------------------------
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="ILUMEO - AI Marketing", layout="wide")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TIPOS_ANALISE = ["Linkedin", "Blog", "OnePage", "Notícias"]


# -------------------------------------------------------------------------------------------------------------
# ESTADO
# -------------------------------------------------------------------------------------------------------------
if "df" not in st.session_state: st.session_state["df"] = None
if "tabelas_texto" not in st.session_state: st.session_state["tabelas_texto"] = ""
if "insights" not in st.session_state: st.session_state["insights"] = ""

# -------------------------------------------------------------------------------------------------------------
# LIMPEZA
# -------------------------------------------------------------------------------------------------------------
def limpar_texto(texto):
    if pd.isna(texto): return None
    texto = str(texto)
    texto = re.sub(r"<.*?>", "", texto)
    return texto.strip()

def padronizar_dataframe(df):
    df = df.copy()
    df.columns = [limpar_texto(c) for c in df.columns]
    return df

# -------------------------------------------------------------------------------------------------------------
# PARSER — REMOÇÃO DA LINHA “RESPONSE”
# -------------------------------------------------------------------------------------------------------------
def parsear_excel_delfos(df_raw):
    """
    Estrutura correta dos seus dados:
    Linha 0 = Perguntas
    Linha 1 = Itens
    Linha 2 = LIXO (Response, Response...)  → deve ser removida
    Linha 3+ = respondentes
    """
    
    # Remover a linha "Response"
    df = df_raw.drop(index=2).reset_index(drop=True)

    perguntas = [limpar_texto(x) for x in df.iloc[0].tolist()]
    itens = [limpar_texto(x) for x in df.iloc[1].tolist()]
    respostas = df.iloc[2:].reset_index(drop=True)

    colunas_final = []
    for p, item in zip(perguntas, itens):
        if item in [None, "", "nan"]:
            colunas_final.append(p)
        else:
            colunas_final.append(f"{p} / {item}")

    respostas.columns = colunas_final
    return respostas

# -------------------------------------------------------------------------------------------------------------
# TABULAÇÃO — 100% PANDAS
# -------------------------------------------------------------------------------------------------------------
def gerar_tabulação(df):
    tabelas_texto = []

    socio_cols = [
        c for c in df.columns
        if "#est" in c or "#cid" in c or "#gen" in c or "#idd" in c or "#esc" in c or "#cls" in c
    ]
    perguntas_cols = [c for c in df.columns if c not in socio_cols]

    texto_buffer = ""

    for col in perguntas_cols:

        # -------- FREQUÊNCIAS ----------
        freq_abs = df[col].value_counts(dropna=False)
        freq_rel = df[col].value_counts(normalize=True, dropna=False) * 100

        todas_alternativas = freq_abs.index.union(freq_rel.index)

        tabela = pd.DataFrame({
            "Alternativa": todas_alternativas.astype(str),
            "Frequência (n)": freq_abs.reindex(todas_alternativas).fillna(0).astype(int),
            "Frequência (%)": freq_rel.reindex(todas_alternativas).fillna(0).round(2)
        })

        tabelas_texto.append((f"Pergunta: {col}", tabela))
        texto_buffer += f"\n\nPergunta: {col}\n{tabela.to_string(index=False)}\n"

        # -------- SEGMENTAÇÕES ----------
        for socio in socio_cols:
            seg = pd.crosstab(df[col], df[socio], normalize="columns") * 100
            seg = seg.round(2)

            tabelas_texto.append((f"Segmentação: {col} x {socio}", seg))
            texto_buffer += f"\nSegmentação: {col} x {socio}\n{seg.to_string()}\n"

    return tabelas_texto, texto_buffer



# -------------------------------------------------------------------------------------------------------------
# CREWAI / INSIGHTS
# -------------------------------------------------------------------------------------------------------------
def gerar_insights(texto):

    agente = Agent(
        role="Analista de Mercado Sênior",
        goal="Extrair insights estratégicos e manchetáveis das tabulações.",
        backstory="Especialista em comportamento do consumidor, varejo e fast fashion."
    )

    tarefa = Task(
        description=(
            "A seguir estão tabelas de frequência e segmentações demográficas.\n"
            "Produza insights acionáveis, concisos, claros e úteis para marketing.\n\n"
            f"{texto}"
        ),
        expected_output="Insights estratégicos e manchetáveis.",
        agent=agente,
    )

    resultado = Crew(agents=[agente], tasks=[tarefa]).kickoff()
    return resultado.raw

# -------------------------------------------------------------------------------------------------------------
# CREWAI / CONTEÚDO FINAL
# -------------------------------------------------------------------------------------------------------------
def formatar_conteudo(insights, formato):

    prompts = {
        "Linkedin": "Transforme os insights abaixo em um post humano, didático e profissional para LinkedIn.",
        "Blog": "Transforme os insights abaixo em artigo estruturado com título e subtítulos.",
        "OnePage": "Transforme os insights em bullets executivos com até 12 palavras.",
        "Notícias": "Transforme os insights em notícia jornalística objetiva."
    }

    agente = Agent(
        role="Redator Especialista em Comunicação de Dados",
        goal="Transformar insights analíticos em conteúdo claro e de impacto.",
        backstory="Copywriter experiente em varejo e inteligência de mercado."
    )

    tarefa = Task(
        description=prompts[formato] + "\n\nINSIGHTS:\n" + insights,
        expected_output="Texto final pronto para publicação.",
        agent=agente
    )

    resultado = Crew(agents=[agente], tasks=[tarefa]).kickoff()
    return resultado.raw

# -------------------------------------------------------------------------------------------------------------
# TELA — TABULAÇÃO
# -------------------------------------------------------------------------------------------------------------
def tela_tabulação():
    st.title("Tabulação Automática da Pesquisa")

    if st.session_state["df"] is None:
        st.warning("Envie um arquivo na barra lateral para começar.")
        return

    if st.button("🚀 Gerar Tabulação Agora"):
        with st.spinner("Processando tabulações..."):
            tabelas, texto = gerar_tabulação(st.session_state["df"])
            st.session_state["tabelas_texto"] = texto

            for titulo, tabela in tabelas:
                st.markdown(f"### {titulo}")
                st.dataframe(tabela)

        st.success("Tabulação concluída!")

# -------------------------------------------------------------------------------------------------------------
# TELA — INSIGHTS
# -------------------------------------------------------------------------------------------------------------
def tela_insights():
    st.title("🧠 Insights + Conteúdo Final")

    if not st.session_state["tabelas_texto"]:
        st.warning("Gere a tabulação primeiro.")
        return

    if st.button("🧠 Gerar Insights da Pesquisa"):
        with st.spinner("Gerando insights estratégicos..."):
            st.session_state["insights"] = gerar_insights(st.session_state["tabelas_texto"])

    if st.session_state["insights"]:
        st.markdown("### 🔍 Insights")
        st.markdown(st.session_state["insights"])

        formato = st.radio("Formato do Conteúdo Final", TIPOS_ANALISE, horizontal=True)

        if st.button("✍️ Criar Conteúdo Final"):
            with st.spinner("Formatando conteúdo..."):
                texto = formatar_conteudo(st.session_state["insights"], formato)
                st.markdown("### 📝 Conteúdo Final")
                st.markdown(texto)

# -------------------------------------------------------------------------------------------------------------
# SIDEBAR — UPLOAD
# -------------------------------------------------------------------------------------------------------------
def sidebar():
    st.image("logo.png", width=160)
    st.markdown("### 📂 Enviar arquivo")

    arquivo = st.file_uploader("Excel ou CSV", type=["xlsx", "csv"])

    if arquivo:
        os.makedirs("temp", exist_ok=True)
        caminho = os.path.join("temp", arquivo.name)

        with open(caminho, "wb") as f:
            f.write(arquivo.getbuffer())

        df_raw = pd.read_excel(caminho) if arquivo.name.endswith(".xlsx") else pd.read_csv(caminho)
        df_raw = padronizar_dataframe(df_raw)

        df = parsear_excel_delfos(df_raw)

        st.session_state["df"] = df
        st.success("Arquivo carregado, linha 'Response' removida e colunas estruturadas!")

# -------------------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------------------
def main():
    with st.sidebar:
        sidebar()

    pagina = st.sidebar.radio(" Navegação ", ["Tabulação", "Insights/Conteúdo"])

    if pagina == "Tabulação":
        tela_tabulação()
    else:
        tela_insights()


if __name__ == "__main__":
    main()