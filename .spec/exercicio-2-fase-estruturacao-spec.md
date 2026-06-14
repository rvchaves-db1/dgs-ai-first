# Exercício 2 — Spec: Fase de Estruturação do Trabalho

**Participante:** Rafael Chaves  
**Papel:** Desenvolvedor  
**Data:** 2026-06-14  
**Branch:** cenario-2 (em `dgs-ai-first`)  
**Tópicos:** MCP, SDD, AGENTS.md, Skills

---

## Contexto e premissas

O cenário 2 começa onde o cenário 1 parou: o discovery está concluído, as ADRs foram produzidas e o protótipo de RAG (Python + ChromaDB) validou a abordagem. Agora o time precisa estruturar o ambiente de desenvolvimento antes de escrever código de produção.

**Decisões herdadas do cenário 1 que impactam este exercício:**
- Stack de produção: TypeScript (backend), Azure Functions v4, Zod (validação), pino (logging), Vitest (testes)
- Context budget: ~4K tokens system prompt + ~8K chunks (5 chunks de ~1.500 tokens) — ADR-0002
- Documentos contraditórios: metadado de vigência, priorizar mais recente — ADR-0003
- Sistema de busca: Azure AI Search (produção); `data/retrieval-corpus/` simula localmente
- Documentação de negócio: `docs/novatech/` simula o SharePoint/Confluence da NovaTech

---

## Estado do Starter Repo (Anexo D) — descoberto em 2026-06-14

O Anexo D (`Anexo-D-starter-repo-novatech-assistant.zip`) foi extraído e movido para `C:\Users\rafael.chaves\Documents\Avaliações\IA First\Certificação AI First DB1\novatech-assistant\` — **um nível acima** de `dgs-ai-first`, como repo git independente. O zip continha um repositório git completo (com `.git/`) que foi inicialmente extraído de forma achatada (flat), destruindo a hierarquia de diretórios. Após extração correta via `Expand-Archive`, o repo ficou acessível.

**Paths de referência:**
- Repo de certificação: `.../Certificação AI First DB1/dgs-ai-first/`
- Repo do projeto: `.../Certificação AI First DB1/novatech-assistant/`

### O que JÁ existe no starter repo

| Item | Status | Observação |
|------|--------|-----------|
| Estrutura de diretórios | ✅ Completa | Idêntica ao Anexo C |
| `docs/novatech/` | ✅ Semeado | 5 docs da NovaTech (POL-001, PROC-042 v1+v2, SLA-2024, FAQ) |
| `data/retrieval-corpus/` | ✅ Semeado | Chunks do Anexo B + README de uso |
| `package.json` | ✅ Configurado | TypeScript 5.5, Vitest 2.0, Zod 3.23 |
| `tsconfig.json` | ✅ Existe | (verificar se strict: true) |
| `.mcp/mcp.example.json` | ✅ Existe | Exemplo com filesystem, git, memory, everything |
| `.mcp/mcp.json` | ⬜ Vazio (`{}`) | **Entregável do Ex 2.1** |
| `AGENTS.md` | ⬜ Skeleton | TODOs por papel — Developer não preenche diretamente |
| `skills/foundation/*.md` | ⬜ Vazios | **`typescript-conventions.md` = entregável Ex 2.3** |
| `skills/domain/*.md` | ⬜ Vazios | Fora do escopo desta fase |
| `skills/artifact/*.md` | ⬜ Vazios | Fora do escopo desta fase |
| `specs/query-endpoint/plan.md` | ⬜ Vazio | Conteúdo vem do enunciado do exercício — copiar |
| `specs/query-endpoint/tasks.md` | ⬜ Vazio | **Entregável do Ex 2.2** |
| `specs/query-endpoint/requirements.md` | ⬜ Vazio | Papel do PS (fora do escopo Dev) |
| `src/**/*.ts` | ⬜ Scaffolds vazios | Código do Ex 2.2 vai em `src/functions/query/` e `src/shared/` |
| `.github/workflows/` | ✅ Existe | CI/CD básico (lint + build) |
| `infra/` | ✅ Existe | Bicep narrativo — não provisionar recurso real |

### O que NÃO existe ainda (a criar neste exercício)

```
[Certificação AI First DB1/]
│
├── novatech-assistant/              ← repo do projeto (independente)
│   ├── .mcp/mcp.json               ← Ex 2.1 (preencher)
│   ├── specs/query-endpoint/
│   │   ├── plan.md                 ← copiar do enunciado (input do Ex 2.2)
│   │   └── tasks.md                ← Ex 2.2 (criar do zero)
│   ├── src/functions/query/
│   │   ├── handler.ts              ← Ex 2.2 (implementar)
│   │   └── validator.ts            ← Ex 2.2 (implementar)
│   ├── src/shared/
│   │   ├── types.ts                ← Ex 2.2 (implementar)
│   │   ├── errors.ts               ← Ex 2.2 (implementar)
│   │   └── logger.ts               ← Ex 2.2 (implementar)
│   └── skills/foundation/
│       └── typescript-conventions.md  ← Ex 2.3 (implementar)
│
└── dgs-ai-first/                   ← repo de certificação
    └── evidencias/
        ├── ex-2.1-mcp-configuracao.md     ← mapeamento + riscos + evidência de uso
        ├── ex-2.2-sdd-tasks-e-revisao.md  ← iteração Copilot + revisão crítica
        └── ex-2.3-skills-estrategia.md    ← árvore de skills + mapeamento criação/consumo
