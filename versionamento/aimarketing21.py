# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing + ETL Automático
# Versão FINAL — Logs + Tabelas + Insights + Conteúdo Multicanal
# + Módulo YouTube → Transcrição REAL (Legenda → Whisper) → Blog (ADICIONAL)
# Melhorias:
#   ✅ Transcrição REAL: tenta legenda (rápido) e faz fallback para Whisper (robusto)
#   ✅ Cache de transcrição e blog por URL (evita custo duplicado)
#   ✅ Botões: "Transcrever / Gerar" e "Gerar novamente" + "Limpar módulo YouTube"
#   ✅ Tratamento de erros e validação de URL
# Requisitos:
#   pip install yt-dlp youtube-transcript-api
#   ffmpeg instalado no sistema (para yt-dlp extrair áudio)
# -------------------------------------------------------------------------------------------------------------

import os
import re
import json
import hashlib
import tempfile

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from crewai import Agent, Task, Crew

# Legendas do YouTube (quando disponíveis)
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Download de áudio do YouTube
import yt_dlp

# ETL OFICIAL
from etl_ilumeo1 import executar_etl  # <<< ATENÇÃO: usa etl_ilumeo1


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
st.markdown(
    """
<style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #333333; }
    :root { --ilumeo-orange: #FF8A00; --sidebar-bg: #F7F7F7; --text-dark: #333333; --text-light: #666666; --border-soft: #E6E6E6; }
    body { background-color: white !important; color: var(--text-dark) !important; }
    section[data-testid="stSidebar"] { background-color: var(--sidebar-bg) !important; border-right: 1px solid var(--border-soft); padding-top: 2rem; }
    h1, h2, h3 { font-weight: 700 !important; color: var(--ilumeo-orange) !important; }
    p, label, span { color: var(--text-light) !important; font-weight: 400; }
    .stButton button { background-color: var(--ilumeo-orange) !important; color: white !important; border-radius: 6px !important; padding: 0.55rem 1.2rem !important; font-weight: 600 !important; border: none !important; }
    .stButton button:hover { background-color: #F59E0B !important; color: white !important; }
    .stFileUploader { background-color: white !important; border: 1px solid var(--border-soft); border-radius: 8px; padding: 10px; }
    hr { border: 0; border-top: 1px solid var(--border-soft); margin: 2rem 0; }
</style>
""",
    unsafe_allow_html=True,
)

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

    # YOUTUBE
    "yt_url": "",
    "yt_transcricao": "",
    "yt_blog": "",
    "yt_origem_transcricao": "",  # "legenda" ou "whisper"
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# -------------------------------------------------------------------------------------------------------------
# UTIL — HELPERS
# -------------------------------------------------------------------------------------------------------------
def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def validar_url_youtube(url: str) -> bool:
    if not url:
        return False
    # cobre youtube.com/watch?v=... e youtu.be/...
    pattern = r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+"
    return re.search(pattern, url) is not None


def extrair_video_id(url: str) -> str | None:
    # youtube.com/watch?v=ID
    m = re.search(r"[?&]v=([^&]+)", url)
    if m:
        return m.group(1)
    # youtu.be/ID
    m = re.search(r"youtu\.be/([^?&]+)", url)
    if m:
        return m.group(1)
    return None

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
        ),
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
        backstory="Especialista em branding, marketing, jornalismo e escrita executiva.",
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
        agent=agente,
    )

    equipe = Crew(agents=[agente], tasks=[tarefa])
    resultado = equipe.kickoff()
    return resultado.raw

# -------------------------------------------------------------------------------------------------------------
# YOUTUBE → TRANSCRIÇÃO (Legenda → Whisper)
# -------------------------------------------------------------------------------------------------------------
def _transcrever_por_legenda(url: str) -> str:
    video_id = extrair_video_id(url)
    if not video_id:
        raise ValueError("Não foi possível extrair o ID do vídeo a partir da URL.")

    # tenta PT/BR e depois EN
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["pt", "pt-BR", "pt-PT", "en"])
    return " ".join([item.get("text", "") for item in transcript]).strip()


