# Tasks — Cenário 2: Fase de Estruturação

**Participante:** Rafael Chaves — Papel: Desenvolvedor  
**Data:** 2026-06-14  
**Referência da spec:** `.spec/exercicio-2-fase-estruturacao-spec.md`  
**Critérios de avaliação:** `Correção/cenario-2/avaliacao-desenvolvedor.md`

> Este arquivo quebra a spec em tasks atômicas para a sessão de implementação.
> Cada task tem critérios verificáveis. Seguir a ordem garante que as dependências são respeitadas.

---

## Exercício 2.1 — MCP Configuration

### TASK-MCP-001 · Preencher `.mcp/mcp.json` com least privilege

**Tamanho:** P  
**Depende de:** —  
**Path de destino:** `novatech-assistant/.mcp/mcp.json`

**O que fazer:**  
Preencher o arquivo vazio (atualmente `{"mcpServers": {}}`) com 5 servers, aplicando least privilege.

**Estrutura alvo:**
```json
{
  "mcpServers": {
    "filesystem-rw": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "./src", "./specs", "./skills"]
    },
    "filesystem-ro": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "--readonly", "./docs/novatech", "./data/retrieval-corpus"]
    },
    "git": {
      "command": "uvx",
      "args": ["mcp-server-git", "--repository", "."]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "everything": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-everything"]
    }
  }
}
```

**Aceite (todos devem ser verdadeiros):**
- [ ] JSON sintaticamente válido
- [ ] 5 servers presentes: `filesystem-rw`, `filesystem-ro`, `git`, `memory`, `everything`
- [ ] `filesystem-rw` tem escopo `./src ./specs ./skills` — nunca `./`
- [ ] `filesystem-ro` tem escopo `./docs/novatech ./data/retrieval-corpus` e flag `--readonly`
- [ ] Escopo raiz (`./`) ausente em qualquer server

---

### TASK-MCP-002 · Criar evidência de uso real dos MCP servers

**Tamanho:** M  
**Depende de:** TASK-MCP-001  
**Path de destino:** `dgs-ai-first/evidencias/ex-2.1-mcp-configuracao.md`

**O que fazer:**  
Criar o documento de evidência com 4 seções: mapeamento, mcp.json final, evidência de execução, e análise de riscos.

**Estrutura do documento:**

```markdown
# Evidência — Ex 2.1: Configuração de MCP Servers

## 1. Mapeamento necessidade → server
(tabela: Necessidade | Server | Tools/Resources expostos | Escopo | Acesso)

## 2. `.mcp/mcp.json` final
(conteúdo do arquivo)

## 3. Evidência de uso real
### 3a. Agente lê doc NovaTech via filesystem-ro
### 3b. Agente recupera chunk via filesystem-ro (coerente com Anexo B)
### 3c. Agente lê histórico do repo via git

## 4. Análise de riscos
(tabela: Risco | Impacto | Mitigação — mínimo 3 riscos)
```

**Aceite:**
- [ ] Mapeamento cobre todas as 5 necessidades do projeto
- [ ] Cada server tem justificativa de escopo
- [ ] Evidência 3a: agente lista/lê arquivo de `docs/novatech/` (ex: `POL-001`)
- [ ] Evidência 3b: chunk recuperado é coerente com o mapa do Anexo B (ex: pergunta sobre devolução → chunk POL-001-A ou POL-001-B)
- [ ] Evidência 3c: agente lê ao menos 1 commit via server git
- [ ] Mínimo 3 riscos com impacto e mitigação acionável (não genérica)
- [ ] Riscos mencionam: escopo amplo exposindo `.env`, escrita habilitada em fontes de negócio

---

## Exercício 2.2 — SDD: plan → tasks → código

### TASK-SDD-001 · Copiar `plan.md` do enunciado para o starter repo

**Tamanho:** P  
**Depende de:** —  
**Path de destino:** `novatech-assistant/specs/query-endpoint/plan.md`

**O que fazer:**  
O arquivo está vazio. Copiar o conteúdo do plan.md fornecido no enunciado do exercício (disponível em `dgs-ai-first/instrucoes/exercicio-2-fase-estruturacao.md`, seção Exercício 2.2, bloco de código do plan.md simulado).

**Aceite:**
- [ ] Arquivo não está mais vazio
- [ ] Contém seções: Approach, Technical Decisions, Prior Decisions, Dependencies
- [ ] Menciona ADR-0002 (context budget) e ADR-0003 (documentos contraditórios)

---

### TASK-SDD-002 · Criar `tasks.md` com tasks atômicas do query endpoint

**Tamanho:** M  
**Depende de:** TASK-SDD-001  
**Path de destino:** `novatech-assistant/specs/query-endpoint/tasks.md`