```

---

## Exercício 2.1 — Configuração de MCP Servers

### O que será feito

Partir do `.mcp/mcp.example.json` já existente, definir o mapeamento necessidade → server com least privilege, preencher o `.mcp/mcp.json` real e documentar evidência de uso.

### Ponto de partida: `.mcp/mcp.example.json`

O arquivo já existe com 4 servers (filesystem, git, memory, everything) sem escopos definidos. Nosso trabalho é **aplicar least privilege**: definir quais caminhos cada server acessa e separar fontes read-only das read-write.

### Mapeamento necessidade → server

| Necessidade | Server | Escopo | Acesso |
|---|---|---|---|
| Código, specs, skills (ler e editar) | `filesystem-rw` | `./src ./specs ./skills` | read-write |
| Docs de negócio NovaTech | `filesystem-ro` | `./docs/novatech` | **read-only** |
| Corpus de chunks (retrieval simulado) | `filesystem-ro` | `./data/retrieval-corpus` | **read-only** |
| Histórico, diff, branches do repo | `git` | `.` (raiz) | read-only por natureza |
| Glossário e decisões persistentes | `memory` | grafo local | read-write |
| Explorar primitivas MCP | `everything` | — | demonstração |

**Justificativa do least privilege:**
- `docs/novatech/` e `data/retrieval-corpus/` são fontes de verdade do negócio — agente com escrita poderia corromper o corpus de retrieval com conteúdo alucinado
- `src/`, `specs/`, `skills/` precisam de escrita para que o agente gere e edite artefatos
- Escopo nunca inclui `./` (raiz) para proteger `.env`, `node_modules`, configs do sistema
- Dois blocos `filesystem` separados (rw vs ro) porque o server não suporta flag `--readonly` por pasta — a separação é feita por instâncias distintas

### Arquivo `.mcp/mcp.json` — estrutura alvo

```json
{
  "mcpServers": {
    "filesystem-rw": {
      "command": "npx",
      "args": [
        "-y", "@modelcontextprotocol/server-filesystem",
        "./src", "./specs", "./skills"
      ]
    },
    "filesystem-ro": {
      "command": "npx",
      "args": [
        "-y", "@modelcontextprotocol/server-filesystem",
        "--readonly",
        "./docs/novatech",
        "./data/retrieval-corpus"
      ]
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

> **Nota:** A flag `--readonly` no `@modelcontextprotocol/server-filesystem` precisa ser verificada contra o README atual do repositório `modelcontextprotocol/servers` (a API evolui). Se não suportada, a separação em dois blocos continua válida — o segundo bloco expõe apenas os paths de leitura sem tools de escrita disponíveis naquele escopo.

### Evidência de uso real

A evidência documentará sessão do Claude Code com MCP ativo, mostrando que o agente:
- **Lê um doc NovaTech:** lista e lê `docs/novatech/POL-001-politica-devolucao.md` via `filesystem-ro`
- **Recupera chunk relevante:** consulta `data/retrieval-corpus/chunks-novatech.md` para a pergunta "Qual o prazo de devolução?" e identifica `POL-001-A` e `POL-001-B` como os mais relevantes (coerente com mapa do Anexo B)
- **Lê histórico git:** usa o server `git` para ler o log de commits do repo

### Riscos de segurança

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| `filesystem-rw` com escopo `./` expõe `.env` e segredos | Alto — agente vaza chaves de API para contexto | Escopo mínimo: apenas `./src ./specs ./skills`; nunca a raiz |
| `filesystem-ro` com escrita habilitada (server errado) | Alto — agente sobrescreve corpus de retrieval com alucinações | Usar instância separada do server com escopo limitado às pastas de negócio |
| `memory` server sem versionamento | Médio — decisões/glossário sobrescritos silenciosamente entre sessões | Commitar exports do grafo de memória periodicamente; tratar como artefato versionado |

### Entregáveis do Ex 2.1

- `[...]/novatech-assistant/.mcp/mcp.json` — configuração final com least privilege
- `[...]/dgs-ai-first/evidencias/ex-2.1-mcp-configuracao.md` — mapeamento + riscos + transcrição de evidência de uso

---

## Exercício 2.2 — Implementação com SDD (plan → tasks → código)

### O que será feito

1. Copiar o `plan.md` do enunciado para `specs/query-endpoint/plan.md`
2. Converter o `plan.md` em `tasks.md` com tasks atômicas
3. Implementar a TASK-001 (setup do handler + validação Zod)
4. Revisar criticamente o código gerado

### Input: `plan.md` do enunciado (a copiar para `specs/query-endpoint/plan.md`)

```markdown
# Plan — Query Endpoint

## Approach
Azure Function HTTP trigger que:
1. Recebe pergunta do atendente via POST /api/query
2. Converte pergunta em embedding via Azure OpenAI
3. Busca top-5 chunks no Azure AI Search
4. Monta prompt com chunks + system prompt + pergunta
   (respeitando context budget: ~4K system + ~8K chunks + pergunta)
5. Envia ao GPT-4o e retorna resposta com source_document

## Technical Decisions
- TypeScript com Azure Functions v4
- Zod para validação de input/output
- Retry com exponential backoff para chamadas Azure
- Structured logging com pino

## Prior Decisions (do cenário 1)
- Context budget definido na ADR-0002: ~4K system + ~8K chunks
- Documentos contraditórios tratados com metadado de vigência (ADR-0003)
- System prompt versionado em /prompts/system-prompt.md

## Dependencies
- Azure AI Search index must be populated (pipeline de ingestão)
- System prompt must be finalized (ver /prompts/system-prompt.md)
```

### Decomposição em tasks (`tasks.md`)

| ID | Descrição | Tamanho | Depende de | Implementada |
|----|-----------|---------|-----------|--------------|
| TASK-001 | Setup do endpoint: handler + validação Zod do input | P | — | **Sim (Ex 2.2)** |
| TASK-002 | Embedding da pergunta via Azure OpenAI | M | TASK-001 | Não |
| TASK-003 | Busca top-5 chunks no Azure AI Search | M | TASK-002 | Não |
| TASK-004 | Montagem do prompt com context budget (ADR-0002) | M | TASK-003 | Não |
| TASK-005 | Chamada ao GPT-4o + resposta com `source_document` | M | TASK-004 | Não |
| TASK-006 | Retry com exponential backoff para chamadas Azure | P | TASK-002, TASK-005 | Não |
| TASK-007 | Testes de integração do handler (Vitest + msw + fixtures) | G | TASK-001–005 | Não |

**TASK-001 implementada neste exercício** — é a única sem dependências, isolável e testável sozinha.

### TASK-001 — Critérios de aceite verificáveis

- [ ] `POST /api/query` → 400 para body sem campo `question`
- [ ] `POST /api/query` → 400 para `question` com string vazia ou só espaços
- [ ] `POST /api/query` → 400 para `question` acima de 2.000 caracteres
- [ ] `POST /api/query` → 422 para body não-JSON
- [ ] `POST /api/query` com `question` válida → 200 com stub de resposta incluindo campo `source_document`
- [ ] Erros de validação logados via `pino` (nunca `console.log`)
- [ ] Schema Zod exportado separadamente (reutilizável nos testes)
- [ ] Handler no path correto: `src/functions/query/handler.ts`

### Arquivos a criar

```
src/functions/query/
├── handler.ts      # Azure Function HTTP trigger v4 — lógica do endpoint
└── validator.ts    # Schema Zod + função de validação do input

src/shared/
├── types.ts        # QueryRequest, QueryResponse, Chunk (tipos do domínio)
├── errors.ts       # ValidationError, SearchError, CompletionError
└── logger.ts       # Instância pino configurada
```

### Revisão crítica do código gerado

Após gerar com Copilot, identificar ao menos 2 problemas reais (não cosméticos):
- Provável uso de `console.log` em vez de pino
- Validação Zod sem mensagens de erro customizadas (dificulta debugging do atendente)
- Handler sem `try/catch` no nível assíncrono (unhandled promise rejection)
- Tipos `any` implícitos onde deveria ser `unknown` ou tipo explícito
- Ausência de referência à ADR-0002 no comment do context budget

### Entregáveis do Ex 2.2

- `[...]/novatech-assistant/specs/query-endpoint/plan.md` — preenchido com input do enunciado
- `[...]/novatech-assistant/specs/query-endpoint/tasks.md` — tasks atômicas com critérios de aceite
- `[...]/novatech-assistant/src/functions/query/handler.ts` — TASK-001
- `[...]/novatech-assistant/src/functions/query/validator.ts` — TASK-001
- `[...]/novatech-assistant/src/shared/types.ts`, `errors.ts`, `logger.ts` — shared
- `[...]/dgs-ai-first/evidencias/ex-2.2-sdd-tasks-e-revisao.md` — decisões do breakdown + revisão crítica

---

## Exercício 2.3 — Estratégia de Skills do Projeto

### O que será feito

Documentar a estratégia completa de skills (árvore + mapeamento por papel) e implementar o `typescript-conventions.md` no slot vazio que o starter repo já criou.

### Contexto: todos os arquivos de skills já existem como placeholders vazios

O starter repo tem a hierarquia correta com arquivos `.md` em cada posição. O Dev escreve `typescript-conventions.md` (Foundation level). As demais skills são atribuídas a outros papéis ou ficam para próximas fases.

### Árvore de skills do projeto

```
skills/
├── foundation/                          # Convenções globais — lidas por TODAS as outras
│   ├── typescript-conventions.md        # ← IMPLEMENTAR neste exercício (Dev)
│   ├── error-handling.md                # (Tech Lead — fase futura)
│   └── project-structure.md            # (Tech Lead — fase futura)
│
├── domain/                              # Padrões por camada técnica
│   ├── azure-functions-endpoint.md      # (Tech Lead — Ex 2.3 do papel TL)
│   ├── azure-ai-search-integration.md   # (Dev Sênior — fase futura)
│   ├── react-components.md              # (Tech Lead — fase futura)
│   └── testing-patterns.md             # (QA — Ex 2.3 do papel QA)
│
└── artifact/                            # Receitas de geração completas
    ├── create-rag-endpoint.md           # (Tech Lead + Dev Sênior — fase futura)
    ├── create-integration-test.md       # (QA — Ex 2.3 do papel QA)
    └── create-react-card.md             # (Tech Lead — fase futura)
```

### Mapeamento criação/consumo por papel

| Skill | Cria | Consome (Papéis) | Consome (Agentes) | Freq. de uso |
|-------|------|------------------|-------------------|-------------|
| `typescript-conventions` | **Dev (este ex.)** | Dev, QA, TL | Copilot, Claude Code | Toda sessão de código |
| `error-handling` | Tech Lead | Dev | Copilot | Por função que pode falhar |
| `project-structure` | Tech Lead | Dev, QA | Copilot | Onboarding + novas pastas |
| `azure-functions-endpoint` | Tech Lead | Dev | Copilot | Por endpoint criado |
| `azure-ai-search-integration` | Dev Sênior | Dev | Copilot | Por integração de busca |
| `react-components` | Tech Lead | Dev (frontend) | Copilot | Por componente criado |
| `testing-patterns` | QA | Dev, QA | Copilot, Claude Code | Por test suite |
| `create-rag-endpoint` | TL + Dev Sênior | Dev Pleno | Copilot | Por endpoint RAG novo |
| `create-integration-test` | QA | Dev, QA | Copilot | Por módulo testado |
| `create-react-card` | Tech Lead | Dev (frontend) | Copilot | Por card no painel |
| Spec SDD template | Product Specialist | PS, TL, Dev | Claude Code | Por módulo especificado |

**Insight multi-papel:** QA e PS são criadores de skills (não apenas consumidores). Isso é fundamental — skills de teste e de spec são domínio do QA e do PS, não dos devs.

### `typescript-conventions.md` — conteúdo prescritivo

O arquivo já existe vazio em `skills/foundation/typescript-conventions.md`. Precisamos preenchê-lo com:

1. **Contexto/ativação:** frase que indica quando esta skill deve ser lida
2. **Regras obrigatórias (DEVE):**
   - `strict: true` no tsconfig (sem exceções)
   - Imports absolutos via path alias (`@/services/...`) — nunca `../../..`
   - Naming: `PascalCase` para tipos/classes, `camelCase` para funções/variáveis, `SCREAMING_SNAKE_CASE` para constantes de configuração
   - Toda função assíncrona com `try/catch` explícito
   - Logger: sempre `pino` — nunca `console.log`/`console.error`
3. **Proibições (NÃO DEVE):**
   - `as any` ou `as unknown as X` para contornar tipagem
   - `require()` dinâmico (usar `import`)
   - `console.log` em qualquer arquivo de `src/`
   - Tipos implícitos em parâmetros de função
4. **Exemplos DO/DON'T** com código real do domínio NovaTech (ex: validação de QueryRequest)
5. **Anti-padrões comuns do Copilot** que esta skill previne
6. **Dependências:** nenhuma (é Foundation)

### Entregáveis do Ex 2.3

- `[...]/novatech-assistant/skills/foundation/typescript-conventions.md` — SKILL.md preenchido
- `[...]/dgs-ai-first/evidencias/ex-2.3-skills-estrategia.md` — árvore completa + mapeamento criação/consumo + raciocínio das escolhas

---

## Ordem de execução (atualizada)

1. ~~Criar estrutura do starter repo~~ → ✅ **Já existe** (Anexo D extraído)
2. ~~Semear dados~~ → ✅ **Já semeado** (docs NovaTech + chunks)
3. Criar branch `cenario-2` no repo `dgs-ai-first`
4. **Ex 2.1:** Preencher `.mcp/mcp.json` com least privilege → documentar evidência de uso → análise de riscos
5. **Ex 2.2:** Copiar `plan.md` do enunciado → criar `tasks.md` → implementar TASK-001 → revisão crítica
6. **Ex 2.3:** Documentar estratégia de skills → escrever `typescript-conventions.md`
7. Criar evidências consolidadas para cada exercício

---

## Critérios de aceite globais

### Ex 2.1
- [ ] `.mcp/mcp.json` sintaticamente válido, com 5 servers (filesystem-rw, filesystem-ro, git, memory, everything)
- [ ] Fontes de negócio (`docs/novatech/`, `data/retrieval-corpus/`) em instância separada (read-only)
- [ ] Escopo de `filesystem-rw` é `./src ./specs ./skills` — nunca `./`
- [ ] Evidência: agente lê doc, recupera chunk coerente com Anexo B, lê commits via git
- [ ] 3 riscos documentados com impacto e mitigação acionável

### Ex 2.2
- [ ] `plan.md` preenchido com conteúdo do enunciado (não vazio)
- [ ] Cada task tem: ID, descrição, critérios verificáveis, dependências, tamanho P/M/G
- [ ] Código em `src/functions/query/` — path correto conforme Anexo C
- [ ] TypeScript strict, Zod, pino, Azure Functions v4
- [ ] Revisão crítica: ao menos 2 problemas reais identificados (não cosméticos)
- [ ] Referência à ADR-0002 presente no código (context budget)
- [ ] Conexão com cenário 1: reconhece que o protótipo open-source (Ex 1.3) validou a abordagem

### Ex 2.3
- [ ] Árvore inclui papéis não-dev como criadores (QA para testing-patterns, PS para spec template)
- [ ] `typescript-conventions.md` tem exemplos de código com snippets do domínio NovaTech
- [ ] Anti-padrões são coisas que LLMs realmente geram de errado (não genéricos)
- [ ] Arquivo no path correto: `skills/foundation/typescript-conventions.md`
- [ ] Evidência de estratégia documentada separadamente (não só o SKILL.md)
