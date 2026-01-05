# ============================================================
#  ILUMEO - ETL COMPLETO PARA PESQUISAS
#  Versão com LOGS para Streamlit
#  Franciane Rodrigues
# ============================================================

import pandas as pd
import numpy as np
import json
import re
from collections import defaultdict

# ------------------------------------------------------------
# 1. CARREGAMENTO E PADRONIZAÇÃO DE CABEÇALHOS
# ------------------------------------------------------------

def carregar_e_padronizar_dados(path, log):

    try:
        df = pd.read_excel(path, header=[0, 1])

        def clean_header(col):
            question, option = col

            if "Unnamed" in str(option) or not str(option):
                return str(question).strip()

            if "Unnamed" in str(question):
                return str(option).strip()

            return f"{str(question).strip()} - {str(option).strip()}"

        df.columns = [clean_header(col) for col in df.columns]

        log("✅ Arquivo carregado e cabeçalhos unificados com sucesso.")
        return df

    except Exception as e:
        log(f"❌ Erro ao processar arquivo: {e}")
        return None


# ------------------------------------------------------------
# 2. FILTRO DE RESPONDENTES
# ------------------------------------------------------------

def filtrar_respondentes_validos(df, log):

    coluna_filtro = "RESPOSTA ESTÁ DENTRO DA PROPORCIONALIZAÇÃO? - imported_in_delfos"

    if coluna_filtro in df.columns:
        linhas_iniciais = df.shape[0]
        df = df[df[coluna_filtro] != "NÃO"]
        removidos = linhas_iniciais - df.shape[0]
        log(f"✅ Filtragem aplicada: {removidos} removidos. Total final: {df.shape[0]}")
    else:
        log(f"⚠️ Coluna '{coluna_filtro}' não encontrada. Nenhuma linha removida.")

    return df


# ------------------------------------------------------------
# 3. REMOVER COLUNAS INDESEJADAS
# ------------------------------------------------------------

def limpar_colunas_indesejadas(df, log):

    termos_proibidos = [
        "RESPOSTA ESTÁ DENTRO DA PROPORCIONALIZAÇÃO? - imported_in_delfos",
        "respondent_id - respondent_id",
        "user_invitation_code - user_invitation_code",
        "collector_id - collector_id",
        "date_created - date_created",
        "date_modified - date_modified",
        "ip_address - ip_address",
        "status - status",
        "total_time - total_time",
        "complement_status - complement_status",
        "Você estuda ou trabalha em uma dessas atividades? #prof - Response",
        "Você estuda ou trabalha em uma dessas atividades? #prof - Outro (especifique)",
        "#awesp", "#aberta_op", "#faw", "#fkn", "#flk", "#fco", "#fpr", "#clt", "#rej", "#mar",
        "PRIMEIRA PALAVRA", "{{", "PRÓXIMA COMPRA",
        "Você gostou de responder essa pesquisa? - Response"
    ]

    colunas_para_remover = []

    for col in df.columns:
        if any(termo in col for termo in termos_proibidos):
            colunas_para_remover.append(col)

    n_antes = df.shape[1]
    df = df.drop(columns=colunas_para_remover, errors="ignore")
    n_depois = df.shape[1]

    log(f"✅ Remoção de colunas: {n_antes - n_depois} colunas removidas.")
    log(f"📊 Shape após limpeza de colunas: {df.shape}")

    return df


# ------------------------------------------------------------
# 4. AJUSTE DE CIDADE E GÊNERO
# ------------------------------------------------------------

def ajustar_cidade_genero(df, log):

    # CIDADE
    col1 = "Em qual cidade você mora? #cid - Response"
    col2 = "Em qual cidade você mora? #cid - Outro (especifique)"

    if col1 in df.columns and col2 in df.columns:
        df[col1] = df[col1].replace("", np.nan).fillna(df[col2])
        df = df.drop(columns=[col2], errors="ignore")

    # GÊNERO
    col3 = "Qual é o seu gênero ? #gen - Response"
    col4 = "Qual é o seu gênero ? #gen - Outro (especifique)"

    if col3 in df.columns and col4 in df.columns:
        df[col3] = df[col3].replace("", np.nan).fillna(df[col4])
        df = df.drop(columns=[col4], errors="ignore")

    log("👤 Ajuste de cidade e gênero concluído.")
    return df


