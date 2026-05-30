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
- **ChromaDB** — vector store local persistente
- **sentence-transformers** (`paraphrase-multilingual-MiniLM-L12-v2`) — embeddings com suporte a PT-BR
- **LLM:** Claude (prompts gerados pelo pipeline, submetidos manualmente)

## Como usar

```bash
# 1. Instalar dependências
cd pipeline-rag
pip install -r requirements.txt

# 2. Indexar os documentos (rodar uma vez, ou ao trocar modelo/docs)
python ingest.py

# 3. Rodar os 5 testes — gera prompts prontos em test_results.json
python test_pipeline.py

# 4. Busca avulsa
python search.py "Qual o prazo de devolução para carga perigosa?"
```

Após `test_pipeline.py`, cole cada prompt de `test_results.json` no Claude e
preencha `llm_response` + `evaluation` + `notes` com os resultados.

## Evidências e avaliação

| Artefato | Descrição |
|---|---|
| [evidencias/ex-1.1-iteracao-claude.md](evidencias/ex-1.1-iteracao-claude.md) | Iteração com Claude no exercício 1.1 |
| [evidencias/ex-1.2-testes-v1-v2.md](evidencias/ex-1.2-testes-v1-v2.md) | Testes do system prompt v1 vs v2 |
| [evidencias/ex-1.3-claude-code/README.md](evidencias/ex-1.3-claude-code/README.md) | Interações com Claude Code no exercício 1.3 |
| [evidencias/ex-1.3-melhoria-embedding.md](evidencias/ex-1.3-melhoria-embedding.md) | Before/after da troca do modelo de embedding |
| [evidencias/ex-1.3-respostas-llm.md](evidencias/ex-1.3-respostas-llm.md) | Ciclo completo: prompts + respostas + avaliação |
| [evidencias/ex-reavaliacao-pos-melhorias.md](evidencias/ex-reavaliacao-pos-melhorias.md) | Reavaliação com a skill de correção da trilha |
