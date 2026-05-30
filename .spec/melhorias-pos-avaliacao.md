# Spec de Melhorias — Pós-Avaliação Automática
**Papel:** Desenvolvedor | **Cenário 1** | Data: 2026-05-30

> Gerado a partir da auto-avaliação usando `cenario-1-prompt-avaliacao.md` +
> `cenario-1-avaliacao-foundation.md` + `cenario-1-avaliacao-desenvolvedor.md`.
> Cada melhoria referencia a dimensão e critério do rubric impactados.

---

## Resultado atual da avaliação

| Exercício | D1 | D2 | D3 | D4 | D5 | Média | Classificação |
|---|---|---|---|---|---|---|---|
| 1.1 | 3 | 3 | 3 | 3 | 3 | **3.0** | Aprovado com Distinção |
| 1.2 | 3 | 3 | 3 | 3 | 3 | **3.0** | Aprovado com Distinção |
| 1.3 | 2 | 2 | 2 | 3 | 3 | **2.4** | Aprovado |

**Gaps concentrados no Exercício 1.3.** As melhorias abaixo visam elevar o 1.3 para Aprovado com Distinção.

---

## Melhoria 1 — Trocar modelo de embedding por multilingual

**Dimensão impactada:** D1 (Domínio Conceitual) e D3 (Qualidade do Entregável)
**Critério do rubric:** "5 testes com gabarito. Ao menos 3/5 corretos."
**Problema:** `all-MiniLM-L6-v2` é treinado principalmente em inglês. Para perguntas em
português, prioriza overlap léxico em vez de similaridade semântica. Resultado: 4/5 testes
retornaram a fonte correta mas a seção errada — o LLM recebe contexto incompleto.

### O que implementar

Alterar `EMBED_MODEL` em dois arquivos:

**`pipeline-rag/ingest.py`**
```python
# Antes
EMBED_MODEL = "all-MiniLM-L6-v2"

# Depois
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

**`pipeline-rag/search.py`**
```python
# Antes
EMBED_MODEL = "all-MiniLM-L6-v2"

# Depois
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
```

Após a troca: limpar o ChromaDB (`chroma_db/`) e re-executar `ingest.py` para re-indexar
com os novos embeddings.

### Evidência a gerar
- Registro do before/after dos scores de similarity para os 5 testes
- Comparação de quais seções foram recuperadas antes e depois da troca
- Documentar em `evidencias/ex-1.3-melhoria-embedding.md`

---

## Melhoria 2 — Adicionar validação de seção em `evaluate_retrieval`

**Dimensão impactada:** D3 (Qualidade do Entregável)
**Critério do rubric:** "Problemas reais derivados dos testes."
**Problema:** `evaluate_retrieval` retornava `FULL` para 5/5 testes validando apenas o nome
do arquivo fonte. 4/5 testes trouxeram seções erradas dentro do arquivo correto —
métrica enganosa que mascarava qualidade real do retrieval.

### O que implementar

**`pipeline-rag/test_pipeline.py`** — atualizar a função `evaluate_retrieval` e os
test cases para incluir `expected_sections`:

```python
def evaluate_retrieval(retrieved, expected_sources, expected_sections=None):
    sources_found = [r["metadata"].get("source", "") for r in retrieved]
    source_match = all(es in sources_found for es in expected_sources)

    section_match = None
    if expected_sections:
        sections_found = [r["metadata"].get("section", "") for r in retrieved]
        section_match = any(
            es in sf
            for sf in sections_found
            for es in expected_sections
        )

    if source_match and section_match:
        return "FULL"
    elif source_match and section_match is False:
        return "SOURCE_ONLY"
    elif source_match and section_match is None:
        return "SOURCE_ONLY (seção não validada)"
    else:
        return "MISS"
