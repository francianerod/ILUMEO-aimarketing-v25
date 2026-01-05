# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing + ETL Automático
# Versão FINAL — Logs + Tabelas + Insights + Conteúdo Multicanal
# + Módulo YouTube → Transcrição → Blog (ADICIONAL)
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
    "conteudos_multicanais": "",
    "etl_logs": [],
    "t_simples": {},
    "t_multi": {},
    "t_matriz": {},
    "t_nota": {},

    # YOUTUBE (NOVO)
    "yt_url": "",
    "yt_transcricao": "",
    "yt_blog": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -------------------------------------------------------------------------------------------------------------
# IA — INSIGHTS PROFUNDOS COM CRUZAMENTO
# -------------------------------------------------------------------------------------------------------------
def gerar_insights(json_text):

    agente = Agent(
        role="Analista de Mercado e Inteligência Competitiva Sênior",
        goal=(
            "Realizar análise profunda, cruzada e estratégica do JSON, "
            "identificando padrões, clusters, motivações, barreiras e oportunidades."
        ),
        backstory=(
            "Especialista em comportamento do consumidor, marketing estratégico, "
            "estatística de pesquisa e análise de frequência."
        )
    )

    tarefa = Task(
        description=(
            "Você receberá o JSON completo contendo tabelas de frequências, múltiplas respostas, "
            "matriz de texto e matriz de notas. Realize uma ANÁLISE PROFUNDA REAL, com cruzamento de dados "
            "entre perguntas, comparações entre categorias, interpretação de padrões e hipóteses de comportamento.\n\n"
            "Identifique:\n"
            "- Tendências e padrões fortes\n"
            "- Contradições e comportamentos divergentes\n"
            "- Barreiras, gatilhos e drivers de decisão\n"
            "- Oportunidades estratégicas para marketing\n"
            "- Relações ocultas entre respostas\n"
            "- Segmentações implícitas ou grupos naturais\n\n"
            "Use linguagem clara, humana, estratégica e orientada a marketing.\n\n"
            "JSON:\n"
            f"{json_text}"
        ),
        expected_output="Insight completo, estratégico, profundo e humanizado.",
        agent=agente,
    )

    equipe = Crew(agents=[agente], tasks=[tarefa])
    resultado = equipe.kickoff()

    return resultado.raw


# -------------------------------------------------------------------------------------------------------------
# IA — CONTEÚDOS MULTICANAIS
# -------------------------------------------------------------------------------------------------------------
def gerar_conteudos_multicanais(insights):

    agente = Agent(
        role="Especialista em Conteúdo Multicanal baseado em Insights de Dados",
        goal="Transformar insights profundos em 4 conteúdos distintos para canais diferentes.",
        backstory="Especialista em branding, marketing, jornalismo e escrita executiva."
    )

    tarefa = Task(
        description=(
            "A partir dos insights fornecidos, gere QUATRO versões de conteúdo distintas:\n\n"

            "### 1) LINKEDIN\n"
            "- Tom institucional\n"
            "- Parágrafos curtos\n"
            "- Abertura forte\n"
            "- Dados claros\n"
            "- CTA leve no final\n\n"

            "### 2) BLOG\n"
            "- Artigo estruturado\n"
            "- Título forte\n"
            "- Subtítulos organizados\n"
            "- Interpretação + contexto\n"
            "- Conclusão analítica\n\n"
            "- Cite Diego Senise CEO da Ilumeo em algum trecho do texto falando de algum insights relevante\n\n"
            "- Para realização de estudo aprofundado, levantamento, pesquisa entre outras, cite a ILUMEO.\n\n"

            "### 3) ONE PAGE EXECUTIVA\n"
            "- Somente bullets\n"
            "- Máximo 12 palavras por bullet\n"
            "- Seções: Dados / Achados / Oportunidades / Implicações / Próximos Passos\n\n"

            "### 4) NOTÍCIA JORNALÍSTICA (Release)\n"
            "- Tom factual, objetivo e neutro\n"
            "- Narração em pirâmide invertida\n"
            "- Sem opinião pessoal\n\n"
            "- Cite Diego Senise CEO da Ilumeo em algum trecho do texto falando de algum insights relevante\n\n"
            "- Para realização de estudo aprofundado, levantamento, pesquisa entre outras, cite a ILUMEO.\n\n"

            "INSIGHTS A TRANSFORMAR:\n"
            f"{insights}"
        ),
        expected_output="Documento contendo as quatro versões, separadas e prontas para copiar.",
        agent=agente
    )

    equipe = Crew(agents=[agente], tasks=[tarefa])
    resultado = equipe.kickoff()

    return resultado.raw


