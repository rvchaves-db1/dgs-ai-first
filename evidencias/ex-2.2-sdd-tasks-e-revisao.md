# Evidência — Ex 2.2: SDD e Implementação

## 1. Processo SDD seguido

O processo SDD (Spec-Driven Development) foi executado em três etapas encadeadas:

**Step 1 — plan.md:** Copiado do enunciado para `novatech-assistant/specs/query-endpoint/plan.md`. O plan define a abordagem de alto nível (5 passos do pipeline RAG), as decisões técnicas (TypeScript + Azure Functions v4 + Zod + pino), as decisões herdadas do cenário 1 (ADR-0002 e ADR-0003) e as dependências de infraestrutura.

**Step 2 — tasks.md:** O plan foi decomposto em 7 tasks atômicas em `novatech-assistant/specs/query-endpoint/tasks.md`. Cada task tem ID, descrição, critérios de aceite verificáveis, dependências explícitas e tamanho (P/M/G). As tasks foram ordenadas pelo grafo de dependências: TASK-001 sem dependências é o ponto de entrada isolável.

**Step 3 — Implementação da TASK-001:** Com o plan e as tasks como contexto, foram implementados os 5 arquivos da TASK-001:
- `src/shared/types.ts` — tipos de domínio
- `src/shared/errors.ts` — erros customizados
- `src/shared/logger.ts` — instância pino
- `src/functions/query/validator.ts` — schema Zod
- `src/functions/query/handler.ts` — Azure Function HTTP trigger v4

Checkpoint de qualidade após cada step: o plan não evoluiu para tasks enquanto havia ambiguidade nas decisões técnicas; o código não foi escrito enquanto os critérios de aceite não eram verificáveis.

---

## 2. Decisões do breakdown de tasks

**Por que 7 tasks?**

O pipeline RAG tem 5 componentes tecnicamente independentes (embedding, busca, prompt, completion, retry) mais o endpoint setup (TASK-001) e os testes de integração (TASK-007). Cada componente tem um boundary claro: falha, tipos de retorno e dependências externas distintos. Granularidade menor (ex: separar logger em task própria) não acrescentaria paralelismo real; granularidade maior (ex: agrupar embedding + busca) esconderia o ponto de falha Azure AI Search.

**Por que TASK-001 sem dependências é o ponto de entrada?**

TASK-001 é a única task isolável: valida input, retorna stub e não chama nenhum serviço externo. Isso permite:
- Desenvolver e testar o handler sem credenciais Azure configuradas
- Estabelecer o contrato HTTP (`source_document` obrigatório) antes de implementar os serviços
- Usar como fixture nos testes de integração da TASK-007

**Por que TASK-006 (retry) depende de TASK-002 e TASK-005?**

O retry é um cross-cutting concern que precisa conhecer os contratos de erro (`CompletionError`, `SearchError`) definidos nas tasks que fazem as chamadas. Implementar antes geraria uma abstração vazia sem erros reais para testar.

---

## 3. Conexão com o Cenário 1

O protótipo open-source do Exercício 1.3 (Python + ChromaDB + LangChain) validou a abordagem RAG antes de qualquer linha de código de produção. Essa validação antecipou:

- **Pipeline de 5 etapas funciona:** embedding → busca por similaridade → montagem de prompt → completion → resposta com fonte. O mesmo pipeline está codificado no `plan.md`.
- **Context budget é real:** no protótipo, respostas degradaram quando o contexto excedeu ~12K tokens. Isso motivou a ADR-0002 (~4K system + ~8K chunks = teto seguro).
- **Documentos contraditórios precisam de tratamento explícito:** no protótipo, perguntas sobre frete retornavam multipliers do PROC-042-v1 mesmo quando v2 era mais relevante. A ADR-0003 (priorizar por metadado de vigência) foi criada a partir dessa observação.

Agora o mesmo padrão é reimplementado em TypeScript + Azure Functions v4, com os guardrails de produção que o protótipo não tinha: Zod para validação, pino para logging estruturado, retry com backoff e testes com msw.

---

## 4. Revisão crítica do código gerado

### Problema 1: `console.log` em vez de pino

**Trecho gerado pelo Copilot (sem skill de convenções):**
```typescript
export async function queryHandler(req: any) {
  const body = req.body;
  console.log('Pergunta recebida:', body.question); // PROBLEMA
  // ...
}
```

**Por que quebra em produção:** Azure Functions usa Application Insights para logging estruturado. `console.log` não inclui correlation ID, severity level nem JSON estruturado — impossível correlacionar logs de uma requisição específica ou criar alertas por severity. Em produção com volume alto, logs `console` se perdem no ruído.

**Correção aplicada:**
```typescript
import { logger } from '../../shared/logger.js';
// ...
logger.info({ question }, 'Query recebida'); // pino: structured, com level e name
logger.warn({ issues: result.error.issues }, 'Validação de input falhou');
```

---

### Problema 2: `QueryRequestSchema.parse()` sem `safeParse`

**Trecho gerado pelo Copilot:**
```typescript
async function queryHandler(request: HttpRequest): Promise<HttpResponseInit> {
  const body = await request.json();
  const data = QueryRequestSchema.parse(body); // PROBLEMA: lança ZodError não capturado
  return { status: 200, jsonBody: { answer: 'ok', source_document: 'stub' } };
}
```

**Por que quebra em produção:** `parse()` lança `ZodError` quando a validação falha. Sem `try/catch` no nível correto, esse erro se propaga como unhandled rejection e o Azure Functions retorna 500 (erro interno) em vez de 400 (input inválido) — o atendente recebe "Erro interno" sem saber que o problema é o input dele.

**Correção aplicada:**
```typescript
const result = QueryRequestSchema.safeParse(body);
if (!result.success) {
  logger.warn({ issues: result.error.issues }, 'Validação de input falhou');
  return {
    status: 400,
    jsonBody: {
      error: 'Requisição inválida.',
      details: result.error.issues.map((i) => i.message),
    },
  };
}
```

`safeParse` retorna `{ success: false, error: ZodError }` — sem exceção — e permite retornar 400 com as mensagens de erro customizadas em português que o atendente consegue interpretar.