**O que fazer:**  
Converter o `plan.md` em tasks atômicas. Cada task deve ter: ID, descrição, critérios de aceite verificáveis, dependências, tamanho P/M/G.

**Tasks a incluir no arquivo:**

| ID | Descrição | Tamanho | Depende de |
|----|-----------|---------|-----------|
| TASK-001 | Setup do endpoint: handler + validação Zod do input | P | — |
| TASK-002 | Embedding da pergunta via Azure OpenAI | M | TASK-001 |
| TASK-003 | Busca top-5 chunks no Azure AI Search | M | TASK-002 |
| TASK-004 | Montagem do prompt com context budget (ADR-0002) | M | TASK-003 |
| TASK-005 | Chamada ao GPT-4o + resposta com `source_document` | M | TASK-004 |
| TASK-006 | Retry com exponential backoff para chamadas Azure | P | TASK-002, TASK-005 |
| TASK-007 | Testes de integração (Vitest + msw + fixtures) | G | TASK-001–005 |

**Para cada task incluir os critérios de aceite — exemplo para TASK-001:**
- `POST /api/query` sem campo `question` → 400
- `POST /api/query` com string vazia/apenas espaços → 400
- `POST /api/query` com `question` > 2.000 chars → 400
- Body não-JSON → 422
- `question` válida → 200 com stub incluindo campo `source_document`
- Erros logados via pino (nunca `console.log`)
- Schema Zod exportado separadamente (reutilizável nos testes)
- Handler em `src/functions/query/handler.ts`

**Aceite do TASK-SDD-002:**
- [ ] 7 tasks no arquivo
- [ ] Cada task tem ID, descrição, critérios de aceite, dependências, tamanho
- [ ] Critérios de aceite são verificáveis (não vagos como "funcionar corretamente")
- [ ] Dependências formam grafo sem ciclos (TASK-001 sem dependências é o ponto de entrada)

---

### TASK-SDD-003 · Implementar `src/shared/types.ts`

**Tamanho:** P  
**Depende de:** TASK-SDD-001  
**Path de destino:** `novatech-assistant/src/shared/types.ts`

**O que fazer:**  
Definir os tipos de domínio do query endpoint. O arquivo já existe como scaffold vazio.

**Tipos a implementar:**
```typescript
// QueryRequest: { question: string }
// QueryResponse: { answer: string; source_document: string; confidence?: number }
// Chunk: { id: string; content: string; source: string; vigencia?: string }
```

**Aceite:**
- [ ] TypeScript strict (sem `any` implícito)
- [ ] `QueryResponse` tem campo `source_document` obrigatório (critério de aceite do exercício 2.3 do PS)
- [ ] `Chunk` tem campo `vigencia` opcional (derivado da ADR-0003)
- [ ] Exports nomeados (não default)

---

### TASK-SDD-004 · Implementar `src/shared/errors.ts`

**Tamanho:** P  
**Depende de:** TASK-SDD-003  
**Path de destino:** `novatech-assistant/src/shared/errors.ts`

**O que fazer:**  
Definir erros customizados do domínio.

**Erros a implementar:**
```typescript
// ValidationError extends Error — para erros de input (Zod failures)
// SearchError extends Error — para falhas no Azure AI Search
// CompletionError extends Error — para falhas no Azure OpenAI
```

**Aceite:**
- [ ] Classes que estendem `Error` (não apenas strings/enums)
- [ ] Cada classe tem `name` explícito (para logging estruturado)
- [ ] `ValidationError` inclui campo para os detalhes do Zod (ex: `issues`)

---

### TASK-SDD-005 · Implementar `src/shared/logger.ts`

**Tamanho:** P  
**Depende de:** —  
**Path de destino:** `novatech-assistant/src/shared/logger.ts`

**O que fazer:**  
Exportar instância configurada do pino. O arquivo já existe como scaffold vazio.

**Aceite:**
- [ ] Usa `pino` (nunca `console.log`)
- [ ] Logger tem `name: 'novatech-assistant'` ou similar
- [ ] Level configurável via env var (`process.env.LOG_LEVEL ?? 'info'`)
- [ ] Exportação nomeada: `export const logger`

---

### TASK-SDD-006 · Implementar `src/functions/query/validator.ts`

**Tamanho:** P  
**Depende de:** TASK-SDD-003  
**Path de destino:** `novatech-assistant/src/functions/query/validator.ts`

**O que fazer:**  
Schema Zod para validar o body do POST /api/query.

**Schema a implementar:**
```typescript
// QueryRequestSchema: z.object({ question: z.string().min(1).max(2000).trim() })
// Mensagens de erro customizadas em português (para o atendente entender)
// Exportar schema separadamente para reuso nos testes
```

