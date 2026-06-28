# Tasks — Cenário 3: Fase de Governança e Validação

**Participante:** Rafael Chaves — Papel: Desenvolvedor  
**Data:** 2026-06-28  
**Referência da spec:** `.spec/exercicio-3-fase-governanca-spec.md`  
**Critérios de avaliação:** `Correção/cenario-3/avaliacao-desenvolvedor.md`

> Este arquivo quebra a spec em tasks atômicas para a sessão de implementação.
> Cada task tem critérios verificáveis. Seguir a ordem garante que as dependências são respeitadas.

---

## Exercício 3.1 — Structured output e verificações determinísticas

### TASK-HARNESS-001 · Definir schema Zod do structured output

**Tamanho:** P  
**Depende de:** —  
**Path de destino:** `novatech-assistant/src/services/response-validator.ts` (início do arquivo)  
**Ferramenta:** GitHub Copilot

**O que fazer:**  
Criar o schema Zod para o structured output do assistente. O modelo deve responder em JSON com este formato exato — se não responder neste formato, a resposta é rejeitada antes de qualquer verificação de conteúdo.

**Schema alvo:**
```typescript
import { z } from 'zod';

export const AssistantResponseSchema = z.object({
  answer: z.string().min(1, 'Resposta não pode ser vazia'),
  source_document: z.string().min(1, 'Documento fonte é obrigatório'),
  confidence_score: z.number().min(0).max(1),
}).strict(); // não aceitar campos extras

export type AssistantResponse = z.infer<typeof AssistantResponseSchema>;
```

**Aceite (todos devem ser verdadeiros):**
- [ ] Schema exportado com nome exato `AssistantResponseSchema`
- [ ] Tipo exportado como `AssistantResponse`
- [ ] `.strict()` presente (campos extras causam erro de validação)
- [ ] `confidence_score` validado como `z.number()` (não string)
- [ ] Mensagens de erro em português

---

### TASK-HARNESS-002 · Implementar `response-validator.ts` com os 2 guardrails

**Tamanho:** M  
**Depende de:** TASK-HARNESS-001  
**Path de destino:** `novatech-assistant/src/services/response-validator.ts`  
**Ferramenta:** GitHub Copilot

**O que fazer:**  
Implementar a função `validateResponse` que: (1) valida o JSON contra o schema, (2) aplica os 2 guardrails determinísticos. Em qualquer falha, loga o motivo e retorna resposta padrão segura.

**Interface pública:**
```typescript
type ValidatedResult =
  | { valid: true; data: AssistantResponse }
  | { valid: false; reason: 'schema_invalid' | 'missing_source' | 'dangerous_goods_violation'; safeResponse: string }

export function validateResponse(raw: unknown): ValidatedResult
```

**Lógica dos guardrails:**

*Guardrail 1 — source_document obrigatório:*  
Disparado quando `source_document` está ausente ou é string vazia (já coberto pelo schema, mas verificar explicitamente após parse para clareza do log).

*Guardrail 2 — carga perigosa + devolução:*  
Verificar se `answer` (em lowercase) contém `"carga perigosa"` E alguma expressão afirmativa de devolução. Expressões que disparam: `"pode ser devolvida"`, `"é possível devolver"`, `"pode devolver"`, `"devolução disponível"`, `"devolução é possível"`. A presença de `"não"` antes da expressão NÃO deve disparar.

**Mensagem padrão segura (para ambos os guardrails):**
```
"Não foi possível processar esta resposta. Por favor, consulte um supervisor."
```

**Aceite:**
- [ ] Função `validateResponse` exportada com tipo de retorno discriminated union
- [ ] Falha no schema → `reason: 'schema_invalid'` + log via pino
- [ ] `source_document` vazio → `reason: 'missing_source'` + log via pino
- [ ] Guardrail 2 bloqueia (não apenas loga) quando disparado
- [ ] `logger` importado de `../../shared/logger` (nunca `console.log`)
- [ ] Nenhum uso de `any` — `raw: unknown` como input
- [ ] Função retorna `{ valid: false, ... }` em qualquer falha (não lança exceção)

---

### TASK-HARNESS-003 · Code review com Claude + correções

**Tamanho:** M  
**Depende de:** TASK-HARNESS-002  
**Path de destino:** corrigir `novatech-assistant/src/services/response-validator.ts` in-place  
**Ferramenta:** Claude (chat) como co-reviewer

**O que fazer:**  
Com o código do Copilot gerado, usar o Claude para identificar problemas. Depois aplicar as correções no arquivo.

**Problemas prováveis a verificar (a buscar ativamente):**

| Problema | O que checar |
|----------|-------------|
| Schema sem `.strict()` | Campos extras passam silenciosamente? |
| Regex de guardrail 2 incompleto | Cobre "pode devolver"? "é devolvível"? Variações com acento? |
| Guardrail loga mas não bloqueia | A função retorna `{ valid: false }` ou apenas chama `logger.warn`? |
| Tipo de retorno usa `any` | Existe `any` no tipo de retorno da função? |
| `console.log` em vez de pino | Algum `console` remanescente? |
| Input `raw` tipado como `unknown` | Ou foi tipado como `object` / `any`? |

