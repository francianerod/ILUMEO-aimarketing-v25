# -------------------------------------------------------------------------------------------------------------
# ILUMEO - AI Marketing com Análise Automática
# Autora: Franciane Rodrigues
# -------------------------------------------------------------------------------------------------------------

import os
import json
import re
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# -------------------------------------------------------------------------------------------------------------
# CONFIGURAÇÕES INICIAIS
# -------------------------------------------------------------------------------------------------------------
load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

st.set_page_config(page_title="ILUMEO - AI Marketing", layout="wide")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

TIPOS_ANALISE = ["Linkedin", "Blog", "OnePage", "Notícias"]

# -------------------------------------------------------------------------------------------------------------
# ESTADO PERSISTENTE
# -------------------------------------------------------------------------------------------------------------
for k in ["historico_tabelas", "historico_insights", "historico_conteudos"]:
    if k not in st.session_state:
        st.session_state[k] = []

# -------------------------------------------------------------------------------------------------------------
# FUNÇÕES DE LIMPEZA
# -------------------------------------------------------------------------------------------------------------
def limpar_texto(texto):
    """Remove HTML e espaços extras."""
    if pd.isna(texto):
        return None
    texto = str(texto)
    texto = re.sub(r"<.*?>", "", texto)  # remove tags HTML, spans etc.
    return texto.strip()

