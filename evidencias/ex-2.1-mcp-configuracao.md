# Evidência — Ex 2.1: Configuração de MCP Servers

## 1. Mapeamento necessidade → server

| Necessidade | Server | Tools/Resources expostos | Escopo | Acesso |
|---|---|---|---|---|
| Ler e editar código, specs e skills | `filesystem-rw` | read_file, write_file, list_directory | `./src`, `./specs`, `./skills` | read-write |
| Ler documentação de negócio NovaTech | `filesystem-ro` | read_file, list_directory | `./docs/novatech` | **read-only** |
| Simular retrieval do corpus de chunks | `filesystem-ro` | read_file, list_directory | `./data/retrieval-corpus` | **read-only** |
| Consultar histórico, diff e branches | `git` | git_log, git_diff, git_show, git_status | `.` (raiz) | read-only por natureza |
| Glossário e decisões persistentes entre sessões | `memory` | create_entities, search_nodes, add_relations | grafo local | read-write |
| Explorar primitivas MCP (tools, resources, prompts) | `everything` | echo, add, printEnv, sampleLLM, ... | — | demonstração |

**Justificativa do least privilege:**
- `docs/novatech/` e `data/retrieval-corpus/` são fontes de verdade do negócio. Um agente com escrita poderia sobrescrever POL-001 com conteúdo alucinado, corrompendo o corpus de retrieval para todas as sessões futuras.
- `src/`, `specs/` e `skills/` precisam de escrita para que o agente gere e edite artefatos de código.
- Escopo nunca inclui `./` (raiz) para proteger `.env`, `node_modules` e arquivos de configuração do sistema.
- Dois blocos `filesystem` separados (rw vs ro) porque o server não suporta flag `--readonly` por pasta — a separação é feita por instâncias com escopos distintos.

---

## 2. `.mcp/mcp.json` final

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

---

## 3. Evidência de uso real

> Execução realizada no Claude Code (extensão VS Code) com o projeto `novatech-assistant` aberto.  
> Evidências em: `ex2-Evidencia Uso MCP filesystem.png`, `ex2-Evidencia Uso MCP filesystem2.png`, `ex2-Evidencia Uso MCP Git.png`

### 3a. Agente lê doc NovaTech via filesystem-ro

**Prompt enviado:** "Use o MCP server filesystem-ro para listar os arquivos em docs/novatech/ e depois ler o conteúdo completo de POL-001-politica-devolucao.md"

**Tool calls executadas (dots verdes no Claude Code):**
```
Filesystem-ro [list_directory]
path: /home/rafaelchaves/dev/DB1/novatech-assistant/docs/novatech
OUT: {"content":"[FILE] FAQ-atendimento.md\n[FILE] POL-001-politica-devolucao.md\n
     [FILE] PROC-042-frete-especial-v1.md\n[FILE] PROC-042-v2-frete-especial-revisado.md\n
     [FILE] README.md\n[FILE] SLA-2024-tabela-sla-clientes.md"}

Filesystem-ro [read_file]
path: /home/rafaelchaves/dev/DB1/novatech-assistant/docs/novatech/POL-001-politica-devolucao.md
OUT: {"content":"# POL-001 — Política de Devolução de Mercadorias\n\n**Versão:** 3.1\n
     **Última atualização:** 15/01/2024\n**Responsável:** Diretoria de Operações\n..."}
```

**Resultado:** agente listou 6 arquivos e leu o conteúdo completo do POL-001 via instância `filesystem-ro`. Nenhuma tool de escrita estava disponível neste server.

---

### 3b. Agente recupera chunk via filesystem-ro (coerente com Anexo B)

**Prompt enviado:** "Um atendente perguntou: 'Qual é o prazo para devolução de mercadorias?' Use o MCP server filesystem-ro para ler data/retrieval-corpus/chunks-novatech.md e identifique quais chunks são mais relevantes."

**Tool call executada:**
```
Filesystem-ro [read_file]
path: /home/rafaelchaves/dev/DB1/novatech-assistant/data/retrieval-corpus/chunks-novatech.md
```

**Chunks identificados pelo agente como relevantes:**

| Chunk | Relevância | Motivo |
|-------|-----------|--------|
| `POL-001-A` | **Primário — obrigatório** | Seção 3.1: prazo geral de 7 dias úteis |
| `POL-001-B` | **Primário — obrigatório** | Seção 3.2: exceções ao processo padrão |
| `PROC-042-v2` | Secundário | Dominantemente diferente — frete, não devolução |
| `SLA-2024-*` | Secundário | SLAs de atendimento, não prazo de devolução |
| `FAQ-38` | Pode aparecer | Carga danificada — processo distinto |

