Markdown

# ILUMEO — AI Marketing & Intelligence Platform

ILUMEO - AI Marketing é uma plataforma de **Inteligência Artificial aplicada a Marketing e Conteúdo**, desenvolvida para transformar dados estruturados e vídeos do YouTube em **insights estratégicos profundos** e **conteúdos editoriais profissionais**, com **governança de IA, controle de custos e foco em uso real**.

O sistema foi concebido inicialmente com um fluxo principal orientado à análise de pesquisas e, posteriormente, evoluiu com a criação de um **módulo independente de YouTube → Blog**, mantendo arquitetura modular, controlada e escalável.

---
## 👩‍💻 Participantes

* Concepção Estratégica: Diego Senise - CEO da ILUMEO
* Arquitetura Técnica e Desenvolvimento: Franciane Rodrigues - Cientista de Dados e Consultora de IA da ILUMEO
* LinkedIn: https://www.linkedin.com/in/francianerod/
* ILUMEO: https://www.linkedin.com/company/ilumeo-consultoria/
* Site ILUMEO: https://ilumeo.com.br/
---

## ✨ Principais Funcionalidades

### 📊 ETL Inteligente de Pesquisas (Fluxo Principal)
* Upload de arquivos Excel (`.xlsx`)
* Processamento automático via pipeline ETL
* Geração de tabelas de frequência:
    * Perguntas simples
    * Multirresposta
    * Matrizes textuais
    * Matrizes de nota
* Consolidação final em JSON estruturado

---

### 🧠 IA Analítica — Insights Profundos
* Análise cruzada real dos dados da pesquisa
* Identificação de padrões, tendências e contradições
* Análise de barreiras, gatilhos e drivers de decisão
* Identificação de segmentações implícitas e clusters
* Linguagem estratégica, humana e orientada a marketing
* Execução apenas sob autorização explícita do usuário

---

### 📝 IA Criativa — Conteúdo Multicanal
A partir dos insights analíticos, o sistema gera automaticamente:
* Post para LinkedIn
* Artigo completo para Blog
* One Page Executiva
* Release Jornalístico

Os conteúdos são entregues prontos para publicação, seguindo regras editoriais específicas, sem metalinguagem ou explicações técnicas.

---

### 🎥 YouTube → Blog (Módulo Adicional e Independente)
Módulo criado posteriormente ao fluxo principal, funcionando de forma totalmente independente do ETL de pesquisas.
* Inserção de URL de vídeo do YouTube
* Transcrição automática do conteúdo:
    * Prioriza legendas oficiais
    * Fallback automático para Whisper (áudio)
* Geração de blog post profissional a partir da transcrição
* Cache inteligente por URL e por hash de conteúdo
* Possibilidade de reprocessamento sob demanda

---

## 🏗️ Arquitetura do Sistema

### 🔹 Fluxo Principal (Primeira Utilização)
`Upload Excel` → `ETL Automatizado` → `JSON Estruturado` → `IA Analítica` → `IA Criativa`

### 🔹 Módulo Adicional (Criado Posteriormente)
`URL YouTube` → `Legenda ou Whisper` → `Transcrição` → `Geração de Blog Post`

---

## 🛡️ Governança de IA
* **A IA não executa automaticamente:** Cada etapa exige autorização explícita do usuário.
* **Controle de execução:** Evita consumo excessivo de tokens, reexecuções involuntárias e inconsistência semântica.
* **Integridade:** Insights são gerados uma única vez por sessão e conteúdos multicanais dependem obrigatoriamente desses insights.
* **Modularidade:** O módulo YouTube opera de forma independente do fluxo ETL.

---

## 🧰 Tecnologias Utilizadas
* Python 3.10+
* Streamlit
* OpenAI API (GPT-4o, Whisper)
* CrewAI
* yt-dlp
* YouTube Transcript API
* Pandas
* FFmpeg

---

## ⚙️ Pré-requisitos
* Python 3.10 ou superior
* FFmpeg instalado e configurado no PATH
* Chave válida da OpenAI

---

## 🔐 Configuração de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
FFMPEG_PATH=C:/ffmpeg/bin/ffmpeg.exe
▶️ Como Executar
Instale as dependências:

Bash

pip install -r requirements.txt
Inicie a aplicação:

Bash

streamlit run aimarketing25.py
A aplicação será aberta automaticamente no navegador.

📁 Estrutura do Projeto
Plaintext

├── aimarketing25.py
├── etl_ilumeo2.py
├── prompts/
│   ├── linkedin.txt
│   ├── blog.txt
│   ├── one_page.txt
│   └── release.txt
├── temp/
├── logo.png
├── .env
└── requirements.txt

🚀 Status do Projeto
* Produto funcional e estável, pronto para uso
* Fluxo principal consolidado (ETL → Insights → Conteúdo)
* Módulo YouTube integrado de forma independente
* Base arquitetural preparada para crescimento enterprise

📌 Observação Final
ILUMEO não é um experimento de IA, mas uma plataforma orientada à tomada de decisão, construída para gerar valor real.
* Período de desenvolvimento: 27/09/2025 a 26/12/2025.
* Publicação oficial: 05/01/2026