def padronizar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Padroniza nomes de colunas."""
    df = df.copy()
    df.columns = [limpar_texto(c) for c in df.columns]
    return df

# -------------------------------------------------------------------------------------------------------------
# CONVERSÃO DELFOS → JSON (linha 1 perguntas, linha 2 itens, linha 3+ respondentes)
# -------------------------------------------------------------------------------------------------------------
def converter_para_json(df: pd.DataFrame, caminho_json: str) -> str:
    # Linha 1: perguntas
    perguntas = [limpar_texto(x) for x in df.iloc[0].tolist()]
    # Linha 2: itens
    itens = [limpar_texto(x) for x in df.iloc[1].tolist()]
    # Linha 3+: respostas
    respostas = df.iloc[2:].reset_index(drop=True)

    registros = []

    for _, row in respostas.iterrows():
        registro = {}
        for col_index, valor in enumerate(row):
            pergunta = perguntas[col_index]
            item = itens[col_index]
            resp = limpar_texto(valor)

            # chave = Pergunta ou Pergunta / Item
            chave = pergunta if item in [None, "", "nan"] else f"{pergunta} / {item}"

            # separa múltiplas respostas se tiver vírgula
            if isinstance(resp, str) and "," in resp:
                resp = [v.strip() for v in resp.split(",")]

            registro[chave] = resp

        registros.append(registro)

    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(registros, f, ensure_ascii=False, indent=4)

    return caminho_json

# -------------------------------------------------------------------------------------------------------------
# TABULAÇÃO ESTATÍSTICA + RESUMO PARA IA (SEM CREWAI)
# -------------------------------------------------------------------------------------------------------------
def analisar_dados_com_crewai(caminho_csv: str) -> str:
    """Tabula os dados com Pandas e gera insights com gpt-4o-mini."""
    try:
        df = pd.read_csv(caminho_csv)
        df = padronizar_dataframe(df)

        # Variáveis sociodemográficas (para segmentações)
        socio_cols = [
            col for col in df.columns
            if "#est" in col or "#cid" in col or "#gen" in col
            or "#idd" in col or "#esc" in col or "#cls" in col
        ]

        # Outras perguntas
        perguntas_cols = [c for c in df.columns if c not in socio_cols]

        tabelas_streamlit = []
        resumo_para_ia = []

        # ----------------------------------------------------------
        # GERA TABELAS DE FREQUÊNCIA + SEGMENTAÇÕES
        # ----------------------------------------------------------
        for pergunta in perguntas_cols:
            if df[pergunta].dropna().shape[0] == 0:
                continue

            # Frequência
            freq_abs = df[pergunta].value_counts(dropna=False)
            freq_rel = df[pergunta].value_counts(normalize=True, dropna=False) * 100

            tabela_freq = pd.DataFrame({
                "Alternativa": freq_abs.index,
                "Frequência (n)": freq_abs.values,
                "Frequência (%)": freq_rel.round(2)
            })

            tabelas_streamlit.append((f"Pergunta: {pergunta}", tabela_freq))

            # Resumo para IA (limitando número de linhas)
            resumo_para_ia.append(
                f"Pergunta: {pergunta}\n{tabela_freq.head(10).to_string(index=False)}"
            )

            # ------------------------------------------------------
            # SEGMENTAÇÕES DEMOGRÁFICAS
            # ------------------------------------------------------
            for socio in socio_cols:
                seg = pd.crosstab(df[pergunta], df[socio], normalize="columns") * 100
                seg = seg.round(2)

                tabelas_streamlit.append(
                    (f"Segmentação: {pergunta} x {socio}", seg)
                )

                resumo_para_ia.append(
                    f"Segmentação: {pergunta} x {socio}\n{seg.head(10).to_string()}"
                )

        # ----------------------------------------------------------
        # EXIBIR TODAS AS TABELAS NO STREAMLIT
        # ----------------------------------------------------------
        for titulo, tabela in tabelas_streamlit:
            st.markdown(f"### {titulo}")
            st.dataframe(tabela)

        # ----------------------------------------------------------
        # GERAR INSIGHTS COM OPENAI (SEM CREWAI)
        # ----------------------------------------------------------
        # limite de blocos resumidos enviados à IA (para não estourar tokens)
        max_itens_ia = 25
        texto_insumo = "\n\n".join(resumo_para_ia[:max_itens_ia])

        if not texto_insumo.strip():
            return "Nenhum dado disponível para análise."

        resposta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Você é um analista de dados sênior especializado em pesquisas de mercado. "
                        "Gere insights claros, objetivos e acionáveis a partir de tabelas de frequência "
                        "e segmentações demográficas."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        "A seguir estão tabelas de frequência e segmentações demográficas resumidas.\n"
                        "Explique os principais padrões, diferenças entre segmentos e oportunidades "
                        "para as marcas. Seja analítico, mas direto.\n\n"
                        f"{texto_insumo}"
                    )
                }
            ]
        )

        return resposta.choices[0].message.content

    except Exception as e:
        return f"⚠️ Erro na análise: {e}"

# -------------------------------------------------------------------------------------------------------------
# FORMATAR CONTEÚDO FINAL (OpenAI direto)
# -------------------------------------------------------------------------------------------------------------
def formatar_conteudo(insights: str, formato: str) -> str:
    prompts = {
        "Linkedin": """
        Transforme os insights abaixo em um post de LinkedIn:
        - Tom humano, profissional e acessível
        - Comece com uma frase de impacto
        - Parágrafos curtos
        - Finalize com uma chamada leve à ação
        """,
        "Blog": """
        Transforme os insights abaixo em um artigo de blog:
        - Crie um título chamativo
        - Estruture em seções com subtítulos
        - Explique os dados e implicações de forma didática
        - Conclua com recomendações práticas
        """,
        "OnePage": """
        Transforme os insights abaixo em uma OnePage executiva:
        - Comece com um título
        - Liste bullets curtos (máx. 12 palavras cada)
        - Foque em mensagens acionáveis para diretoria/marketing
        """,
        "Notícias": """
        Transforme os insights abaixo em uma notícia jornalística:
        - Parágrafo 1: resumo do principal achado
        - Parágrafo 2: dados que sustentam
        - Parágrafo 3: desdobramentos e contexto
        """
    }

    prompt = prompts[formato]

    resposta = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Você é um redator especialista em comunicação de dados."
            },
            {
                "role": "user",
                "content": prompt + "\n\nINSIGHTS:\n" + insights
            }
        ]
    )

    return resposta.choices[0].message.content

# -------------------------------------------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# -------------------------------------------------------------------------------------------------------------
def pagina_chat():
    st.markdown("""
        <h2 style='margin-bottom:0; color:black;'> ILUMEO - AI Marketing</h2>
        <hr style='border: 2px solid #FFA500; border-radius: 5px; margin-top: 5px;'>
        <p style='font-size:16px; color:#333;'>
        Olá! Seja bem-vindo(a) ao <strong>ILUMEO - AI Marketing</strong>.<br>
        Aqui, a inteligência artificial transforma seus dados em <em>insights estratégicos</em> e conteúdos prontos para comunicação.<br>
        Envie sua planilha ou arquivo CSV ao lado para começar a análise automática!
    """, unsafe_allow_html=True)

    # Pré-visualização
    if "df" in st.session_state:
        st.dataframe(st.session_state["df"].head())

        if st.button("🚀 Executar Análise"):
            with st.spinner("Processando tabulação e gerando insights..."):
                resultado = analisar_dados_com_crewai(st.session_state["caminho_csv"])
                st.session_state["resultado_tab"] = resultado
                st.session_state["historico_tabelas"].append(resultado)

    # Exibir insights da última análise
    if "resultado_tab" in st.session_state:
        st.markdown("### 🔍 Insights da Pesquisa")
        st.markdown(st.session_state["resultado_tab"])

    # Geração de conteúdo a partir dos insights
    if "resultado_tab" in st.session_state:
        st.markdown("### 🎨 Escolha o Formato do Conteúdo")
        formato = st.radio("Formato:", TIPOS_ANALISE, horizontal=True)

        if st.button("✍️ Gerar Conteúdo Final"):
            with st.spinner("Gerando conteúdo final..."):
                texto = formatar_conteudo(st.session_state["resultado_tab"], formato)
                st.session_state["conteudo_final"] = texto
                st.session_state["historico_conteudos"].append(
                    {"formato": formato, "texto": texto}
                )

    # Histórico de conteúdos gerados
    for i, item in enumerate(st.session_state["historico_conteudos"]):
        st.markdown(f"### 📝 Conteúdo {i+1} — {item['formato']}")
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

        # Leitura do arquivo original
        df = pd.read_excel(caminho) if arquivo.name.endswith(".xlsx") else pd.read_csv(caminho)
        df = padronizar_dataframe(df)

        # CSV para análise com Pandas
        caminho_csv = caminho.replace(".xlsx", ".csv")
        df.to_csv(caminho_csv, index=False)

        # JSON no formato pergunta/item/resposta
        caminho_json = caminho.replace(".xlsx", ".json").replace(".csv", ".json")
        converter_para_json(df, caminho_json)

        st.session_state.update({
            "df": df,
            "caminho_csv": caminho_csv,
            "caminho_json": caminho_json
        })

        st.success("✅ Arquivo convertido para CSV e JSON com sucesso!")
        st.write("📦 JSON gerado em:", caminho_json)

# -------------------------------------------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------------------------------------------
def main():
    with st.sidebar:
        sidebar()
    pagina_chat()

if __name__ == "__main__":
    main()