```

Atualizar os 5 test cases para incluir `expected_sections` conforme o gabarito
(Anexo B do enunciado 1.3):

| Teste | `expected_sources` | `expected_sections` |
|---|---|---|
| 1 | `["POL-001"]` | `["3.1", "3.2"]` |
| 2 | `["POL-001"]` | `["3.2"]` |
| 3 | `["SLA-2024"]` | `["2"]` |
| 4 | `["PROC-042-v2"]` | `["2", "2.1"]` |
| 5 | `["SLA-2024", "FAQ"]` | `["1", "FAQ-15"]` |

### Evidência a gerar
- Output do `test_pipeline.py` mostrando `SOURCE_ONLY` nos testes onde antes aparecia `FULL`
- Confirma honestidade da métrica
- Documentar resultado na tabela de sumário de `resultados-testes.md`

---

## Melhoria 3 — Fechar o ciclo de testes com respostas do LLM

**Dimensão impactada:** D3 (Qualidade do Entregável)
**Critério do rubric:** "Pergunta → chunks recuperados → comparação com Anexo B. Ao menos 3/5 corretos."
**Problema:** `test_results.json` foi preparado com os prompts mas sem as respostas do Claude
documentadas. O ciclo ingestão → busca → prompt → resposta → avaliação não está fechado.

### O que implementar

Para cada um dos 5 prompts gerados pelo `test_pipeline.py`:
1. Submeter o prompt ao Claude (nova conversa, sem contexto adicional)
2. Registrar a resposta literal
3. Avaliar: a resposta está correta? Citou a fonte? Cometeu alucinação? Seguiu as regras do system prompt v2?

Critérios de avaliação por resposta (baseados no system prompt v2 do 1.2):
- Citou fonte no formato `[Fonte: NOME-DOC, seção X.X]`? S/N
- Apresentou restrições com "ATENÇÃO:" quando aplicável? S/N
- Inventou valor, prazo ou procedimento não presente no chunk? S/N
- Para tier inexistente (Platinum): respondeu "não encontrado" sem alucinar? S/N

### Evidência a gerar
- Arquivo `evidencias/ex-1.3-respostas-llm.md` com:
  - Prompt submetido (completo, como gerado pelo pipeline)
  - Resposta literal do Claude
  - Avaliação linha a linha
  - Gabarito (resposta esperada segundo Anexo B)
  - Veredito: Correto / Parcial / Incorreto
- Tabela final: N/5 corretos após a melhoria 1 (multilingual)

---

## Melhoria 4 — Adicionar evidência de uso do Claude Code

**Dimensão impactada:** D2 (Uso de Ferramentas)
**Critério do rubric:** "Copilot evidenciado — Prompts/completions do Copilot na geração do código."
**Problema:** `ex-1.3-claude-code/README.md` declara que Claude Code foi usado mas não fornece
trechos rastreáveis. Evidência declaratória não substitui evidência demonstrada.

### O que implementar

Adicionar ao `evidencias/ex-1.3-claude-code/README.md` pelo menos 2 exemplos concretos:

**Formato de cada exemplo:**
```
### Interação [N] — [Descrição do que foi gerado]

**Prompt submetido ao Claude Code:**
> [texto exato do prompt]

**Trecho de código gerado/sugerido:**
```python
[código]
```

**Ajuste feito após a sugestão:**
[descreve o que foi aceito, rejeitado ou modificado e por quê]
```

Exemplos a documentar (escolher os mais representativos da sessão):
- Geração da lógica de chunking semântico por headers Markdown em `ingest.py`
- Geração da lógica de deduplicação PROC-042 v1/v2 em `search.py`
- Qualquer caso onde a sugestão do Claude Code estava errada e foi corrigida (demonstra julgamento técnico — D4)

### Evidência a gerar
- `evidencias/ex-1.3-claude-code/README.md` atualizado com as interações
- Pelo menos 1 caso de ajuste pós-sugestão (demonstra que não foi delegação cega)

---

## Melhoria 5 — Adicionar regra de conflito de versões ao system prompt v2

**Dimensão impactada:** D1 e D3 do 1.2 (já em 3.0, melhoria incremental)
**Critério do rubric:** "System prompt específico — regras + instruções para chunks."
**Problema:** A contradição PROC-042 v1/v2 foi identificada no 1.1 e tratada no pipeline (1.3),
mas o system prompt v2 do 1.2 não inclui instrução explícita para o LLM sobre como agir
quando dois chunks de versões diferentes aparecerem no contexto.

### O que implementar

Adicionar ao system prompt v2 (em `.spec/exercicio-1.2-prototipacao-system-prompt.md`)
uma nova regra após a Regra 7 atual:

```
8. Se os chunks fornecidos incluírem versões diferentes do mesmo documento,
   priorize sempre o de data mais recente. Informe ao atendente que existe
   uma versão anterior e que a informação pode ter mudado.
   Exemplo: "Conforme PROC-042 v2 (nov/2023) [Fonte: PROC-042-v2, seção 2.1].
   Nota: existe versão anterior (v1) com valores diferentes."
```

### Evidência a gerar
- Diff do system prompt v2 mostrando a regra adicionada
- Teste adicional em `evidencias/ex-1.2-testes-v1-v2.md`:
  - Pergunta: "Qual o multiplicador para Norte?"
  - Chunks injetados: PROC-042-v1 §2.1 + PROC-042-v2 §2.1 (ambas as versões)
  - Resposta esperada: v2 (1.8), com nota sobre v1 (1.6)

---

## Ordem de execução sugerida

```
Melhoria 1 → Melhoria 2 → re-rodar test_pipeline.py → Melhoria 3 → Melhoria 4 → Melhoria 5
```

A ordem importa: executar 1 e 2 antes de 3 garante que os prompts submetidos ao Claude
no ciclo de testes já usam o modelo multilingual correto e a métrica honesta.

---

## Score esperado após as melhorias

| Exercício | D1 | D2 | D3 | D4 | D5 | Média esperada |
|---|---|---|---|---|---|---|
| 1.1 | 3 | 3 | 3 | 3 | 3 | **3.0** |
| 1.2 | 3 | 3 | 3 | 3 | 3 | **3.0** |
| 1.3 | 3 | 3 | 3 | 3 | 3 | **3.0** |

Melhoria 1 eleva D1 (1.3): demonstra que a escolha de modelo multilingual era conhecida
e não ignorada — gap de design corrigido.
Melhorias 2+3 elevam D3 (1.3): ciclo de testes fechado com métrica honesta e ≥3/5 corretos.
Melhoria 4 eleva D2 (1.3): evidência rastreável do assistente de código.