# -------------------------------------------------------------------------------------------------------------
# IA — YOUTUBE → TRANSCRIÇÃO
# -------------------------------------------------------------------------------------------------------------
def transcrever_video_youtube(url):

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": f"""
                Gere a transcrição completa, em português brasileiro,
                do vídeo do YouTube abaixo. Preserve o conteúdo falado.

                URL:
                {url}
                """
            }
        ],
        temperature=0.0
    )

    return resposta.choices[0].message.content


# -------------------------------------------------------------------------------------------------------------
# IA — TRANSCRIÇÃO → BLOG
# -------------------------------------------------------------------------------------------------------------
def gerar_blog_a_partir_transcricao(transcricao):

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"""
                A partir da transcrição abaixo, gere um BLOG POST profissional
                alinhado ao posicionamento da marca ILUMEO.

                Regras:
                - Não mencionar que veio de vídeo
                - Linguagem estratégica e institucional
                - Estrutura:
                    • Título
                    • Introdução
                    • Subtítulos
                    • Desenvolvimento
                    • Conclusão

                TRANSCRIÇÃO:
                {transcricao}
                """
            }
        ],
        temperature=0.1
    )

    return resposta.choices[0].message.content


# -------------------------------------------------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------------------------------------------------
def sidebar():

    st.image("logo.png", width=170)

    st.markdown("### 📂 Enviar arquivo Excel")
    arquivo = st.file_uploader("Upload", type=["xlsx"])

    st.markdown("---")
    st.markdown("### 🎥 YouTube → Blog")
    st.session_state["yt_url"] = st.text_input(
        "Cole a URL do vídeo do YouTube",
        value=st.session_state["yt_url"]
    )

    return arquivo


# -------------------------------------------------------------------------------------------------------------
# TELA PRINCIPAL — FLUXO ORIGINAL + MÓDULO ADICIONAL
# -------------------------------------------------------------------------------------------------------------
def main():

    with st.sidebar:
        arquivo = sidebar()

    st.title("📊 ILUMEO — AI Marketing")
    st.markdown("Aqui, a Inteligência Artificial transforma seus dados em **tabelas, insights e 4 conteúdos**.\n")

    # ---------------------------------------------------------------------
    # MÓDULO YOUTUBE (INDEPENDENTE DO ETL)
    # ---------------------------------------------------------------------
    if st.session_state["yt_url"]:

        st.markdown("---")
        st.subheader("🎥 Conteúdo Gerado a partir de Vídeo do YouTube")

        if not st.session_state["yt_transcricao"]:
            with st.spinner("🎙️ Transcrevendo vídeo automaticamente..."):
                st.session_state["yt_transcricao"] = transcrever_video_youtube(
                    st.session_state["yt_url"]
                )

        st.text_area(
            "📝 Transcrição do Vídeo",
            st.session_state["yt_transcricao"],
            height=250
        )

        if not st.session_state["yt_blog"]:
            with st.spinner("✍️ Gerando blog post automaticamente..."):
                st.session_state["yt_blog"] = gerar_blog_a_partir_transcricao(
                    st.session_state["yt_transcricao"]
                )

        st.subheader("✍️ Blog Post Gerado")
        st.markdown(st.session_state["yt_blog"])

    # ---------------------------------------------------------------------
    # UPLOAD → ETL → JSON (FLUXO ORIGINAL INALTERADO)
    # ---------------------------------------------------------------------
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

                st.success("ETL concluído! JSON carregado com sucesso.")

            except Exception as e:
                st.error(f"Erro durante o ETL: {e}")
                return

        # ------------------- LOGS -------------------
        st.subheader("📄 Log da Execução do ETL")
        with st.expander("Ver detalhes"):
            for linha in st.session_state["etl_logs"]:
                st.markdown(f"- {linha}")

        # ------------------- TABELAS -------------------
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

        # ---------------------------------------------------------------------
        # GERAR INSIGHT PROFUNDO
        # ---------------------------------------------------------------------
        with st.spinner("🧠 Analisando dados profundamente e cruzando informações..."):
            st.session_state["insights"] = gerar_insights(st.session_state["json_etl"])

        st.subheader("🧠 Insight Profundo da Pesquisa")
        st.markdown(st.session_state["insights"])

        st.markdown("---")

        # ---------------------------------------------------------------------
        # GERAR CONTEÚDOS MULTICANAIS AUTOMATICAMENTE
        # ---------------------------------------------------------------------
        st.subheader("✍️ Conteúdo Multicanal Gerado Automaticamente")

        if not st.session_state["conteudos_multicanais"]:
            with st.spinner("✍️ Criando textos completos para todos os canais..."):
                st.session_state["conteudos_multicanais"] = gerar_conteudos_multicanais(
                    st.session_state["insights"]
                )
            st.rerun()

        st.markdown(st.session_state["conteudos_multicanais"])


if __name__ == "__main__":
    main()