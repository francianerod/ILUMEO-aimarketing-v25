# -------------------------------------------------------------------------------------------------------------
# AI Marketing - Aplicação de Chat com Upload de Arquivos
# Descrição: Esta aplicação permite aos usuários interagir com um chatbot a partir dos seus dados de marketing.
# Autor: Franciane Rodrigues
# -------------------------------------------------------------------------------------------------------------

import os
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv

# -------------------------------------------------------------------------
# CARREGA A VARIÁVEL DE AMBIENTE A PARTIR DO ARQUIVO .env
# -------------------------------------------------------------------------
load_dotenv()  # Carrega variáveis do arquivo .env
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------------------------------------------------------
# CONFIGURAÇÕES GERAIS
# -------------------------------------------------------------------------
TIPOS_ARQUIVOS = ["Planilha (.xlsx)", "Texto (.csv)"]
st.set_page_config(page_title="ILUMEO - AI Marketing", layout="wide")

# -------------------------------------------------------------------------
# FUNÇÃO DE RESPOSTA DA IA
# -------------------------------------------------------------------------
def gerar_resposta(mensagens):
    try:
        resposta = client.chat.completions.create(model="gpt-4o-mini",
                                                  messages=[{"role": m[0], "content": m[1]} for m in mensagens]
                                                 )
        return resposta.choices[0].message.content
    except Exception as e:
        return f"⚠️ Erro ao conectar com a OpenAI: {e}"

# -------------------------------------------------------------------------
# PÁGINA DE CHAT
# -------------------------------------------------------------------------
def pagina_chat():
    # Título da página com linha laranja personalizada
    st.markdown(
        """
        <h2 style='margin-bottom:0; color:black;'>💬 ILUMEO - Projeto AI Marketing</h2>
        <hr style='border: 2px solid #FFA500; border-radius: 5px; margin-top: 5px;'>
        """,
        unsafe_allow_html=True
               )

    # Recupera as mensagens anteriores ou inicializa o chat
    mensagens = st.session_state.get('mensagens', [('assistant', 'Olá! Sou sua Assistente de IA em Marketing da ILUMEO. Como posso ajudar você hoje?')])

    # Exibe o histórico
    for msg in mensagens:
        with st.chat_message(msg[0]):
             st.markdown(msg[1])

    # Campo de entrada do usuário
    input_usuario = st.chat_input("Digite sua mensagem aqui...")
    if input_usuario:
        mensagens.append(('user', input_usuario))
        with st.chat_message("user"):
            st.markdown(input_usuario)

        # Gera resposta da OpenAI
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                resposta = gerar_resposta(mensagens)
                st.markdown(resposta)

        # Atualiza histórico
        mensagens.append(('assistant', resposta))
        st.session_state['mensagens'] = mensagens

# -------------------------------------------------------------------------
# BARRA LATERAL
# -------------------------------------------------------------------------
def sidebar():
    st.image("logo.png", width=180)
    st.subheader("📂 Upload de Arquivo")

    tipo_arquivo = st.selectbox("Selecione o tipo de arquivo:", TIPOS_ARQUIVOS)

    if tipo_arquivo == "Planilha (.xlsx)":
        arquivo = st.file_uploader("Faça o upload do arquivo Excel", type=["xlsx"])
    else:
        arquivo = st.file_uploader("Faça o upload do arquivo CSV", type=["csv"])

    if arquivo is not None:
        st.success(f"✅ Arquivo '{arquivo.name}' carregado com sucesso!")
        try:
            if tipo_arquivo == "Planilha (.xlsx)":
                df = pd.read_excel(arquivo)
            else:
                df = pd.read_csv(arquivo)
            st.dataframe(df.head())
        except Exception as e:
            st.error(f"Erro ao ler o arquivo: {e}")

# -------------------------------------------------------------------------
# MAIN
# -------------------------------------------------------------------------
def main():
    pagina_chat()
    with st.sidebar:
        sidebar()

if __name__ == "__main__":
    main()  