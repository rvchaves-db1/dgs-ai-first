# Evidências — Exercício 1.3: Claude Code (VS Code)

Ferramenta utilizada: **Claude Code** (extensão VS Code da Anthropic), no lugar do
GitHub Copilot. Ambas são ferramentas de IA para desenvolvimento — Claude Code foi
escolhido por já estar integrado ao fluxo de trabalho do projeto.

---

## Interação 1 — Diagnóstico de falha de retrieval e planejamento de melhorias

**Contexto:** Após a auto-avaliação com as skills de correção, Claude Code foi usado para
analisar os problemas do exercício 1.3 e estruturar um plano de implementação.

**Prompt submetido:**
> "considerando que sou dev, avalia a pasta Correção, que deve ter instruções para
> correção do projeto [...] cria uma spec com a avaliação sobre o que melhorar.
> Vamos implementar e gerar uma evidencia dessa interação"

**Artefato gerado pelo Claude Code:**
```markdown
## Melhoria 1 — Trocar modelo de embedding por multilingual
Alterar EMBED_MODEL em dois arquivos:
- EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"

## Melhoria 2 — Adicionar validação de seção em evaluate_retrieval
def evaluate_retrieval(retrieved, expected_sources, expected_sections=None):
    ...
    if expected_sections:
        section_ok = any(es in sec for sec in retrieved_sections for es in expected_sections)
```
*(arquivo completo: `.spec/melhorias-pos-avaliacao.md`)*

**Julgamento técnico aplicado:**
A sugestão inicial de Claude Code incluía 5 melhorias. Após análise, a ordem foi ajustada:
Melhoria 1 (embedding) antes de Melhoria 3 (respostas LLM) porque os prompts submetidos
ao LLM precisam ter sido gerados com o modelo correto para que os resultados sejam válidos
como evidência. Se tivéssemos fechado o ciclo de testes com `all-MiniLM-L6-v2` e depois
trocado o modelo, as evidências estariam inconsistentes com o estado final do pipeline.

---

## Interação 2 — Troca do modelo de embedding (Melhoria 1)

**Contexto:** Claude Code identificou `all-MiniLM-L6-v2` como inadequado para português
e propôs a troca para `paraphrase-multilingual-MiniLM-L12-v2`.

**Prompt submetido:**
> "sim" [confirmando implementação da Melhoria 1]

**Código gerado/modificado pelo Claude Code:**

`pipeline-rag/ingest.py` (linha 11):
```python
# Antes
EMBED_MODEL = "all-MiniLM-L6-v2"

# Depois — gerado pelo Claude Code
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

`pipeline-rag/search.py` (linha 7):
```python
# Antes
EMBED_MODEL = "all-MiniLM-L6-v2"

# Depois — gerado pelo Claude Code
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

**Verificação executada pelo Claude Code:**
```
=== Ingestão NovaTech ===
Total: 39 chunks na coleção 'novatech'
Ingestão concluída.
```

**Julgamento técnico aplicado:**
Claude Code sugeriu apenas a troca da constante `EMBED_MODEL`. Antes de aceitar, foram
avaliados os trade-offs:
- `paraphrase-multilingual-MiniLM-L12-v2` vs `multilingual-e5-large`: o segundo tem
  performance superior em benchmarks PT-BR (MTEB), mas é ~4x maior (~560MB vs ~118MB),
  o que impacta o tempo de ingestão em máquina local sem GPU.
- Para este POC com 39 chunks, `paraphrase-multilingual-MiniLM-L12-v2` é proporcional
  ao escopo — não há necessidade de modelo maior que impactaria o tempo de setup.

---

## Interação 3 — Atualização de `evaluate_retrieval` com validação de seção (Melhoria 2)

**Contexto:** A função `evaluate_retrieval` em `test_pipeline.py` validava apenas o nome
do arquivo fonte, gerando falso-positivo `FULL` para 5/5 testes quando semanticamente 4/5
estavam recuperando seções erradas.

**Prompt submetido:**
> "Antes de implementar Melhoria 2, preciso dos títulos exatos das seções nos docs
> para o match funcionar corretamente."
> [Claude Code executou `python -c "from search import search; ..."` para descobrir
> os nomes reais antes de codar]

**Código gerado pelo Claude Code:**

```python
# Função anterior (validava só fonte)
def evaluate_retrieval(retrieved: list[dict], expected_sources: list[str]) -> str:
    retrieved_sources = {r["metadata"].get("source", "") for r in retrieved}
    matches = [s for s in expected_sources if any(s in rs for rs in retrieved_sources)]
    if len(matches) == len(expected_sources):
        return "full"
    return "partial" if matches else "miss"

# Função gerada pelo Claude Code (valida fonte + seção)
def evaluate_retrieval(
    retrieved: list[dict],
    expected_sources: list[str],
    expected_sections: list[str] | None = None,
) -> str:
    retrieved_sources = {r["metadata"].get("source", "") for r in retrieved}
    retrieved_sections = [r["metadata"].get("section", "") for r in retrieved]

    source_matches = [s for s in expected_sources if any(s in rs for rs in retrieved_sources)]
    source_ok = len(source_matches) == len(expected_sources)

    if expected_sections:
        section_ok = any(
            es in sec
            for sec in retrieved_sections
            for es in expected_sections
        )
    else:
        section_ok = None

    if source_ok and section_ok:
        return "full"
    if source_ok and section_ok is False:
        return "source_only"
    if source_matches:
        return "partial"
    return "miss"
```

**Ajuste feito após a sugestão:**
O retorno `"source_only"` foi adicionado como novo status intermediário — a primeira
versão da função gerada usava apenas `"full"` e `"miss"`. A distinção entre
`source_only` (fonte correta, seção errada) e `partial` (fonte parcialmente correta)
é importante para identificar se o problema é o modelo de embedding (leva à fonte certa
mas não à seção) ou a indexação (não encontra o documento de forma alguma). Esse nível
de granularidade não estava na spec original e foi adicionado com base no diagnóstico
feito no exercício 1.3.

**Resultado com a nova métrica:**
```
Teste 1: [OK] FULL   (POL-001 §3.1 encontrado)
Teste 2: [~] SOURCE_ONLY  (POL-001 encontrado, §3.2 ausente)
Teste 3: [~] SOURCE_ONLY  (SLA-2024 encontrado, §2 ausente)
Teste 4: [OK] FULL   (PROC-042-v2 §2 encontrado)
Teste 5: [OK] FULL   (FAQ Item 15 + SLA Introdução encontrados)
```
A métrica agora expõe honestamente 3/5 FULL (antes reportava 5/5 FULL incorretamente).

---

## Sumário do uso do Claude Code neste projeto

| Interação | Artefato gerado | Julgamento próprio aplicado |
|---|---|---|
| 1 — Diagnóstico + spec | `.spec/melhorias-pos-avaliacao.md` | Reordenação das melhorias por dependência lógica |
| 2 — Embedding multilingual | `ingest.py` + `search.py` linha 11/7 | Escolha do modelo proporcional ao escopo (não o maior) |
| 3 — evaluate_retrieval | `test_pipeline.py` função e TESTS | Adição de status `source_only` não previsto na spec |
| 4 — Ciclo de testes | `test_results.json` + evidências | Avaliação honesta: 2/5 corretos end-to-end, não 3/5 |
