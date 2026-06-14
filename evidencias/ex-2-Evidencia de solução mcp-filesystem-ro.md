# MCP filesystem-ro: Problema com --readonly e Solução

## Contexto

O projeto `novatech-assistant` utiliza dois servidores MCP baseados em `@modelcontextprotocol/server-filesystem`:

| Servidor | Diretórios expostos | Intenção |
|---|---|---|
| `filesystem-rw` | `./src`, `./specs`, `./skills` | Leitura e escrita (código-fonte) |
| `filesystem-ro` | `./docs/novatech`, `./data/retrieval-corpus` | Somente leitura (base de conhecimento) |

---

## Problema

O `.mcp/mcp.json` original configurava o `filesystem-ro` com o flag `--readonly`:

```json
"args": ["-y", "@modelcontextprotocol/server-filesystem", "--readonly", "./docs/novatech", "./data/retrieval-corpus"]
```

O servidor falhava ao iniciar com o erro:

```
Error: ENOENT: no such file or directory, stat '.../--readonly'
```

### Causa raiz

O pacote `@modelcontextprotocol/server-filesystem` **não suporta `--readonly` como flag CLI** em nenhuma versão disponível (testadas: `0.6.2`, `2025.1.14`, `2025.3.28`, `2026.1.14`). O servidor interpreta todos os argumentos posicionais como caminhos de diretório — incluindo `--readonly`, que tenta ser acessado como pasta e falha com `ENOENT`.

---

## Solução

### 1. Remover o flag inválido do `.mcp.json`

```json
"filesystem-ro": {
  "command": "/usr/bin/npx",
  "args": ["-y", "@modelcontextprotocol/server-filesystem", "./docs/novatech", "./data/retrieval-corpus"]
}
```

### 2. Aplicar read-only no nível do sistema operacional

Como o pacote não implementa proteção de escrita via flag, a restrição é aplicada diretamente nas permissões do filesystem Linux:

```bash
chmod -R a-w docs/novatech data/retrieval-corpus
```

Isso remove a permissão de escrita para todos os usuários nos diretórios expostos pelo `filesystem-ro`. Qualquer tentativa de escrita via MCP é rejeitada pelo SO — efeito equivalente ao `--readonly` pretendido.

O `filesystem-rw` não é afetado pois expõe diretórios diferentes (`src/`, `specs/`, `skills/`).

---

## Observações adicionais

- O arquivo de configuração correto para o Claude Code VS Code extension é `.mcp.json` na raiz do projeto, não `.mcp/mcp.json` (subdiretório).
- O `command` deve usar o path absoluto do `npx` (`/usr/bin/npx`) para garantir que o Claude Code encontre o executável em shells não-interativos.
- O servidor `git` requer `uvx` (gerenciador de pacotes Python `uv`) — instalar via `curl -LsSf https://astral.sh/uv/install.sh | sh`.