**Resposta sugerida pelo agente com base nos chunks:**
> "O prazo para solicitar a devolução é de **7 dias úteis** após a data de recebimento confirmado no sistema de tracking. Sábados, domingos e feriados nacionais não são contabilizados. Cargas perigosas (classes 1–6 ANTT), cargas refrigeradas com cadeia de frio rompida e cargas com lacre violado **não são elegíveis** pelo processo padrão — nesses casos, orientar o cliente a contatar a Gestão de Riscos pelo ramal 4500."

**Coerência com Anexo B:** `POL-001-A` (DEVE recuperar) e `POL-001-B` (DEVE recuperar) identificados corretamente como primários. Resultado consistente com o mapa de cobertura do Anexo B para a pergunta "prazo de devolução".

---

### 3c. Agente lê histórico do repo via git

**Prompt enviado:** "Use o MCP server git para listar os commits mais recentes deste repositório."

**Tool call executada:**
```
Git [git_log]
OUT: Commit history:
     Commit: 'bbdd03aeecd7e349a2bfc93849e0552a0b766ac6'
     Author: <git.Actor "Trilha AI First trilha@db1.local">
```

**Detalhes do commit:**

| Campo | Detalhe |
|-------|---------|
| Hash | `bbdd03a` |
| Autor | Trilha AI First `<trilha@db1.local>` |
| Data | 09/06/2026 às 18:13 UTC |
| Mensagem | `chore: starter repo (Anexo D) — estrutura + dados semeados dos Anexos A e B` |

**Resultado:** server `git` executou `git_log` com sucesso. O repositório `novatech-assistant` tem 1 commit (o commit inicial do starter repo). O server é read-only por natureza — não expõe tools como `git_commit` ou `git_push`.

---

### 3d. Descoberta durante execução: flag `--readonly` não suportada

Durante a ativação do `filesystem-ro`, foi descoberto que o pacote `@modelcontextprotocol/server-filesystem` **não suporta `--readonly` como flag CLI** em nenhuma versão disponível. O servidor interpreta todos os argumentos posicionais como caminhos de diretório, tentando acessar `--readonly` como pasta e falhando com `ENOENT`.

**Workaround aplicado:** restrição de escrita aplicada no nível do SO:
```bash
chmod -R a-w docs/novatech data/retrieval-corpus
```

Isso remove a permissão de escrita para todos os usuários nos diretórios expostos pelo `filesystem-ro`. Qualquer tentativa de escrita via MCP é rejeitada pelo SO — efeito equivalente ao `--readonly` pretendido.

Essa descoberta reforça o risco documentado na seção 4: a separação em duas instâncias (`filesystem-rw` e `filesystem-ro`) é necessária precisamente porque o server não oferece controle de acesso interno — a proteção precisa vir de fora (permissões do SO ou escopos de pastas distintos).

---

## 4. Análise de riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| `filesystem-rw` configurado com escopo `./` (raiz) expõe `.env` com chaves de API ao contexto do agente | **Alto** — o agente inclui `AZURE_OPENAI_KEY` e `AZURE_AI_SEARCH_KEY` no contexto e os vaza em respostas ou logs | Escopo mínimo e explícito: `./src ./specs ./skills`. Nunca usar `./` ou `..` como argumento do server. Verificar em code review que nenhum path de raiz foi adicionado. |
| `filesystem-ro` configurado na instância errada (sem `--readonly`) habilita escrita nas fontes de negócio | **Alto** — agente pode sobrescrever `POL-001-politica-devolucao.md` com conteúdo alucinado, corrompendo o corpus de retrieval para todas as sessões futuras sem aviso | Usar instância separada do server com escopo limitado a `./docs/novatech` e `./data/retrieval-corpus`; adicionar `--readonly` na linha de args; validar na revisão de `.mcp/mcp.json` que a instância ro não tem tools de escrita. |
| Server `memory` sem versionamento sobrescreve decisões e glossário silenciosamente entre sessões | **Médio** — uma sessão pode adicionar uma entidade errada (ex: "Platinum tier existe") que persiste e contamina sessões futuras | Commitar exports periódicos do grafo de memória como artefatos Git; tratar o grafo como versionado; documentar no `AGENTS.md` o procedimento de reset e auditoria do grafo. |