**Processo a documentar na evidência:**
1. Transcrição ou resumo do que o Copilot gerou
2. Prompt enviado ao Claude para revisão
3. Lista de problemas identificados pelo Claude
4. Comparação: o que o Copilot gerou vs o que a revisão encontrou
5. Diff das correções aplicadas

**Aceite:**
- [ ] Ao menos 2 problemas reais identificados (não inventados, não cosméticos)
- [ ] Problemas têm explicação de por que causam risco real (não só "viola a convenção")
- [ ] Correções aplicadas no arquivo — arquivo final não tem os problemas encontrados
- [ ] Distinção clara na evidência: prompt é probabilístico, guardrail no código é determinístico

---

### TASK-HARNESS-004 · Criar evidência Ex 3.1

**Tamanho:** M  
**Depende de:** TASK-HARNESS-003  
**Path de destino:** `dgs-ai-first/evidencias/ex-3.1-structured-output-harness.md`

**O que fazer:**  
Documentar o processo completo do exercício.

**Estrutura do documento:**
```markdown
# Evidência — Ex 3.1: Structured Output e Harness de Código

## 1. Schema Zod — AssistantResponseSchema
(código do schema com justificativa de cada campo)

## 2. Implementação do response-validator.ts
(código final — após revisão e correções)

## 3. Code review com Claude
### 3a. Código gerado pelo Copilot (antes da revisão)
(trecho ou código completo)
### 3b. Problemas identificados
(cada problema com trecho + explicação + risco)
### 3c. Correções aplicadas
(diff ou antes/depois de cada correção)

## 4. Probabilístico vs. determinístico
(parágrafo explicando: o system prompt diz "não devolva carga perigosa" — mas se o modelo 
alucinar, apenas o código pega. Um é soft rule, o outro é hard block.)
```

**Aceite:**
- [ ] Schema documentado com justificativa de `.strict()`
- [ ] Pelo menos 2 problemas com trecho de código original + explicação + correção
- [ ] Seção 4 demonstra entendimento do conceito (não é genérica)

---

## Exercício 3.2 — Revisão crítica de código gerado por IA

### TASK-REVIEW-001 · Revisão própria do feedback-handler problemático

**Tamanho:** M  
**Depende de:** —  
**Path de destino:** rascunho interno / evidência (não modifica nenhum arquivo ainda)  
**Ferramenta:** análise manual (sem Claude neste passo)

**O que fazer:**  
Ler o código problemático fornecido pelo enunciado e fazer a revisão SEM usar o Claude primeiro. Listar cada problema com classificação.

**Código a revisar (do enunciado):**
```typescript
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

**Problemas mínimos obrigatórios (avaliação vai checar estes):**

| # | Problema | Classificação |
|---|----------|---------------|
| 1 | `as any` sem validação Zod | Violação AGENTS.md + bug potencial |
| 2 | `console.log(JSON.stringify(feedback))` — loga `attendantEmail` | Violação AGENTS.md + problema de segurança |
| 3 | `require('@azure/cosmos')` dentro da função | Violação AGENTS.md |
| 4 | `attendantEmail` incluído no log (dado pessoal) | Problema de segurança |

**Problemas adicionais a notar para diferenciar a revisão:**
- Ausência de `try/catch` (unhandled rejection se Cosmos falhar)
- `rating` sem validação de range (aceita qualquer valor)
- `InvocationContext` ausente na assinatura (Azure Functions v4)
- `body: 'OK'` como string (padrão do projeto usa JSON)

**Aceite:**
- [ ] Revisão feita e registrada ANTES de usar o Claude (evidência mostra a sequência)
- [ ] 4 problemas obrigatórios identificados
- [ ] Cada problema tem: trecho de código + classificação + motivo do risco

---

### TASK-REVIEW-002 · Segunda revisão com Claude + comparação

**Tamanho:** P  
**Depende de:** TASK-REVIEW-001  
**Ferramenta:** Claude (chat)

**O que fazer:**  
Usar o Claude como segundo revisor do mesmo código. Comparar com a própria revisão.

**Prompt sugerido para o Claude:**
```
Revise o seguinte código TypeScript para Azure Functions v4.
Contexto: o projeto usa as seguintes regras (AGENTS.md):
- TypeScript strict mode
- Zod para validação de input
- pino para logging (nunca console.log)
- Nunca logar dados pessoais (e-mail, nome)
- Imports estáticos no topo (nunca require dinâmico)

[colar o código]