# ------------------------------------------------------------
# 5. REMOVER HTML
# ------------------------------------------------------------

def remove_html(text):
    if pd.isna(text):
        return text
    return re.sub(r"<.*?>", "", str(text)).strip()


def limpar_html_df(df, log):
    df = df.apply(lambda col: col.map(remove_html) if col.dtype == "object" else col)
    log("🧽 Remoção de HTML aplicada às colunas de texto.")
    return df


# ------------------------------------------------------------
# 6. LIMPEZA ESCALA LIKERT
# ------------------------------------------------------------

def limpar_likert(valor):
    if pd.isna(valor):
        return np.nan
    valor_str = str(valor).strip()
    if valor_str.startswith("0"): return 0
    if valor_str.startswith("10"): return 10
    if valor_str.isdigit(): return int(valor_str)
    return np.nan


def limpar_escalas(df, log):

    colunas_escala = [
        col for col in df.columns
        if "gostaria de" in col.lower()
        or "receber como presente" in col.lower()
        or "nota" in col.lower()
    ]

    log(f"🔄 Limpeza Likert em {len(colunas_escala)} colunas...")

    for col in colunas_escala:
        df[col] = df[col].apply(limpar_likert)
        df[col] = pd.to_numeric(df[col], errors="coerce")

    log("✅ Limpeza de escalas concluída.")
    return df


# ------------------------------------------------------------
# 7. FUNÇÕES DE GERAÇÃO DE TABELAS (SIMPLES, MULTI, MATRIZ TEXTO, MATRIZ NOTA)
# ------------------------------------------------------------

def identificar_colunas_simples(df):
    col_response = [c for c in df.columns if "response" in c.lower()]
    col_not_multi = [c for c in df.columns if " - " not in c]
    numericas = df.select_dtypes(include=["int", "float"]).columns.tolist()
    colunas = list(set(col_response + col_not_multi))
    return [c for c in colunas if c not in numericas]


def encontrar_colunas_hifen(df):
    return [c for c in df.columns if " - " in c and "response" not in c.lower()]


def agrupar_por_pergunta(colunas):
    grupos = defaultdict(list)
    for col in colunas:
        pergunta = col.split(" - ")[0].strip()
        grupos[pergunta].append(col)
    return grupos


def classificar_perguntas(df, grupos):
    grupos_multi = {}
    grupos_texto = {}
    grupos_nota = {}

    for pergunta, cols in grupos.items():
        exemplo = cols[0]
        serie = df[exemplo].dropna()

        if pd.api.types.is_numeric_dtype(serie):
            grupos_nota[pergunta] = cols
            continue

        marca_ex = exemplo.split(" - ")[1].strip()
        valores = serie.astype(str).str.strip().unique()

        if marca_ex in valores:
            grupos_multi[pergunta] = cols
        else:
            grupos_texto[pergunta] = cols

    return grupos_multi, grupos_texto, grupos_nota


def tabelas_simples(df, colunas):
    t = {}
    for col in colunas:
        abs_ = df[col].value_counts(dropna=False)
        rel_ = df[col].value_counts(normalize=True, dropna=False) * 100
        t[col] = pd.DataFrame({
            "Frequência Absoluta": abs_,
            "Frequência Relativa (%)": rel_.round(1)
        })
    return t


def tabelas_multiresposta(df, grupos):
    t = {}
    total = len(df)

    for pergunta, cols in grupos.items():
        marcas = []
        abs_list = []
        rel_list = []

        for col in cols:
            marca = col.split(" - ")[1].strip()
            freq_abs = (df[col] == marca).sum()
            freq_rel = (freq_abs / total * 100) if total else 0

            marcas.append(marca)
            abs_list.append(freq_abs)
            rel_list.append(round(freq_rel, 1))

        t[pergunta] = pd.DataFrame({
            "Frequência Absoluta": abs_list,
            "Frequência Relativa (%)": rel_list
        }, index=marcas)

    return t


def tabelas_matriz_texto(df, grupos):
    t = {}
    for pergunta, cols in grupos.items():
        meios = {}
        for col in cols:
            meio = col.split(" - ")[1].strip()
            serie = df[col].dropna().astype(str).str.strip()
            abs_ = serie.value_counts()
            rel_ = (serie.value_counts(normalize=True) * 100).round(1)
            meios[meio] = pd.DataFrame({
                "Frequência Absoluta": abs_,
                "Frequência Relativa (%)": rel_
            })
        t[pergunta] = meios
    return t


