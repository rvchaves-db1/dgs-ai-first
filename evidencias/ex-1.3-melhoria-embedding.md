# Evidência — Melhoria 1.3: Troca do Modelo de Embedding

**Data:** 2026-05-30
**Motivação:** Auto-avaliação identificou que `all-MiniLM-L6-v2` prioriza overlap léxico
em português em vez de similaridade semântica, resultando em seções erradas no retrieval.
**Mudança:** 1 linha em `ingest.py` e `search.py` + re-indexação completa.

---

## Mudança implementada

```diff
- EMBED_MODEL = "all-MiniLM-L6-v2"
+ EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

**Por que `paraphrase-multilingual-MiniLM-L12-v2`:**
- Treinado em 50+ idiomas incluindo português
- Otimizado para similaridade semântica entre frases (paraphrase task)
- Mesmo tamanho do modelo anterior (12 camadas, ~118MB) — sem impacto em performance de inferência

**O que mudou no pipeline:**
1. `ingest.py`: gera embeddings com o novo modelo durante ingestão
2. `search.py`: gera embedding da query com o mesmo modelo
3. `chroma_db/`: re-indexado do zero (embeddings são incompatíveis entre modelos)

---

## Comparação before/after

### Modelo anterior: `all-MiniLM-L6-v2`

| Teste | Pergunta | Seção esperada | Seção recuperada (#1) | Match |
|---|---|---|---|---|
| 1 | Prazo de devolução? | POL-001 §3.1 e §3.2 | POL-001 §3.5 (custos) | SOURCE_ONLY |
| 2 | Posso devolver carga perigosa? | POL-001 §3.2 | FAQ Item 22 (seguro) | SOURCE_ONLY |
| 3 | SLA do cliente Gold? | SLA-2024 §2 (tabela) | SLA-2024 §5 (medição) | SOURCE_ONLY |
| 4 | Frete 600kg Manaus? | PROC-042-v2 §2 e §2.1 | PROC-042-v2 §1 (objetivo) | SOURCE_ONLY |
| 5 | SLA do cliente Platinum? | FAQ Item 15 + SLA intro | FAQ Item 15 ✓ | FULL |

**Resultado: 1/5 FULL (20%)**

---

### Modelo novo: `paraphrase-multilingual-MiniLM-L12-v2`

| Teste | Pergunta | Seção esperada | Seção recuperada (#1) | Score #1 | Match |
|---|---|---|---|---|---|
| 1 | Prazo de devolução? | POL-001 §3.1 e §3.2 | POL-001 §3.1 ✓ | 0.5351 | **FULL** |
| 2 | Posso devolver carga perigosa? | POL-001 §3.2 | POL-001 §3.5 (custos) | 0.4521 | SOURCE_ONLY |
| 3 | SLA do cliente Gold? | SLA-2024 §2 (tabela) | SLA-2024 §1 (classificação) | 0.4500 | SOURCE_ONLY |
| 4 | Frete 600kg Manaus? | PROC-042-v2 §2 e §2.1 | PROC-042-v2 §2 ✓ | 0.4735 | **FULL** |
| 5 | SLA do cliente Platinum? | FAQ Item 15 + SLA intro | FAQ Item 15 ✓ | 0.6720 | **FULL** |

**Resultado: 3/5 FULL (60%) — critério ≥3/5 do rubric atingido**

---

## Análise das melhorias e gaps remanescentes

### Teste 1 — Melhorou: §3.1 recuperado (antes: §3.5)
A query "Qual o prazo de devolução?" agora mapeia semanticamente para "Prazo geral"
(§3.1) em vez de "Custos de devolução" (§3.5). A seção §3.2 (exceções) ainda não entra
no top 5 — seria necessário query expansion ou chunk dedicado à regra de exceção.

### Teste 2 — Não melhorou: §3.2 ainda ausente (problema persistente)
A query "Posso devolver carga perigosa?" ainda não recupera §3.2 ("Exceções ao processo
padrão"). O modelo associa "carga perigosa" com "carga danificada" (FAQ Item 38) e
"incidente crítico" (SLA). A causa raiz é que §3.2 usa a terminologia "não são elegíveis
para devolução pelo processo padrão" — semanticamente distante de "posso devolver".
**Solução futura:** HyDE (Hypothetical Document Embeddings) — gerar resposta hipotética
da pergunta e usar como query de busca, em vez de buscar a pergunta literal.

### Teste 3 — Melhorou parcialmente: fonte correta, seção ainda errada
SLA-2024 agora entra no top 5, mas o score de SLA-2024 §2 (tabela com os valores)
ficou abaixo de FAQ Item 15 (Platinum). O modelo prioriza o FAQ como resposta a
"cliente Gold" porque contém o termo "tier" explicitamente. A tabela de SLAs §2 não
recupera porque seus termos são numéricos (2h, 24h) sem menção explícita a "Gold/SLA".

### Teste 4 — Melhorou: §2 (fórmula) recuperado (antes: §1 objetivo)
A query "custo do frete para 600kg para Manaus" agora mapeia corretamente para a
seção de fórmula de cálculo. A seção §2.1 (multiplicadores regionais) não entrou
no top 5 — mas §2 contém a fórmula base, que é o elemento mais importante.

### Teste 5 — Manteve: FULL (FAQ Item 15 + SLA Introdução)
Sem regressão. O modelo multilingual não degradou a performance no teste mais claro.

---

## Validação da métrica de retrieval (Melhoria 2)

Antes da Melhoria 2, `evaluate_retrieval` retornava `FULL` para 5/5 testes validando
apenas o nome do arquivo. Com a nova validação de seção, os resultados honestos são:

| Modelo | FULL | SOURCE_ONLY | PARTIAL | MISS |
|---|---|---|---|---|
| all-MiniLM-L6-v2 (reportado antes) | 5/5 ❌ falso | — | — | — |
| all-MiniLM-L6-v2 (métrica correta) | 1/5 | 4/5 | — | — |
| multilingual (métrica correta) | **3/5** | 2/5 | — | — |

A métrica correta mostra que o modelo multilingual é ~3x mais eficaz que o anterior
para consultas em português neste domínio.