Liste todos os problemas com classificação: violação do AGENTS.md, problema de segurança, ou bug potencial.
```

**O que documentar na comparação:**
- Problemas que ambos identificaram
- Problemas que só o Claude encontrou (o que eu perdi?)
- Problemas que só eu encontrei (o Claude perdeu?)
- Onde as classificações divergiram

**Aceite:**
- [ ] Prompt ao Claude documentado
- [ ] Comparação honesta (não apenas "concordamos em tudo")
- [ ] Reflexão: o que a revisão humana captura que o Claude pode perder (contexto do domínio, regras não documentadas)

---

### TASK-REVIEW-003 · Reescrever `feedback/handler.ts` com Copilot

**Tamanho:** M  
**Depende de:** TASK-REVIEW-002  
**Path de destino:** `novatech-assistant/src/functions/feedback/handler.ts`  
**Ferramenta:** GitHub Copilot

**O que fazer:**  
Reescrever o módulo do zero, corrigindo todos os problemas identificados.

**Schema Zod a criar (dentro do mesmo arquivo ou em `validator.ts` paralelo):**
```typescript
const FeedbackRequestSchema = z.object({
  queryId: z.string().min(1),
  rating: z.number().int().min(1).max(5),
  comment: z.string().optional(),
  // attendantEmail: NUNCA incluir em logs — pode estar no schema para persistência,
  // mas nunca passa para o objeto logado
});
```

**Estrutura esperada do arquivo reescrito:**
```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';  // import estático no topo
import { z } from 'zod';
import { logger } from '../../shared/logger';  // pino

const FeedbackRequestSchema = z.object({ ... });

export async function feedbackHandler(
  request: HttpRequest,
  context: InvocationContext  // segundo parâmetro obrigatório no v4
): Promise<HttpResponseInit> {
  // safeParse — não lança exceção
  // log SEM attendantEmail
  // try/catch explícito
  // retorno JSON
}

app.http('feedback', {
  methods: ['POST'],
  authLevel: 'anonymous',
  route: 'feedback',
  handler: feedbackHandler,
});
```

**Aceite:**
- [ ] Nenhum `as any` — body validado com `FeedbackRequestSchema.safeParse()`
- [ ] Nenhum `console.log` — usar `logger.info(...)` ou `logger.error(...)`
- [ ] `import { CosmosClient }` no topo (não `require` dentro da função)
- [ ] Nenhum campo pessoal no objeto logado
- [ ] `try/catch` explícito cobrindo a operação do Cosmos
- [ ] Assinatura com `InvocationContext` como segundo parâmetro
- [ ] Retorno com `body: JSON.stringify(...)` (não string literal)
- [ ] Compila sem erros TypeScript strict

---

### TASK-REVIEW-004 · Criar evidência Ex 3.2

**Tamanho:** M  
**Depende de:** TASK-REVIEW-003  
**Path de destino:** `dgs-ai-first/evidencias/ex-3.2-revisao-critica-feedback-handler.md`

**O que fazer:**  
Documentar o processo completo do exercício.

**Estrutura do documento:**
```markdown
# Evidência — Ex 3.2: Revisão Crítica de Código Gerado por IA

## 1. Revisão própria (antes do Claude)
(lista de problemas com classificação e trecho de código)

## 2. Revisão do Claude
(prompt enviado + lista de problemas identificados pelo Claude)

## 3. Comparação
(tabela: problema | encontrei | Claude encontrou | classificação concordou?)

## 4. Reflexão
(o que a revisão humana captura que o Claude pode perder neste contexto)

## 5. Código reescrito
(código final do feedback/handler.ts)
```

**Aceite:**
- [ ] Seção 1 documentada ANTES da seção 2 (sequência preservada)
- [ ] 4 problemas obrigatórios presentes na revisão própria
- [ ] Comparação em tabela (não narrativa genérica)
- [ ] Código final inclui todos os itens do aceite da TASK-REVIEW-003

---

## Ordem de execução recomendada

```
Bloco 1 — Ex 3.1 (Harness de código):
  TASK-HARNESS-001 (schema Zod)           ← sem dependências
  TASK-HARNESS-002 (response-validator)   ← depende de HARNESS-001
  TASK-HARNESS-003 (code review)          ← depende de HARNESS-002
  TASK-HARNESS-004 (evidência)            ← depende de HARNESS-003

Bloco 2 — Ex 3.2 (Revisão crítica):
  TASK-REVIEW-001 (revisão própria)       ← sem dependências, fazer SEM Claude
  TASK-REVIEW-002 (revisão Claude)        ← depende de REVIEW-001
  TASK-REVIEW-003 (reescrita)             ← depende de REVIEW-002
  TASK-REVIEW-004 (evidência)             ← depende de REVIEW-003
```

**Total: 8 tasks**  
Estimativa: Bloco 1 (~45 min), Bloco 2 (~45 min)

---

## Checklist de entregáveis por exercício

### Ex 3.1
- [ ] `novatech-assistant/src/services/response-validator.ts` — schema Zod + guardrails + correções do code review
- [ ] `dgs-ai-first/evidencias/ex-3.1-structured-output-harness.md` — schema, código, review, distinção probabilístico vs. determinístico

### Ex 3.2
- [ ] `novatech-assistant/src/functions/feedback/handler.ts` — módulo reescrito conforme AGENTS.md
- [ ] `dgs-ai-first/evidencias/ex-3.2-revisao-critica-feedback-handler.md` — revisão própria, revisão Claude, comparação, código final