**Aceite:**
- [ ] Rejeita string vazia (`min(1)` + `.trim()`)
- [ ] Rejeita acima de 2.000 chars (`max(2000)`)
- [ ] Mensagens de erro em português (não o default do Zod em inglês)
- [ ] Schema e tipo exportados separadamente: `export const QueryRequestSchema`, `export type QueryRequest`

---

### TASK-SDD-007 · Implementar `src/functions/query/handler.ts`

**Tamanho:** M  
**Depende de:** TASK-SDD-005, TASK-SDD-006  
**Path de destino:** `novatech-assistant/src/functions/query/handler.ts`

**O que fazer:**  
Azure Function HTTP trigger v4 que valida input e retorna stub de resposta.

**Esqueleto obrigatório:**
```typescript
import { app, HttpRequest, HttpResponseInit, InvocationContext } from '@azure/functions';
import { QueryRequestSchema } from './validator';
import { logger } from '../../shared/logger';
// ... ValidationError de errors.ts

// Função assíncrona com try/catch
// Validar body com QueryRequestSchema.safeParse()
// Retornar 400 para falha de validação (com mensagem do Zod)
// Retornar 200 com stub: { answer: '...', source_document: 'stub' }

app.http('query', {
  methods: ['POST'],
  authLevel: 'anonymous',
  route: 'query',
  handler: queryHandler,
});
```

**Aceite:**
- [ ] Arquivo em `src/functions/query/handler.ts` (path exato conforme Anexo C)
- [ ] Azure Functions v4 (usa `app.http(...)`, não a API v3 com `module.exports`)
- [ ] Validação com Zod via `safeParse` (não parse que lança exceção)
- [ ] Erros logados com `logger.warn(...)` ou `logger.error(...)` — nunca `console.log`
- [ ] `try/catch` explícito na função async
- [ ] Resposta de sucesso inclui `source_document` (campo obrigatório do contrato)
- [ ] Comentário referenciando ADR-0002 na área onde o context budget seria aplicado

---

### TASK-SDD-008 · Criar evidência de SDD e revisão crítica

**Tamanho:** M  
**Depende de:** TASK-SDD-002, TASK-SDD-007  
**Path de destino:** `dgs-ai-first/evidencias/ex-2.2-sdd-tasks-e-revisao.md`

**O que fazer:**  
Documentar o processo SDD e a revisão crítica do código gerado.

**Estrutura do documento:**
```markdown
# Evidência — Ex 2.2: SDD e Implementação

## 1. Processo SDD seguido
(plan.md → tasks.md → implementação — checkpoint por step)

## 2. Decisões do breakdown de tasks
(por que 7 tasks? por que TASK-001 sem dependências?)

## 3. Conexão com o Cenário 1
(protótipo open-source do Ex 1.3 validou a abordagem; agora é código de produção Azure)

## 4. Revisão crítica do código gerado
### Problema 1: [título]
(trecho do código problemático + explicação + correção)
### Problema 2: [título]
(trecho do código problemático + explicação + correção)
```

**Aceite:**
- [ ] Menciona explicitamente que o protótipo open-source (cenário 1, Ex 1.3) validou a abordagem RAG
- [ ] Revisão identifica ao menos 2 problemas reais (não cosméticos)
- [ ] Problemas reais = coisas que quebrariam em produção ou violam os padrões do plan:
  - `console.log` em vez de pino
  - Zod sem mensagens de erro customizadas
  - Handler sem `try/catch` no nível assíncrono
  - Tipos `any` implícitos onde deveria ser `unknown`
  - Ausência de referência à ADR-0002
- [ ] Cada problema tem trecho de código + explicação + correção proposta

---

## Exercício 2.3 — Skills Strategy

### TASK-SKILL-001 · Escrever `skills/foundation/typescript-conventions.md`

**Tamanho:** M  
**Depende de:** TASK-SDD-003, TASK-SDD-007 (para usar exemplos reais do domínio)  
**Path de destino:** `novatech-assistant/skills/foundation/typescript-conventions.md`

**O que fazer:**  
Preencher o arquivo placeholder vazio com a skill Foundation mais importante do projeto.

**Estrutura obrigatória do SKILL.md:**

```markdown
# Skill: TypeScript Conventions
**Nível:** Foundation  
**Ativação:** Leia este arquivo antes de gerar qualquer arquivo `.ts` no projeto.

## Contexto
(quando e por que esta skill existe)

## Regras — DEVE
1. `strict: true` no tsconfig (sem exceções)
2. Imports absolutos via path alias (`@/shared/...`) — nunca `../../..`
3. Naming: PascalCase tipos/classes, camelCase funções/variáveis, SCREAMING_SNAKE_CASE constantes de config
4. Toda função assíncrona com `try/catch` explícito
5. Logger: sempre `pino` — nunca `console.log` ou `console.error`

## Proibições — NÃO DEVE
- `as any` ou `as unknown as X` para contornar tipagem
- `require()` dinâmico (usar `import`)
- `console.log` em qualquer arquivo de `src/`
- Parâmetros de função sem tipo explícito

## Exemplos DO / DON'T
(usar exemplos com o domínio NovaTech — ex: validação de QueryRequest)

## Anti-padrões comuns do Copilot
(coisas que o Copilot realmente gera errado sem esta skill)

## Dependências
Nenhuma — esta é a skill base.
```

