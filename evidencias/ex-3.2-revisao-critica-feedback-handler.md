# Evidência — Ex 3.2: Revisão Crítica de Código Gerado por IA

**Exercício:** 3.2 — Revisão Crítica de Outputs de IA  
**Papel:** Desenvolvedor  
**Arquivo produzido:** `novatech-assistant/src/functions/feedback/handler.ts`

---

## 1. Revisão própria (antes do Claude)

**Código recebido para revisão:**

```typescript
// feedback-handler.ts — gerado pelo Copilot
import { app, HttpRequest, HttpResponseInit } from '@azure/functions';

export async function feedbackHandler(
  request: HttpRequest
): Promise<HttpResponseInit> {
  const body = await request.json() as any;

  const feedback = {
    queryId: body.queryId,
    rating: body.rating,
    comment: body.comment,
    attendantEmail: body.attendantEmail,
    timestamp: new Date().toISOString()
  };

  console.log('Feedback recebido:', JSON.stringify(feedback));

  const { CosmosClient } = require('@azure/cosmos');
  const client = new CosmosClient(process.env.COSMOS_CONNECTION_STRING);
  const database = client.database('novatech');
  const container = database.container('feedbacks');

  await container.items.create(feedback);

  return { status: 200, body: 'OK' };
}

app.http('feedback', {
  methods: ['POST'],
  handler: feedbackHandler
});
```

**Problemas identificados (sem uso de IA):**

| # | Problema | Trecho | Classificação |
|---|----------|--------|---------------|
| 1 | `as any` sem validação Zod — `body` é tratado como tipado mas não foi validado | `const body = await request.json() as any` | Violação AGENTS.md + bug potencial |
| 2 | `console.log` em vez de pino | `console.log('Feedback recebido:', ...)` | Violação AGENTS.md |
| 3 | `attendantEmail` incluído no objeto `feedback` que é logado integralmente | `JSON.stringify(feedback)` com `attendantEmail` dentro | Violação AGENTS.md + problema de segurança |
| 4 | `require('@azure/cosmos')` dinâmico dentro da função | `const { CosmosClient } = require(...)` | Violação AGENTS.md |
| 5 | Sem `try/catch` — `container.items.create(feedback)` pode lançar sem tratamento | `await container.items.create(feedback)` | Bug potencial (unhandled rejection) |
| 6 | `rating` sem validação de range — aceita qualquer valor, incluindo strings e negativos | `rating: body.rating` | Bug potencial |
| 7 | `InvocationContext` ausente na assinatura — Azure Functions v4 requer o segundo parâmetro | `feedbackHandler(request: HttpRequest)` | Violação da API do framework |
| 8 | `body: 'OK'` como string — padrão do projeto usa JSON com Content-Type | `return { status: 200, body: 'OK' }` | Inconsistência com padrão do projeto |

---

## 2. Revisão do Claude

**Prompt enviado:**

```
Revise o seguinte código TypeScript para Azure Functions v4.
O projeto segue estas regras (AGENTS.md):
- TypeScript strict mode
- Zod para validação de input (nunca as any)
- pino para logging (nunca console.log)
- Nunca logar dados pessoais (e-mail, nome)
- Imports estáticos no topo (nunca require dinâmico)

Liste todos os problemas com classificação: violação do AGENTS.md, 
problema de segurança, ou bug potencial.

[código colado]
```

**Problemas identificados pelo Claude:**

1. **`as any` sem validação Zod** — Violação AGENTS.md. O body não é validado antes do uso. Campos obrigatórios como `queryId` e `rating` podem estar ausentes ou ter tipo errado sem nenhum erro ser lançado.

2. **`console.log` em vez de pino** — Violação AGENTS.md. O pino foi definido como logger padrão do projeto para permitir saída estruturada e configuração de nível via env.

3. **Dado pessoal (`attendantEmail`) no log** — Problema de segurança. O `JSON.stringify(feedback)` inclui o email do atendente, violando a regra de não logar dados pessoais. Isso pode expor informações em sistemas de log centralizados.

4. **`require` dinâmico** — Violação AGENTS.md. O `require('@azure/cosmos')` dentro da função viola a regra de imports estáticos. Além de ser mais lento (o módulo é carregado a cada invocação), impede tree-shaking e dificulta análise estática.

5. **Ausência de `try/catch`** — Bug potencial. Se o Cosmos DB estiver indisponível ou lançar um erro, a promise é rejeitada sem tratamento, resultando em um erro 500 não controlado sem log de diagnóstico.

6. **`InvocationContext` ausente** — O segundo parâmetro é obrigatório na assinatura do Azure Functions v4. Sem ele, o runtime pode não passar o contexto corretamente em cenários mais complexos.

7. **Retorno `body: 'OK'` como string** — O padrão do projeto retorna JSON. O Content-Type deveria ser `application/json`.

