# Exercício 1.3 — Spec: Pipeline de RAG com Ferramentas Open-Source

**Participante:** Rafael Chaves  
**Papel:** Desenvolvedor  
**Data:** 2026-05-30  
**Stack:** Python + ChromaDB + sentence-transformers + LangChain (opcional)

---

## Objetivo

Construir uma prova de conceito funcional do pipeline de RAG que:
1. Ingere os 5 documentos da NovaTech (Anexo A)
2. Realiza busca semântica por similaridade
3. Monta o prompt completo pronto para enviar ao LLM
4. É testado com 5 perguntas do mapa de cobertura do Anexo B

---

## Estrutura de arquivos

```
pipeline-rag/
├── docs/                          # Documentos fonte (cópia dos .md do Anexo A)
│   ├── POL-001-politica-devolucao.md
│   ├── PROC-042-frete-especial-v1.md
│   ├── PROC-042-v2-frete-especial-revisado.md
│   ├── SLA-2024-tabela-sla-clientes.md
│   └── FAQ-atendimento.md
├── ingest.py                      # Script de ingestão: docs → chunks → embeddings → ChromaDB
├── search.py                      # Função de busca: pergunta → chunks similares
├── prompt_builder.py              # Função de montagem: chunks + pergunta → prompt completo
├── test_pipeline.py               # Testes com 5 perguntas do Anexo B
├── requirements.txt
└── chroma_db/                     # Diretório gerado pelo ChromaDB (não versionar)
```

---

## Dependências (`requirements.txt`)

```
chromadb>=0.4.0
sentence-transformers>=2.2.0
```

---

## Componente 1 — `ingest.py`

### Responsabilidade
Ler os documentos `.md`, dividir em chunks, gerar embeddings e persistir no ChromaDB.

### Estratégia de chunking
Conforme definido no Exercício 1.1: **chunking por seção semântica**, respeitando fronteiras de título Markdown (`##`, `###`), com tamanho máximo de 500 tokens e overlap de ~50 tokens entre chunks adjacentes de uma mesma seção.

Regras especiais:
- Blocos de tabela Markdown (`|---|`) são mantidos inteiros como um único chunk, mesmo que ultrapassem 500 tokens.
- Cada chunk recebe metadados obrigatórios: `source` (nome do arquivo), `section` (título da seção pai), `doc_version` (extraído do frontmatter do `.md`), `doc_date` (data de emissão).

### Interface esperada

```python
def load_documents(docs_dir: str) -> list[dict]:
    """Retorna lista de dicts com 'content' e 'metadata' por arquivo."""

def split_into_chunks(document: dict) -> list[dict]:
    """
    Divide um documento em chunks semânticos.
    Cada chunk: {'text': str, 'metadata': dict}
    Preserva tabelas inteiras. Respeita fronteiras de seção.
    """

def ingest_to_chromadb(chunks: list[dict], collection_name: str = "novatech") -> None:
    """Gera embeddings com sentence-transformers e persiste no ChromaDB local."""
```

### Modelo de embedding
`all-MiniLM-L6-v2` (sentence-transformers) — leve, gratuito, adequado para português com vocabulário técnico simples.

### Metadados por chunk (schema)

```python
{
    "source": "PROC-042-v2-frete-especial-revisado.md",
    "section": "2.1 Multiplicadores regionais",
    "doc_version": "2.0",
    "doc_date": "2023-11-10",
    "chunk_index": 3,          # posição do chunk no documento
    "source_quality": "native" # "native" | "ocr" (para PDFs escaneados)
}
```

---

## Componente 2 — `search.py`

### Responsabilidade
Receber uma pergunta em linguagem natural, gerar seu embedding, buscar os N chunks mais similares no ChromaDB e retornar com scores.

### Interface esperada

```python
def search(
    query: str,
    collection_name: str = "novatech",
    n_results: int = 5
) -> list[dict]:
    """
    Retorna lista de dicts:
    {
        'text': str,
        'metadata': dict,
        'similarity_score': float  # 0.0 a 1.0, maior = mais similar
    }
    Ordenado por score descendente.
    """
```

### Comportamento esperado
- Retornar `n_results` chunks, mesmo que os últimos tenham score baixo (o chamador decide o threshold).
- Incluir o score de similaridade para que o `prompt_builder` possa decidir o posicionamento dos chunks (mais relevantes no início/fim — mitigação do *lost in the middle*).

---

## Componente 3 — `prompt_builder.py`

### Responsabilidade
Receber os chunks recuperados e a pergunta do atendente e montar o prompt completo no formato definido no Exercício 1.2 (System Prompt v2).

### Interface esperada