**Aceite:**
- [ ] Arquivo não está vazio
- [ ] Tem seção de ativação (frase que indica quando ler)
- [ ] Regras DEVE e NÃO DEVE são prescritivas (não descritivas)
- [ ] Exemplos DO/DON'T usam tipos do domínio NovaTech (`QueryRequest`, `Chunk`, etc.)
- [ ] Anti-padrões são coisas que LLMs realmente geram (não genéricos)
- [ ] Menciona `pino` vs `console.log` explicitamente

---

### TASK-SKILL-002 · Criar evidência de estratégia de skills

**Tamanho:** M  
**Depende de:** TASK-SKILL-001  
**Path de destino:** `dgs-ai-first/evidencias/ex-2.3-skills-estrategia.md`

**O que fazer:**  
Documentar a estratégia completa de skills do projeto.

**Estrutura do documento:**
```markdown
# Evidência — Ex 2.3: Estratégia de Skills

## 1. Árvore de skills do projeto
(Foundation / Domain / Artifact — com todas as skills da hierarquia)

## 2. Mapeamento criação/consumo por papel
(tabela: Skill | Cria | Consome (Papéis) | Consome (Agentes) | Freq. uso)

## 3. Raciocínio das escolhas
(por que QA e PS são criadores, não só consumidores?)

## 4. SKILL.md implementado
(transcrição ou referência ao typescript-conventions.md)
```

**Aceite:**
- [ ] Árvore inclui Foundation, Domain e Artifact
- [ ] QA e PS aparecem como criadores (não só devs) — critério explícito da avaliação
- [ ] Mapeamento tem frequência de uso (não só quem cria/consome)
- [ ] Raciocínio explica por que cada skill existe no projeto (não é genérico)
- [ ] Referencia a hierarquia de diretórios `/skills/foundation/`, `/skills/domain/`, `/skills/artifact/`

---

## Ordem de execução recomendada para a sessão de implementação

```
Bloco 1 — MCP (independente):
  TASK-MCP-001 → TASK-MCP-002

Bloco 2 — SDD Foundation (sem dependências entre si):
  TASK-SDD-001 (plan.md)
  TASK-SDD-005 (logger.ts)

Bloco 3 — SDD Types + Errors:
  TASK-SDD-003 (types.ts) → TASK-SDD-004 (errors.ts)

Bloco 4 — SDD Validator:
  TASK-SDD-006 (validator.ts)  ← depende de TASK-SDD-003

Bloco 5 — SDD Handler:
  TASK-SDD-007 (handler.ts)  ← depende de TASK-SDD-005 + TASK-SDD-006

Bloco 6 — SDD Artifacts:
  TASK-SDD-002 (tasks.md)
  TASK-SDD-008 (evidência + revisão crítica)

Bloco 7 — Skills:
  TASK-SKILL-001 (typescript-conventions.md)
  TASK-SKILL-002 (evidência estratégia)
```

**Total: 12 tasks**  
Estimativa: Bloco 1 (~20 min), Blocos 2–6 (~60 min), Bloco 7 (~30 min)

---

## Checklist de entregáveis por exercício

### Ex 2.1
- [ ] `novatech-assistant/.mcp/mcp.json` — 5 servers com least privilege
- [ ] `dgs-ai-first/evidencias/ex-2.1-mcp-configuracao.md` — mapeamento + evidência + riscos

### Ex 2.2
- [ ] `novatech-assistant/specs/query-endpoint/plan.md` — preenchido
- [ ] `novatech-assistant/specs/query-endpoint/tasks.md` — 7 tasks atômicas
- [ ] `novatech-assistant/src/shared/types.ts`
- [ ] `novatech-assistant/src/shared/errors.ts`
- [ ] `novatech-assistant/src/shared/logger.ts`
- [ ] `novatech-assistant/src/functions/query/validator.ts`
- [ ] `novatech-assistant/src/functions/query/handler.ts`
- [ ] `dgs-ai-first/evidencias/ex-2.2-sdd-tasks-e-revisao.md` — decisões + revisão crítica

### Ex 2.3
- [ ] `novatech-assistant/skills/foundation/typescript-conventions.md` — SKILL.md completo
- [ ] `dgs-ai-first/evidencias/ex-2.3-skills-estrategia.md` — árvore + mapeamento + raciocínio
