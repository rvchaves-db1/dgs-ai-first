# Tasks — Query Endpoint

Derivado de: `specs/query-endpoint/plan.md`

| ID | Descrição | Tamanho | Depende de |
|----|-----------|---------|------------|
| TASK-001 | Setup do endpoint: handler + validação Zod do input | P | — |
| TASK-002 | Embedding da pergunta via Azure OpenAI | M | TASK-001 |
| TASK-003 | Busca top-5 chunks no Azure AI Search | M | TASK-002 |
| TASK-004 | Montagem do prompt com context budget (ADR-0002) | M | TASK-003 |
| TASK-005 | Chamada ao GPT-4o + resposta com `source_document` | M | TASK-004 |
| TASK-006 | Retry com exponential backoff para chamadas Azure | P | TASK-002, TASK-005 |
| TASK-007 | Testes de integração (Vitest + msw + fixtures) | G | TASK-001–005 |

---

## TASK-001 — Setup do endpoint: handler + validação Zod do input

**Tamanho:** P  
**Depende de:** —  
**Arquivos:**  
- `src/functions/query/handler.ts`  
- `src/functions/query/validator.ts`  
- `src/shared/types.ts`  
- `src/shared/errors.ts`  
- `src/shared/logger.ts`

**Critérios de aceite:**
- [ ] `POST /api/query` sem campo `question` → 400
- [ ] `POST /api/query` com string vazia ou só espaços → 400
- [ ] `POST /api/query` com `question` > 2.000 chars → 400
- [ ] Body não-JSON → 422
- [ ] `question` válida → 200 com stub incluindo campo `source_document`
- [ ] Erros logados via pino (`logger.warn` / `logger.error`) — nunca `console.log`
- [ ] Schema Zod exportado separadamente (`export const QueryRequestSchema`) — reutilizável nos testes
- [ ] Handler em `src/functions/query/handler.ts` (path exato conforme Anexo C)
- [ ] Azure Functions v4 (`app.http(...)`, não `module.exports`)
- [ ] Validação via `safeParse` (não `parse` que lança exceção)
- [ ] `try/catch` explícito na função async
- [ ] Comentário referenciando ADR-0002 na área do context budget

---

## TASK-002 — Embedding da pergunta via Azure OpenAI

**Tamanho:** M  
**Depende de:** TASK-001  
**Arquivos:** `src/services/completion.ts` (seção de embedding)

**Critérios de aceite:**
- [ ] Chama `POST /openai/deployments/{model}/embeddings` com a pergunta
- [ ] Retorna vetor `number[]` de dimensão compatível com o índice do Azure AI Search
- [ ] Erros de API (`4xx`, `5xx`) lançam `CompletionError` com mensagem descritiva
- [ ] Credenciais lidas exclusivamente de variáveis de ambiente (`AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_KEY`)
- [ ] Sem valores hardcoded de endpoint ou chave

---

## TASK-003 — Busca top-5 chunks no Azure AI Search

**Tamanho:** M  
**Depende de:** TASK-002  
**Arquivos:** `src/services/search.ts`

**Critérios de aceite:**
- [ ] Chama Azure AI Search com vetor retornado pela TASK-002
- [ ] Retorna array de `Chunk[]` com no máximo 5 itens (top-5 por score)
- [ ] Cada `Chunk` tem `id`, `content`, `source` e `vigencia` (opcional)
- [ ] Erros de API lançam `SearchError` com mensagem descritiva
- [ ] Resultado vazio (`[]`) não lança erro — retorna array vazio

---

## TASK-004 — Montagem do prompt com context budget (ADR-0002)

**Tamanho:** M  
**Depende de:** TASK-003  
**Arquivos:** `src/services/prompt-builder.ts`

**Critérios de aceite:**
- [ ] Lê system prompt de `/prompts/system-prompt.md`
- [ ] Trunca chunks para respeitar orçamento de ~8K tokens (ADR-0002)
- [ ] Quando dois chunks de fontes contraditórias são recuperados, inclui ambos e indica vigência (ADR-0003)
- [ ] Retorna string de prompt pronta para envio ao GPT-4o
- [ ] Testa limites de truncagem com fixture de chunks que excedem o budget

---

## TASK-005 — Chamada ao GPT-4o + resposta com `source_document`

**Tamanho:** M  
**Depende de:** TASK-004  
**Arquivos:** `src/functions/query/handler.ts` (integração), `src/services/completion.ts` (chat)

**Critérios de aceite:**
- [ ] Chama `POST /openai/deployments/gpt-4o/chat/completions` com o prompt montado
- [ ] Resposta inclui campo `source_document` com o `source` do chunk de maior relevância
- [ ] Resposta tipada como `QueryResponse` (de `src/shared/types.ts`)
- [ ] Erros de API lançam `CompletionError`
- [ ] `confidence` opcional retornado quando o modelo reportar logprobs

---

## TASK-006 — Retry com exponential backoff para chamadas Azure

**Tamanho:** P  
**Depende de:** TASK-002, TASK-005  
**Arquivos:** utilitário em `src/shared/`

**Critérios de aceite:**
- [ ] Máximo de 3 tentativas com backoff de 1s, 2s, 4s
- [ ] Apenas erros `5xx` e `429` (rate limit) são retentados — erros `4xx` não
- [ ] Após esgotar tentativas lança o erro original (`SearchError` ou `CompletionError`)
- [ ] Testável unitariamente com mock de clock (sem `setTimeout` real nos testes)

---

## TASK-007 — Testes de integração (Vitest + msw + fixtures)

**Tamanho:** G  
**Depende de:** TASK-001–005  
**Arquivos:** `tests/` (diretório de integração)

**Critérios de aceite:**
- [ ] Usa `msw` para interceptar chamadas HTTP às APIs Azure (sem chamadas reais)
- [ ] Usa fixtures de `tests/fixtures/` (chunks.ts, queries.ts, expected-responses.ts)
- [ ] Cobre: 400 por input inválido, 422 por body não-JSON, 200 com `source_document` correto
- [ ] Cobre: falha na busca → 500 com log de erro
- [ ] Cobre: chunk de PROC-042-v2 sobrepõe PROC-042-v1 quando ambos recuperados
- [ ] Cobertura de linhas ≥ 80% no módulo `src/functions/query/`
- [ ] Testes rodam sem variáveis de ambiente reais configuradas