def _transcrever_por_whisper(url: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.mp3")

        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": audio_path,
            "quiet": True,
            "noplaylist": True,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        with open(audio_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                language="pt",
            )
    return transcription.text.strip()


@st.cache_data(show_spinner=False)
def transcrever_video_youtube_cacheada(url: str) -> dict:
    """
    Retorna um dict:
      { "texto": "...", "origem": "legenda"|"whisper" }
    Cacheado por URL para evitar custo repetido.
    """
    # 1) tenta legenda
    try:
        texto = _transcrever_por_legenda(url)
        if texto:
            return {"texto": texto, "origem": "legenda"}
    except (TranscriptsDisabled, NoTranscriptFound, ValueError):
        pass
    except Exception:
        # qualquer outra falha na legenda → fallback
        pass

    # 2) fallback whisper
    texto = _transcrever_por_whisper(url)
    return {"texto": texto, "origem": "whisper"}


# -------------------------------------------------------------------------------------------------------------
# IA — TRANSCRIÇÃO → BLOG (cache por hash)
# -------------------------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def gerar_blog_a_partir_transcricao_cacheado(transcricao: str) -> str:
    """
    Cache por conteúdo (transcrição) evita gerar o mesmo blog novamente
    mesmo que a URL seja reprocessada.
    """
    _ = _hash_text(transcricao)  # apenas para "amarrar" o cache ao conteúdo

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
""".strip(),
            }
        ],
        temperature=0.1,
    )

    return resposta.choices[0].message.content


def limpar_modulo_youtube():
    st.session_state["yt_transcricao"] = ""
    st.session_state["yt_blog"] = ""
    st.session_state["yt_origem_transcricao"] = ""


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
        value=st.session_state["yt_url"],
        placeholder="Ex: https://www.youtube.com/watch?v=XXXX",
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🧹 Limpar YouTube"):
            limpar_modulo_youtube()
            st.rerun()
    with col_b:
        if st.button("🔄 Limpar cache"):
            st.cache_data.clear()
            limpar_modulo_youtube()
            st.rerun()

    return arquivo


# -------------------------------------------------------------------------------------------------------------
# TELA PRINCIPAL — FLUXO ORIGINAL + MÓDULO ADICIONAL
# -------------------------------------------------------------------------------------------------------------
def main():
    with st.sidebar:
        arquivo = sidebar()

    st.title("📊 ILUMEO — AI Marketing")
    st.markdown("Aqui, a Inteligência Artificial transforma seus dados em **insights**.\n")

    # ---------------------------------------------------------------------
    # MÓDULO YOUTUBE (INDEPENDENTE DO ETL)
    # ---------------------------------------------------------------------
    if st.session_state["yt_url"]:
        st.markdown("---")
        st.subheader("🎥 Conteúdo Gerado a partir de Vídeo do YouTube")

        url = st.session_state["yt_url"].strip()

        if not validar_url_youtube(url):
            st.error("URL inválida. Cole uma URL válida do YouTube (youtube.com/watch?v=... ou youtu.be/...).")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                gerar_tudo = st.button("🎙️ Transcrever + ✍️ Gerar Blog", use_container_width=True)

            with col2:
                transcrever_apenas = st.button("🎙️ Só Transcrever", use_container_width=True)

            with col3:
                regerar_blog = st.button("✍️ Gerar Blog novamente", use_container_width=True)

            # Ações
            if transcrever_apenas or gerar_tudo:
                with st.spinner("🎙️ Transcrevendo vídeo (Legenda → Whisper)..."):
                    try:
                        out = transcrever_video_youtube_cacheada(url)
                        st.session_state["yt_transcricao"] = out["texto"]
                        st.session_state["yt_origem_transcricao"] = out["origem"]
                    except Exception as e:
                        st.error(f"Erro ao transcrever o vídeo: {e}")

            # Se pediu tudo e temos transcrição
            if gerar_tudo and st.session_state["yt_transcricao"]:
                with st.spinner("✍️ Gerando blog post automaticamente..."):
                    try:
                        st.session_state["yt_blog"] = gerar_blog_a_partir_transcricao_cacheado(
                            st.session_state["yt_transcricao"]
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o blog post: {e}")

            # Se pediu regerar (ignora cache do blog: limpa cache e gera)
            if regerar_blog and st.session_state["yt_transcricao"]:
                with st.spinner("✍️ Gerando blog post novamente (sem cache)..."):
                    try:
                        # truque: limpa cache apenas do blog (mais simples: limpa tudo)
                        # se preferir granularidade, dá para separar em outro cache.
                        st.cache_data.clear()
                        st.session_state["yt_blog"] = gerar_blog_a_partir_transcricao_cacheado(
                            st.session_state["yt_transcricao"]
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o blog post: {e}")

            # Exibição
            if st.session_state["yt_transcricao"]:
                origem = st.session_state.get("yt_origem_transcricao", "")
                if origem:
                    st.caption(f"Transcrição obtida via: **{origem.upper()}**")

                st.text_area(
                    "📝 Transcrição do Vídeo",
                    st.session_state["yt_transcricao"],
                    height=250,
                )

            if st.session_state["yt_blog"]:
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