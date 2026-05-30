# dgs-ai-first — Certificação AI First DB1

**Participante:** Rafael Chaves  
**Papel:** Desenvolvedor  
**Fase:** 1 — Entendimento e Contexto

---

## Sobre o projeto

Prova de conceito de um assistente de IA para a NovaTech (empresa de logística fictícia),
construído como parte da certificação AI First da DB1. O assistente responde perguntas dos
atendentes com base na documentação interna da empresa, usando RAG (Retrieval-Augmented Generation).

---

## Exercícios

### Exercício 1.1 — Análise de viabilidade técnica
Análise dos desafios de cada tipo de fonte (PDFs, OCR, wiki, planilhas), estimativa da base
em tokens, análise de orçamento de contexto e estratégia de chunking.

- **Entregável:** [.spec/exercicio-1.1-analise-viabilidade-tecnica.md](.spec/exercicio-1.1-analise-viabilidade-tecnica.md)
- **Evidência de iteração com Claude:** [evidencias/ex-1.1-iteracao-claude.md](evidencias/ex-1.1-iteracao-claude.md)
- **Ferramenta:** Claude (chat)

---

### Exercício 1.2 — Prototipação de system prompt
Design do system prompt com mapeamento de contexto estático/dinâmico, testes com chunks
do Anexo B e iteração v1 → v2.

- **Entregável:** [.spec/exercicio-1.2-prototipacao-system-prompt.md](.spec/exercicio-1.2-prototipacao-system-prompt.md)
- **Evidência de testes:** [evidencias/ex-1.2-testes-v1-v2.md](evidencias/ex-1.2-testes-v1-v2.md)
- **Ferramenta:** Claude (chat)

---

### Exercício 1.3 — Pipeline de RAG open-source
Pipeline funcional em Python: ingestão de documentos, busca semântica e montagem de prompt,
testado com 5 perguntas do mapa de cobertura do Anexo B.

- **Spec:** [.spec/exercicio-1.3-pipeline-rag-spec.md](.spec/exercicio-1.3-pipeline-rag-spec.md)
- **Código:** [pipeline-rag/](pipeline-rag/)
- **Evidências do Claude Code:** [evidencias/ex-1.3-claude-code/](evidencias/ex-1.3-claude-code/)
- **Ferramentas:** Claude Code (VS Code)

---

## Stack do pipeline (Exercício 1.3)

- **Python 3.10+**
- **ChromaDB** — vector store local
- **sentence-transformers** (`all-MiniLM-L6-v2`) — embeddings open-source
- **LLM:** Claude (via chat manual)

## Instalação

```bash
cd pipeline-rag
pip install -r requirements.txt
python ingest.py
python test_pipeline.py
```