```python
def build_prompt(
    query: str,
    chunks: list[dict],
    client_tier: str = None,      # "Gold" | "Silver" | "Standard" | None
    conversation_history: list[dict] = None  # [{"role": "user"|"assistant", "content": str}]
) -> str:
    """
    Retorna o prompt completo pronto para enviar ao LLM.
    Estrutura: system prompt (estático) + metadados do cliente (dinâmico)
               + chunks ordenados (dinâmico) + histórico (dinâmico) + pergunta.
    Chunks são posicionados com os de maior score no início e no fim
    (mitigação lost in the middle).
    """

def estimate_tokens(text: str) -> int:
    """Estimativa rápida: len(text) // 4"""
```

### Ordenação dos chunks no contexto
Para mitigar o efeito *lost in the middle*:
1. Ordenar chunks por score descendente.
2. Posicionar o chunk de maior score primeiro.
3. Posicionar o segundo chunk de maior score por último.
4. Preencher o meio com os demais chunks em ordem decrescente de score.

### Detecção de documentos contraditórios
Se dois chunks recuperados tiverem `source` diferente mas `section` com mesmo prefixo (ex: `PROC-042` e `PROC-042-v2`), incluir aviso no prompt:

```
[AVISO: Foram encontradas duas versões do documento PROC-042.
 A versão mais recente (2023-11-10) foi posicionada primeiro.
 Priorize-a, mas informe ao atendente que existe uma versão anterior.]
```

---

## Componente 4 — `test_pipeline.py`

### 5 perguntas de teste (do mapa de cobertura do Anexo B)

| # | Pergunta | Chunks esperados (gabarito) | Armadilha |
|---|---|---|---|
| 1 | "Qual o prazo de devolução?" | POL-001-A, POL-001-B | Regra geral vs. exceção |
| 2 | "Posso devolver carga perigosa?" | POL-001-B | Inversão da regra (NÃO pode) |
| 3 | "Qual o SLA do cliente Gold?" | SLA-2024-B | Omitir SLA crítico |
| 4 | "Frete para 600kg para Manaus?" | PROC-042v2-B, PROC-042v2-A | Misturar versões v1/v2 |
| 5 | "Qual o SLA do cliente Platinum?" | SLA-2024-A | Alucinação de tier inexistente |

### Para cada teste, documentar:
- Chunks recuperados (IDs e scores)
- Se batem com o gabarito do Anexo B (sim / parcial / não)
- Prompt montado (conteúdo completo)
- Resposta obtida colando o prompt no Claude chat
- Avaliação: correta / parcialmente correta / incorreta + justificativa

### Estrutura de saída esperada por teste

```python
{
    "question": str,
    "retrieved_chunks": [{"id": str, "score": float, "text": str}],
    "expected_chunks": [str],          # gabarito do Anexo B
    "retrieval_match": "full" | "partial" | "miss",
    "prompt": str,                     # prompt montado completo
    "llm_response": str,               # resposta do Claude chat
    "evaluation": "correct" | "partial" | "incorrect",
    "notes": str                       # análise do participante
}
```

---

## Problemas esperados e propostas de correção

Com base nos documentos do Anexo A, estes problemas são previsíveis:

### Problema 1 — Chunks concorrentes de PROC-042 v1 e v2
**Sintoma:** Para a pergunta sobre frete para Manaus, o retrieval retorna chunks de ambas as versões. Sem filtro, o LLM pode misturar multiplicadores antigos (Norte: 1.6) com novos (Norte: 1.8).

**Correção proposta:** No `search.py`, implementar deduplicação por família de documento: se dois chunks têm o mesmo prefixo de `source` (ex: `PROC-042`), manter apenas o da versão com `doc_date` mais recente.

### Problema 2 — FAQ como fonte para informações sem respaldo formal
**Sintoma:** Perguntas sobre carga danificada ou frete expresso com carga perigosa retornam apenas chunks do FAQ (sem documento formal). O LLM pode responder com alta confiança usando fonte informal.

**Correção proposta:** No `prompt_builder.py`, injetar aviso quando todos os chunks de uma resposta têm `source` começando com `FAQ`: `[ATENÇÃO: Esta resposta é baseada apenas no FAQ informal. Confirme com a documentação normativa antes de informar ao cliente.]`

### Problema 3 — Chunking de tabelas Markdown pode falhar em tabelas grandes
**Sintoma:** A tabela de SLAs (SLA-2024, seção 2) tem múltiplas linhas e colunas. Se o parser não identificar corretamente os delimitadores `|---|`, a tabela é tratada como texto corrido e dividida no meio.

**Correção proposta:** No `ingest.py`, usar regex para detectar início (`| --- |` ou `|:---|`) e fim de blocos de tabela antes de aplicar o chunking por seção. Envolver o bloco inteiro em um único chunk.

---

## Critérios de aceite

- [ ] `ingest.py` roda sem erros nos 5 documentos e popula o ChromaDB
- [ ] `search.py` retorna chunks com score de similaridade para qualquer pergunta
- [ ] `prompt_builder.py` monta prompt dentro do orçamento de tokens (< 8.000 tokens)
- [ ] Testes 1–5 documentados com retrieval, prompt e resposta do LLM
- [ ] Ao menos 2 problemas identificados com proposta de correção concreta