---

## 3. Comparação: revisão própria vs. revisão do Claude

| Problema | Encontrei | Claude encontrou | Classificação concordou? |
|----------|:---------:|:----------------:|:------------------------:|
| `as any` sem Zod | ✅ | ✅ | ✅ Sim |
| `console.log` em vez de pino | ✅ | ✅ | ✅ Sim |
| `attendantEmail` logado | ✅ | ✅ | ✅ Sim |
| `require` dinâmico | ✅ | ✅ | ✅ Sim |
| Sem `try/catch` | ✅ | ✅ | ✅ Sim |
| `rating` sem validação de range | ✅ | ❌ | — (Claude não identificou explicitamente) |
| `InvocationContext` ausente | ✅ | ✅ | ✅ Sim |
| `body: 'OK'` como string | ✅ | ✅ | ✅ Sim |

**Observações:**
- A revisão própria capturou o problema de `rating` sem validação de range (aceita `rating: "cinco"`, `rating: -1`, `rating: 999`) — o Claude focou nos problemas mais óbvios e não aprofundou nas validações de campo.
- O Claude organizou os problemas com boa clareza técnica e destacou o impacto do `as any` em termos de type safety em tempo de execução.
- Ambos concordaram nos 4 problemas obrigatórios da avaliação e em outros adicionais relevantes.

---

## 4. Reflexão

A revisão humana capturou o problema de `rating` sem range porque ao ler o domínio (formulário de satisfação de 1 a 5) é imediato perceber que `body.rating` pode receber qualquer valor. O Claude, sem o contexto implícito do domínio, focou nas violações mais explícitas do AGENTS.md.

Esse padrão se repete: a IA é eficiente em identificar violações de convenção (o que está explícito nas regras), mas a revisão humana captura melhor os problemas de negócio (o que deveria ser validado mesmo que não esteja na regra). Os dois se complementam: a IA não substitui o revisor humano, ela atua como primeiro filtro para não desperdiçar tempo em problemas óbvios.

---

## 5. Código reescrito — `feedback/handler.ts`

```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import { z } from 'zod';
import { logger } from '../../shared/logger';

const FeedbackRequestSchema = z.object({
  queryId: z.string().min(1, 'queryId é obrigatório'),
  rating: z.number().int().min(1).max(5, 'rating deve ser entre 1 e 5'),
  comment: z.string().optional(),
  attendantEmail: z.string().email('e-mail inválido').optional(),
});

type FeedbackRequest = z.infer<typeof FeedbackRequestSchema>;

const cosmosClient = new CosmosClient(process.env.COSMOS_CONNECTION_STRING ?? '');
const container = cosmosClient.database('novatech').container('feedbacks');

export async function feedbackHandler(
  request: HttpRequest,
  _context: InvocationContext,
): Promise<HttpResponseInit> {
  const body = await request.json().catch(() => null);
  const parsed = FeedbackRequestSchema.safeParse(body);

  if (!parsed.success) {
    logger.warn({ issues: parsed.error.issues }, 'feedback: input inválido');
    return {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Input inválido', details: parsed.error.issues }),
    };
  }

  // Separar dado pessoal antes de qualquer log
  const { attendantEmail, ...safeFields } = parsed.data;

  try {
    await container.items.create({
      ...parsed.data,
      timestamp: new Date().toISOString(),
    });

    logger.info(
      { queryId: safeFields.queryId, rating: safeFields.rating },
      'feedback: registrado com sucesso',
    );

    return {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ok: true }),
    };
  } catch (err) {
    logger.error(
      { err, queryId: safeFields.queryId },
      'feedback: falha ao salvar no Cosmos DB',
    );
    return {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Erro interno ao registrar feedback' }),
    };
  }
}

app.http('feedback', {
  methods: ['POST'],
  authLevel: 'anonymous',
  route: 'feedback',
  handler: feedbackHandler,
});
```

**Checklist de correções aplicadas:**

- [x] `as any` substituído por `FeedbackRequestSchema.safeParse()` com retorno 400 em caso de falha
- [x] `console.log` substituído por `logger.info` / `logger.warn` / `logger.error` (pino)
- [x] `attendantEmail` separado via destructuring antes de qualquer log (`safeFields` não inclui o campo)
- [x] `require` dinâmico substituído por `import { CosmosClient } from '@azure/cosmos'` no topo
- [x] `try/catch` explícito cobrindo a operação do Cosmos, com log de erro e retorno 500 controlado
- [x] `rating` validado com `z.number().int().min(1).max(5)`
- [x] `InvocationContext` presente como segundo parâmetro na assinatura
- [x] Retorno com `body: JSON.stringify(...)` e `Content-Type: application/json`
- [x] `CosmosClient` instanciado fora da função (singleton por invocação fria, não por request)
