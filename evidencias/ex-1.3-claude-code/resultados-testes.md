# Resultados dos Testes — Exercício 1.3

**Data:** 2026-05-30  
**Pipeline:** ingest.py + search.py + prompt_builder.py  
**Modelo de embedding:** all-MiniLM-L6-v2  
**Base indexada:** 39 chunks / 5 documentos

---

## Sumário dos testes

| # | Pergunta | Match fonte | Seção correta | Prompt (tokens) |
|---|---|---|---|---|
| 1 | Qual o prazo de devolução? | FULL | NÃO | ~849 |
| 2 | Posso devolver carga perigosa? | FULL | NÃO | ~931 |
| 3 | Qual o SLA do cliente Gold? | FULL | NÃO | ~781 |
| 4 | Qual o custo do frete para 600kg para Manaus? | FULL | PARCIAL | ~760 |
| 5 | Qual o SLA do cliente Platinum? | FULL | SIM | ~713 |

---

## Detalhes por teste

### Teste 1 — "Qual o prazo de devolução?"
**Chunks esperados:** POL-001 seção 3.1 (prazo) e 3.2 (exceções)  
**Chunks recuperados:**
- score=0.5648 | POL-001 — **3.5. Custos de devolução** ← seção errada
- score=0.5059 | SLA-2024 — 3. Definição de incidente crítico ← irrelevante
- score=0.4743 | FAQ — Item 8 frete especial ← irrelevante
- score=0.4379 | PROC-042-v2 — Prazo de entrega frete especial ← irrelevante

**Análise:** A fonte correta foi recuperada (POL-001), mas a seção 3.5 (custos) teve score maior que 3.1 (prazo) e 3.2 (exceções), que não entraram no top 5. O modelo priorizou a seção que contém mais ocorrências de "devolução" (lexical overlap) em vez da semanticamente correta.

---

### Teste 2 — "Posso devolver carga perigosa?"
**Chunks esperados:** POL-001 seção 3.2 (exceções — cargas perigosas NÃO podem)  
**Chunks recuperados:**
- score=0.5449 | FAQ — Item 22 seguro de carga ← irrelevante
- score=0.5345 | SLA-2024 — incidente crítico ← parcialmente relevante (menciona carga perigosa)
- score=0.5102 | PROC-042-v2 — Condições especiais ← relevante (menciona carga perigosa)
- score=0.4945 | POL-001 — 3.5. Custos ← seção errada

**Análise:** A seção 3.2 com a regra de exclusão de cargas perigosas NÃO foi recuperada. O modelo não associou "posso devolver carga perigosa" com "NÃO são elegíveis para devolução pelo processo padrão". Risco alto: o LLM poderia responder incorretamente sem ter o chunk com a regra de exclusão explícita.

---

### Teste 3 — "Qual o SLA do cliente Gold?"
**Chunks esperados:** SLA-2024 seção 2 (tabela de SLAs)  
**Chunks recuperados:**
- score=0.5600 | SLA-2024 — **5. Medição e reportes** ← seção errada
- score=0.5311 | FAQ — Item 27 tracking ← irrelevante
- score=0.4017 | POL-001 — 3.3. Procedimento ← irrelevante

**Análise:** A seção 2 (tabela com os valores reais de SLA) não entrou no top 3. A seção 5 (medição) teve score maior porque contém o termo "SLA" repetidamente. O LLM não receberia os valores de SLA (2h/24h para Gold) para responder corretamente.

---

### Teste 4 — "Qual o custo do frete para 600kg para Manaus?"
**Chunks esperados:** PROC-042-v2 seção 2.1 (multiplicadores) e seção 2 (fórmula)  
**Chunks recuperados:**
- score=0.5413 | PROC-042-v2 — **1. Objetivo** ← introdução, não os multiplicadores
- score=0.4850 | SLA-2024 — 2. Tabela de SLAs ← irrelevante
- score=0.4774 | FAQ — Item 27 ← irrelevante

**Análise:** A seção com os multiplicadores regionais (2.1) e a fórmula (seção 2) não foram recuperadas. A deduplicação de versões funcionou (v1 não apareceu), mas as seções relevantes da v2 ficaram abaixo do threshold.

---

### Teste 5 — "Qual o SLA do cliente Platinum?"
**Chunks esperados:** SLA-2024 seção 1 (que diz que Platinum não existe)  
**Chunks recuperados:**
- score=0.5382 | FAQ-15 — "Cliente diz que é Platinum. Existe esse tier?" ✓ correto
- score=0.5097 | SLA-2024 — Introdução ✓ correto
- score=0.4962 | POL-001 — 3.5 Custos ← irrelevante

**Análise:** Único teste com retrieval semanticamente correto. O FAQ-15 e SLA-2024 Introdução contêm a informação de que Platinum não existe. O LLM teria o contexto certo para responder corretamente.

---

## Problemas identificados

### Problema 1 — Modelo de embedding não otimizado para português (crítico)

**Sintoma:** `all-MiniLM-L6-v2` é treinado principalmente em inglês. Para perguntas em português, o modelo prioriza overlap léxico (frequência da palavra "devolução") em vez de similaridade semântica real. Resultado: seções com mais ocorrências da palavra-chave ganham score maior que as seções semanticamente corretas.

**Impacto:** 4 dos 5 testes recuperaram seções erradas dentro do documento correto. O LLM recebe contexto incompleto e pode responder de forma imprecisa ou alucinada.

**Correção proposta:** Substituir `all-MiniLM-L6-v2` por `paraphrase-multilingual-MiniLM-L12-v2`, modelo sentence-transformers com suporte explícito a 50+ idiomas incluindo português. Mudança de 1 linha em `ingest.py` e `search.py`:
```python
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

---

### Problema 2 — Avaliação de retrieval valida fonte, não seção (retrieval falso-positivo)

**Sintoma:** A função `evaluate_retrieval` retornou `FULL` para 5/5 testes porque verificou apenas o nome do arquivo fonte, não a seção específica. Na prática, 4 dos 5 testes trouxeram seções erradas dentro do arquivo correto.

**Impacto:** Métrica de qualidade do retrieval enganosa — o pipeline parece funcionar melhor do que está. Em produção, respostas incorretas passariam despercebidas.

**Correção proposta:** Adicionar validação de seção na função `evaluate_retrieval`:
```python
def evaluate_retrieval(retrieved, expected_sources, expected_sections=None):
    # Validar fonte (atual)
    source_match = ...
    # Validar seção (novo)
    if expected_sections:
        section_match = any(
            es in r["metadata"].get("section", "")
            for r in retrieved
            for es in expected_sections
        )
    ...
```

---

## Conclusão

O pipeline está funcional end-to-end (ingestão → busca → montagem de prompt), mas o modelo de embedding é o gargalo principal. A troca para um modelo multilingual resolveria os problemas de retrieval semântico sem alterações na arquitetura do pipeline. Os prompts gerados estão dentro do orçamento de tokens (< 1.000 tokens em todos os casos), e a deduplicação de versões funcionou corretamente no teste 4.
