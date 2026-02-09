# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing + ETL Automático + YouTube → Blog
# # Por: Franciane Rodrigues
# -------------------------------------------------------------------------------------------------------------

import os
import re
import json
import hashlib
import tempfile
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from openai import RateLimitError
from crewai import Agent, Task, Crew

# Legendas do YouTube (quando disponíveis)
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Download de áudio do YouTube (mantido, mas no Community Cloud é instável)
import yt_dlp

# ETL OFICIAL
from etl_ilumeo2 import executar_etl  # <<< ATENÇÃO: usa etl_ilumeo2

# -------------------------------------------------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------------------------------------------------
load_dotenv()
#os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY") para uso em máquina local
st.set_page_config(page_title="ILUMEO - AI Marketing", layout="wide")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------------------------------------------------------------------
# CSS — PERSONALIZAÇÃO ILUMEO
# -------------------------------------------------------------------------------------------------------------
st.markdown(
    """
<style>
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #333333; }
    :root {
        --ilumeo-orange: #FF8A00;
        --sidebar-bg: #F7F7F7;
        --text-dark: #333333;
        --text-light: #666666;
        --border-soft: #E6E6E6;
}

    body { background-color: white !important; color: var(--text-dark) !important; }
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg) !important;
        border-right: 1px solid var(--border-soft);
        padding-top: 2rem;
}

    h1, h2, h3 { font-weight: 700 !important; color: var(--ilumeo-orange) !important; }
    p, label, span { color: var(--text-light) !important; font-weight: 400; }

    .stButton button {
    background-color: var(--ilumeo-orange) !important;
    color: white !important;
    border-radius: 6px !important;
    padding: 0.55rem 1.2rem !important;
    font-weight: 600 !important;
    border: none !important;
}

    .stButton button span,
    .stButton button p {
    color: white !important;
}

    .stButton button:hover,
    .stButton button:hover span,
    .stButton button:hover p {
    background-color: #F59E0B !important;
    color: white !important;
}
    .stFileUploader {
        background-color: white !important;
        border: 1px solid var(--border-soft);
        border-radius: 8px;
        padding: 10px;
}

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

    # <<< GOVERNANÇA DE IA: só consome token sob demanda
    "autorizar_insights": False,
    "insights_gerados": False,
    "autorizar_conteudos": False,

    # YOUTUBE
    "yt_url": "",
    "yt_transcricao": "",
    "yt_blog": "",
    "yt_origem_transcricao": "",  # "legenda" | "upload"
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
    pattern = r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+"
    return re.search(pattern, url) is not None

def extrair_video_id(url: str) -> str | None:
    m = re.search(r"[?&]v=([^&]+)", url)
    if m:
        return m.group(1)
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
        goal=("Realizar análise profunda, cruzada e estratégica do JSON,"
              "identificando padrões, clusters, motivações, barreiras e oportunidades."
            ),
        backstory=("Especialista em comportamento do consumidor, marketing estratégico, "
                   "estatística de pesquisa e análise de frequência."
                  ),
    )

    tarefa = Task(
        description=(
                    "Seu objetivo é gerar INSIGHTS PROFUNDOS e estratégicos a partir dos dados da pesquisa. "
                    "Não use expressões referenciais como:\n"
                    "“conforme acima”, “como visto”, “analisado anteriormente”, "
                    "“segue abaixo”, “resultado da análise”.\n\n"

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
            "- Detalhe clusterizações específicas\n\n"
            "- Faça análises cruzadas entre perfil socioeconômico e comportamento de consumo\n\n"
            "Use linguagem clara, humana, estratégica e orientada a marketing.\n\n"
            "JSON:\n"
            f"{json_text}"
        ),
        expected_output=("Insight completo, estratégico, profundo e humanizado."),
        agent=agente,
    )

    equipe = Crew(agents=[agente], tasks=[tarefa])
    resultado = equipe.kickoff()
    return resultado.raw

# -------------------------------------------------------------------------------------------------------------
# IA — CONTEÚDOS MULTICANAIS
# -------------------------------------------------------------------------------------------------------------
def carregar_prompt(nome_arquivo: str) -> str:
    caminho = os.path.join("prompts", nome_arquivo)
    with open(caminho, "r", encoding="utf-8") as f:
        return f.read().strip()

def gerar_conteudos_multicanais(insights):
    agente = Agent(
        role="Especialista em Conteúdo Multicanal baseado em Insights de Dados",
        goal="Gerar conteúdos editoriais por canal a partir de insights de pesquisa.",
        backstory="Especialista em branding, marketing, jornalismo e escrita executiva.",
    )

    tarefas = [
        Task(
            description=f"{carregar_prompt('linkedin.txt')}\n\nINSIGHTS:\n{insights}",
            expected_output=("Texto final para LinkedIn, "
                             "sem frases introdutórias ou explicativas, "
                             "pronto para publicação."),
            agent=agente,
        ),
        Task(
            description=f"{carregar_prompt('blog.txt')}\n\nINSIGHTS:\n{insights}",
            expected_output=("Artigo completo para Blog, "
                             "estruturado com título, introdução, subtítulos e conclusão, "
                             "sem explicações sobre o processo de escrita."),
            agent=agente,
        ),
        Task(
            description=f"{carregar_prompt('one_page.txt')}\n\nINSIGHTS:\n{insights}",
            expected_output=("Apenas a ONE PAGE EXECUTIVA final, "
                             "começando diretamente em '### Dados', "
                             "sem qualquer frase introdutória, explicativa ou de encerramento."),
            agent=agente,
        ),
        Task(
            description=f"{carregar_prompt('release.txt')}\n\nINSIGHTS:\n{insights}",
            expected_output=("Texto completo do RELEASE jornalístico, "
                             "começando diretamente pelo TÍTULO, "
                             "seguindo a estrutura exigida, "
                             "sem qualquer frase explicativa, referencial ou metalinguística."),
            agent=agente,
        ),
    ]

    crew = Crew(agents=[agente], tasks=tarefas)
    crew.kickoff()

    return (
        "## LinkedIn\n\n" + tarefas[0].output.raw +
        "\n\n---\n\n## Blog\n\n" + tarefas[1].output.raw +
        "\n\n---\n\n## One Page Executiva\n\n" + tarefas[2].output.raw +
        "\n\n---\n\n## Release\n\n" + tarefas[3].output.raw
    )

# -------------------------------------------------------------------------------------------------------------
# YOUTUBE → TRANSCRIÇÃO (Legenda → Upload)
# (No Streamlit Community Cloud, yt-dlp tende a falhar com 403)
# -------------------------------------------------------------------------------------------------------------
def _transcrever_por_legenda(url: str) -> str:
    video_id = extrair_video_id(url)
    if not video_id:
        raise ValueError("Não foi possível extrair o ID do vídeo a partir da URL.")

    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["pt", "pt-BR", "pt-PT", "en"])
    return " ".join([item.get("text", "") for item in transcript]).strip()

def _transcrever_por_whisper(url: str) -> str:
    with tempfile.TemporaryDirectory() as tmpdir:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(tmpdir, "%(id)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,

            # anti-403
            "user_agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/123.0.0.0 Safari/537.36"
            ),
            "http_headers": {
                "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            "extractor_args": {"youtube": {"player_client": ["android", "web"]}},
            "retries": 3,
            "fragment_retries": 3,

            "postprocessors": [
                {"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}
            ],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

        audio_file = None
        for f in os.listdir(tmpdir):
            if f.lower().endswith(".mp3"):
                audio_file = os.path.join(tmpdir, f)
                break

        if not audio_file:
            raise FileNotFoundError("MP3 não foi gerado pelo yt-dlp.")

        with open(audio_file, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                file=audio, model="whisper-1", language="pt"
            )
    return transcription.text.strip()


def _transcrever_upload_whisper(uploaded_file) -> str:
    suffix = os.path.splitext(uploaded_file.name)[1].lower() or ".mp3"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                file=audio,
                model="whisper-1",
                language="pt",
            )
        return transcription.text.strip()
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@st.cache_data(show_spinner=False)
def transcrever_video_youtube_cacheada(url: str, uploaded_name: str | None) -> dict:
    # 1) Legenda
    try:
        texto = _transcrever_por_legenda(url)
        if texto:
            return {"texto": texto, "origem": "legenda"}
    except (TranscriptsDisabled, NoTranscriptFound, ValueError):
        pass
    except Exception:
        pass

    # 2) Whisper por URL (yt-dlp hardened)
    try:
        texto = _transcrever_por_whisper(url)
        if texto:
            return {"texto": texto, "origem": "whisper"}
    except Exception:
        # 3) Fallback upload
        if uploaded_name:
            return {"texto": "", "origem": "upload_pendente"}
        raise


# -------------------------------------------------------------------------------------------------------------
# IA — TRANSCRIÇÃO → BLOG (cache por hash)
# -------------------------------------------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def gerar_blog_a_partir_transcricao_cacheado(transcricao: str) -> str:
    _ = _hash_text(transcricao)

    resposta = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user",
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
        temperature=0.0,
    )

    return resposta.choices[0].message.content

def limpar_modulo_youtube():
    keys_youtube = [
        "yt_url",
        "yt_transcricao",
        "yt_blog",
        "yt_origem_transcricao",
    ]

    for k in keys_youtube:
        if k in st.session_state:
            del st.session_state[k]

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

    st.markdown("Ou envie um arquivo de áudio/vídeo (fallback quando não há legenda):")
    yt_file = st.file_uploader(
        "Upload de áudio/vídeo",
        type=["mp3", "wav", "m4a", "mp4", "mov", "webm"],
        key="yt_upload_file",
    )

    return arquivo, yt_file

# -------------------------------------------------------------------------------------------------------------
# TELA PRINCIPAL — FLUXO ORIGINAL + MÓDULO ADICIONAL
# -------------------------------------------------------------------------------------------------------------
def main():
    with st.sidebar:
        arquivo, yt_file = sidebar()

    st.title("ILUMEO — AI Marketing & Intelligence Platform")
    st.markdown("Aqui, a Inteligência Artificial transforma seus dados em **Insights**.\n")

    # ---------------------------------------------------------------------
    # MÓDULO YOUTUBE (INDEPENDENTE DO ETL)
    # ---------------------------------------------------------------------
    if st.session_state["yt_url"]:
        st.markdown("---")
        st.subheader("Conteúdo Gerado a partir de Vídeo do YouTube")

        url = st.session_state["yt_url"].strip()

        if not validar_url_youtube(url):
            st.error("URL inválida. Cole uma URL válida do YouTube (youtube.com/watch?v=... ou youtu.be/...).")
        else:
            col1, col2, col3 = st.columns(3)

            with col1:
                gerar_tudo = st.button("Transcrever + Gerar Blog", use_container_width=True)

            with col2:
                transcrever_apenas = st.button("Só Transcrever", use_container_width=True)

            with col3:
                regerar_blog = st.button("Gerar Blog novamente", use_container_width=True)

            if transcrever_apenas or gerar_tudo:
                with st.spinner("Transcrevendo (Legenda → Whisper → Upload)..."):
                    try:
                        out = transcrever_video_youtube_cacheada(url, yt_file.name if yt_file else None)

                        if out["origem"] == "legenda":
                            st.session_state["yt_transcricao"] = out["texto"]
                            st.session_state["yt_origem_transcricao"] = "legenda"

                        elif out["origem"] == "whisper":
                             st.session_state["yt_transcricao"] = out["texto"]
                             st.session_state["yt_origem_transcricao"] = "whisper"

                        elif out["origem"] == "upload_pendente":
                            if not yt_file:
                                st.warning("Sem legenda e o YouTube pode bloquear no Community Cloud. Envie um arquivo para Whisper.")
                            else:
                                texto = _transcrever_upload_whisper(yt_file)
                                st.session_state["yt_transcricao"] = texto
                                st.session_state["yt_origem_transcricao"] = "upload"

                    except Exception as e:
                        st.error(
                                  "Não foi possível transcrever automaticamente pela URL (o YouTube pode bloquear no Community Cloud). "
                                  "Envie um arquivo de áudio/vídeo no sidebar para transcrever com Whisper."
                                )
                        st.caption(str(e))

            if gerar_tudo and st.session_state["yt_transcricao"]:
                with st.spinner("Gerando blog post automaticamente..."):
                    try:
                        st.session_state["yt_blog"] = gerar_blog_a_partir_transcricao_cacheado(
                            st.session_state["yt_transcricao"]
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o blog post: {e}")

            if regerar_blog and st.session_state["yt_transcricao"]:
                with st.spinner("Gerando blog post novamente (sem cache)..."):
                    try:
                        st.cache_data.clear()
                        st.session_state["yt_blog"] = gerar_blog_a_partir_transcricao_cacheado(
                            st.session_state["yt_transcricao"]
                        )
                    except Exception as e:
                        st.error(f"Erro ao gerar o blog post: {e}")

            if st.session_state["yt_transcricao"]:
                origem = st.session_state.get("yt_origem_transcricao", "")
                if origem:
                    st.caption(f"Transcrição obtida via: **{origem.upper()}**")

                st.text_area(
                    "Transcrição do Vídeo",
                    st.session_state["yt_transcricao"],
                    height=250,
                )

            if st.session_state["yt_blog"]:
                st.subheader("Blog Post Gerado")
                st.markdown(st.session_state["yt_blog"])

    # ---------------------------------------------------------------------
    # UPLOAD → ETL → JSON 
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
        # IA — INSIGHTS
        # ---------------------------------------------------------------------
        st.markdown("---")
        st.subheader("Insight Profundo da Pesquisa")

        # <<< GOVERNANÇA DE IA: botão de autorização
        if st.button("Gerar Insights Profundos com IA. Clique aqui!", use_container_width=True):
            st.session_state["autorizar_insights"] = True

        # <<< GOVERNANÇA DE IA: executa apenas sob demanda e uma única vez
        if st.session_state["autorizar_insights"] and not st.session_state["insights_gerados"]:
            with st.spinner("Analisando dados profundamente e cruzando informações..."):
                try:
                    insights_raw = gerar_insights(st.session_state["json_etl"])

                    # -------- FILTRO DEFINITIVO ANTI-PLACEHOLDER --------
                    texto = (insights_raw or "").strip()
                    lixo = {
                        "[conteúdo detalhado acima]",
                        "[conteúdo acima]",
                        "[conteúdo detalhado]",
                        "[conteúdo]",
                    }
                    if texto.lower() in {x.lower() for x in lixo}:
                        texto = ""

                    st.session_state["insights"] = texto
                    st.session_state["insights_gerados"] = True

                except RateLimitError as e:
                    st.session_state["autorizar_insights"] = False
                    st.error(
                        "Sua chave da OpenAI está sem quota/crédito (erro 429). "
                        "Verifique Billing e a API Key nos Secrets do Streamlit."
                    )
                    st.caption(str(e))

                except Exception as e:
                    st.session_state["autorizar_insights"] = False
                    st.error("Falha ao gerar insights por um erro inesperado.")
                    st.caption(str(e))

        # -------- EXIBIÇÃO CONTROLADA --------
        if st.session_state["insights_gerados"] and st.session_state["insights"]:
            st.markdown(st.session_state["insights"])
        elif st.session_state["insights_gerados"] and not st.session_state["insights"]:
            st.warning(
                "A IA retornou um conteúdo inválido ou genérico. "
                "Clique novamente para gerar o insight."
            )

        st.markdown("---")

        # ---------------------------------------------------------------------
        # IA — CONTEÚDOS MULTICANAIS
        # ---------------------------------------------------------------------
        st.subheader("Conteúdo Multicanal Gerado Automaticamente")

        # <<< GOVERNANÇA DE IA: só habilita o botão de conteúdo após insights
        if st.session_state["insights_gerados"]:
            if st.button("Gerar Conteúdos Multicanais", use_container_width=True):
                st.session_state["autorizar_conteudos"] = True

            # Executa sob demanda (sem rerun forçado)
            if st.session_state["autorizar_conteudos"] and not st.session_state["conteudos_multicanais"]:
                with st.spinner("Criando textos completos para todos os canais..."):
                    st.session_state["conteudos_multicanais"] = gerar_conteudos_multicanais(
                        st.session_state["insights"]
                    )
        else:
            st.caption("Gere os **Insights Profundos** primeiro para liberar a geração multicanal.")

        if st.session_state["conteudos_multicanais"]:
            st.markdown(st.session_state["conteudos_multicanais"])

if __name__ == "__main__":
    main()