def tabelas_matriz_nota(df, grupos):
    t = {}
    for pergunta, cols in grupos.items():
        marcas = {}
        for col in cols:
            marca = col.split(" - ")[1].strip()
            serie = df[col].dropna()
            abs_ = serie.value_counts().sort_index()
            rel_ = (serie.value_counts(normalize=True).sort_index() * 100).round(1)
            marcas[marca] = pd.DataFrame({
                "Frequência Absoluta": abs_,
                "Frequência Relativa (%)": rel_
            })
        t[pergunta] = marcas
    return t


def gerar_todas_as_tabelas(df):
    col_simples = identificar_colunas_simples(df)
    t_simples = tabelas_simples(df, col_simples)

    col_hifen = encontrar_colunas_hifen(df)
    grupos = agrupar_por_pergunta(col_hifen)
    grupos_multi, grupos_texto, grupos_nota = classificar_perguntas(df, grupos)

    t_multi = tabelas_multiresposta(df, grupos_multi)
    t_matriz = tabelas_matriz_texto(df, grupos_texto)
    t_nota = tabelas_matriz_nota(df, grupos_nota)

    return t_simples, t_multi, t_matriz, t_nota


def gerar_json_todas_as_tabelas(t_simples, t_multi, t_matriz, t_nota):

    resultado = {
        "perguntas_simples": [],
        "multirresposta": [],
        "matriz_texto": [],
        "matriz_nota": []
    }

    for pergunta, tabela in t_simples.items():
        resultado["perguntas_simples"].append({
            "pergunta": pergunta,
            "tabela": tabela.reset_index().rename(columns={"index": "Resposta"}).to_dict(orient="records")
        })

    for pergunta, tabela in t_multi.items():
        bloco = {"pergunta": pergunta, "marcas": []}
        for marca, row in tabela.iterrows():
            bloco["marcas"].append({
                "marca": marca,
                "frequencia_absoluta": int(row["Frequência Absoluta"]),
                "frequencia_relativa": float(row["Frequência Relativa (%)"])
            })
        resultado["multirresposta"].append(bloco)

    for pergunta, meios in t_matriz.items():
        bloco = {"pergunta": pergunta, "itens": []}
        for meio, tabela in meios.items():
            bloco["itens"].append({
                "item": meio,
                "tabela": tabela.reset_index().rename(columns={"index": "Resposta"}).to_dict(orient="records")
            })
        resultado["matriz_texto"].append(bloco)

    for pergunta, marcas in t_nota.items():
        bloco = {"pergunta": pergunta, "marcas": []}
        for marca, tabela in marcas.items():
            bloco["marcas"].append({
                "marca": marca,
                "tabela": tabela.reset_index().rename(columns={"index": "Nota"}).to_dict(orient="records")
            })
        resultado["matriz_nota"].append(bloco)

    return json.dumps(resultado, ensure_ascii=False, indent=2)


# ------------------------------------------------------------
# 8. PIPELINE PRINCIPAL
# ------------------------------------------------------------

def executar_etl(file_path):

    logs = []

    def log(msg):
        logs.append(msg)

    log("🚀 Iniciando ETL ILUMEO...")
    df = carregar_e_padronizar_dados(file_path, log)
    if df is None:
        log("❌ ETL abortado por erro no carregamento.")
        return None, None, None, None, None, logs

    df = filtrar_respondentes_validos(df, log)
    df = limpar_colunas_indesejadas(df, log)
    df = ajustar_cidade_genero(df, log)
    df = limpar_html_df(df, log)
    df = limpar_escalas(df, log)

    log("📊 Gerando tabelas de frequência...")
    t_simples, t_multi, t_matriz, t_nota = gerar_todas_as_tabelas(df)
    log("✅ Tabelas de frequência criadas.")

    resultado_json = gerar_json_todas_as_tabelas(t_simples, t_multi, t_matriz, t_nota)

    with open("resultado_pesquisa.json", "w", encoding="utf-8") as f:
        f.write(resultado_json)

    log("📁 JSON salvo como resultado_pesquisa.json")
    log("🏁 ETL finalizado com sucesso!")

    return df, t_simples, t_multi, t_matriz, t_nota, logs