# Skill: TypeScript Conventions

**Nível:** Foundation  
**Ativação:** Leia este arquivo antes de gerar qualquer arquivo `.ts` no projeto.

---

## Contexto

Este projeto usa TypeScript strict em Azure Functions v4. Estas convenções existem porque o Copilot e o Claude Code, sem orientação, geram código que compila mas falha silenciosamente em produção: `console.log` vaza em logs estruturados do Azure, `any` implícito passa na compilação mas quebra inferência, e handlers sem `try/catch` produzem unhandled rejections em runtime.

Toda sessão de geração de código `.ts` deve seguir estas regras sem exceção.

---

## Regras — DEVE

1. **`strict: true` no tsconfig** — sem exceções. Nunca desabilite `strictNullChecks`, `noImplicitAny` ou `strictFunctionTypes`.

2. **Imports absolutos via path alias** — use `@/shared/...`, `@/services/...`. Nunca caminhos relativos com `../../`.

3. **Naming:**
   - `PascalCase` para tipos, interfaces e classes: `QueryRequest`, `ValidationError`
   - `camelCase` para funções e variáveis: `queryHandler`, `sourceDocument`
   - `SCREAMING_SNAKE_CASE` para constantes de configuração: `MAX_QUESTION_LENGTH`, `LOG_LEVEL`

4. **Toda função assíncrona com `try/catch` explícito** — nunca deixe uma `Promise` sem tratamento de erro no nível do handler.

5. **Logger: sempre `pino`** — nunca `console.log`, `console.error`, `console.warn` em qualquer arquivo de `src/`.

---

## Proibições — NÃO DEVE

- `as any` ou `as unknown as X` para contornar tipagem — corrija o tipo ou use `satisfies`
- `require()` dinâmico — use `import` estático ou `await import()` com tipo explícito
- `console.log` / `console.error` em qualquer arquivo de `src/` — use `logger.info`, `logger.warn`, `logger.error`
- Parâmetros de função sem tipo explícito — `function foo(x)` é proibido; use `function foo(x: string)`
- Tipos de retorno implícitos em funções exportadas — declare explicitamente

---

## Exemplos DO / DON'T

### Validação de QueryRequest

**DON'T — gerado pelo Copilot sem esta skill:**
```typescript
// Copilot gera: any implícito, console.log, parse que lança exceção não tratada
export async function handler(req: any) {
  const body = req.body;
  try {
    const data = QueryRequestSchema.parse(body); // lança exceção — não capturada no nível do caller
    console.log('Pergunta recebida:', data.question);
    return { status: 200, body: JSON.stringify({ answer: 'ok' }) };
  } catch (e) {
    console.error(e);
    return { status: 400 };
  }
}
```

**DO — correto para este projeto:**
```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from '@azure/functions';
import { QueryRequestSchema } from '@/functions/query/validator';
import { logger } from '@/shared/logger';

async function queryHandler(request: HttpRequest, _context: InvocationContext): Promise<HttpResponseInit> {
  try {
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return { status: 422, jsonBody: { error: 'Body inválido: esperado JSON.' } };
    }

    const result = QueryRequestSchema.safeParse(body); // safeParse — não lança exceção
    if (!result.success) {
      logger.warn({ issues: result.error.issues }, 'Validação falhou'); // pino, não console
      return { status: 400, jsonBody: { error: 'Requisição inválida.' } };
    }

    logger.info({ question: result.data.question }, 'Query recebida');
    return { status: 200, jsonBody: { answer: 'stub', source_document: 'stub' } };
  } catch (err) {
    logger.error({ err }, 'Erro inesperado');
    return { status: 500, jsonBody: { error: 'Erro interno.' } };
  }
}
```

### Definição de tipos de domínio

**DON'T:**
```typescript
// Copilot gera: interface com any, sem vigencia opcional
interface Chunk {
  id: any;
  content: string;
  metadata: any; // campo genérico que esconde o que realmente importa
}
```

**DO:**
```typescript
export type Chunk = {
  id: string;
  content: string;
  source: string;
  vigencia?: string; // opcional — ADR-0003: documentos contraditórios tratados por metadado
};
```

---

## Anti-padrões comuns do Copilot

1. **`module.exports` em vez de `app.http`** — Copilot usa API v3 do Azure Functions. Este projeto usa v4 com `app.http(...)`.

2. **`console.log` em vez de `pino`** — Copilot não sabe que o projeto tem logger configurado. Sempre substitua.

3. **`QueryRequestSchema.parse(body)` sem `safeParse`** — Copilot usa `parse` que lança `ZodError`. Handlers async precisam de `safeParse` para controlar a resposta HTTP.

4. **Tipos `any` em parâmetros de handler** — Copilot tipifica `req: any` quando não vê a importação de `@azure/functions`. Importe e use `HttpRequest`.

5. **Try/catch ausente no nível assíncrono** — Copilot frequentemente gera `async function handler(...)` sem `try/catch` externo, deixando exceções inesperadas como unhandled rejections.

6. **Imports relativos com `../../../`** — Copilot não conhece os path aliases do tsconfig. Converta para `@/shared/...`.

---

## Dependências

Nenhuma — esta é a skill base. Todas as outras skills de domínio e artefato pressupõem que estas convenções foram lidas.
