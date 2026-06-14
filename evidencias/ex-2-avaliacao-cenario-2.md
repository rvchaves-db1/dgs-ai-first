# Avaliação — Cenário 2 / Papel Desenvolvedor

**Programa:** Trilha de Certificação AI First — DGS / DB1 Global Software  
**Participante:** Rafael Chaves  
**Papel:** Desenvolvedor  
**Cenário:** 2 — Fase de Estruturação do Trabalho  
**Exercícios avaliados:** 2.1, 2.2, 2.3  
**Data da avaliação:** 2026-06-14  
**Avaliador:** Claude Sonnet 4.6 (via Claude Code)

---

## Resumo Consolidado

| Exercício | Score | Classificação |
|-----------|-------|---------------|
| 2.1 — Configuração de MCP Servers | 3.0 | Aprovado com distinção |
| 2.2 — Implementação com SDD | 3.0 | Aprovado com distinção |
| 2.3 — Estratégia de Skills | 2.8 | Aprovado com distinção |
| **Média do Cenário** | **2.93** | **Aprovado com distinção** |

**Padrão de excelência consistente:** evidência de execução real (Ex 2.1), revisão crítica com snippets concretos (Ex 2.2) e artefatos prescritivos com anti-padrões reais (Ex 2.3). A única lacuna transversal é a ausência de documentação do processo iterativo no Ex 2.3 — os outros dois exercícios demonstram que o participante sabe fazê-lo quando aplica.

---

## Avaliação do Exercício 2.1 — Configuração de MCP Servers

### Resumo
Entregável completo e sofisticado: mapeamento necessidade → server com least privilege explícito, mcp.json com 5 servers e escopos corretos, evidência de execução real com tool calls documentados (list_directory, read_file, git_log) e outputs coerentes com o Anexo B. Destaque para a descoberta autêntica de que a flag `--readonly` do server-filesystem não funciona como CLI arg, com workaround via chmod documentado e justificado.

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | 3 | Distingue tools/resources por server (read_file vs write_file vs git_log vs create_entities); aplica least privilege com justificativa por server; dois blocos filesystem separados porque o server não suporta controle por pasta — demonstra entendimento da arquitetura MCP, não só da configuração. |
| D2 — Uso de Ferramentas | 3 | Evidência de execução real com tool calls e outputs transcritos; o agente recuperou POL-001-A e POL-001-B como chunks primários, coerente com o mapa do Anexo B; git_log executado com hash e autor reais; descoberta iterativa da limitação `--readonly` com workaround aplicado. |
| D3 — Qualidade do Entregável | 3 | mcp.json sintaticamente correto com 5 servers; escopos mínimos (`./src ./specs ./skills` para rw; `./docs/novatech ./data/retrieval-corpus` para ro); três riscos com impacto e mitigação acionável (expõe AZURE_OPENAI_KEY, corrompe corpus, grafo sem versionamento). **Nota:** o mcp.json documentado ainda contém `--readonly` nos args do filesystem-ro, que a seção 3d prova não funcionar — a versão final deveria ter o flag removido. |
| D4 — Pensamento Crítico | 3 | Descoberta genuína: `--readonly` tenta acessar um diretório chamado `--readonly` e falha com ENOENT. Solução alternativa (chmod) aplicada e conectada ao risco documentado na seção 4. Análise de riscos cita chaves específicas do projeto (AZURE_OPENAI_KEY, AZURE_AI_SEARCH_KEY) e consequência concreta (corpus de retrieval corrompido para sessões futuras). |
| D5 — Aplicabilidade ao Projeto | 3 | Referencia docs/novatech/, data/retrieval-corpus/, chunks POL-001-A e POL-001-B do Anexo B; menciona AZURE_OPENAI_KEY e AZURE_AI_SEARCH_KEY como segredos reais do projeto; cita AGENTS.md como destino do procedimento de reset do memory server; estrutura coerente com o Anexo C. |

**Score do exercício: 3.0**

### Verificação de Artefatos Machine-Readable
O mcp.json é o artefato machine-readable central — sintaticamente válido, um agente ou Claude Code consegue consumi-lo diretamente. A evidência de uso documenta que o agente de fato executou as tools expostas pelos servers. Artefato aprovado.

### Pontos Fortes
1. Evidência de execução real com saída transcrita — tool calls com paths absolutos e conteúdo retornado, incluindo os chunks do Anexo B identificados corretamente.
2. Descoberta e resolução da limitação da flag `--readonly` transforma um potencial ponto de falha silencioso em conhecimento documentado e acionável para o time.
3. Análise de riscos específica ao projeto: não cita "alguém pode hackear" — cita o AZURE_OPENAI_KEY e a corrupção do corpus de retrieval como consequências concretas.

### Pontos de Melhoria
1. **mcp.json inconsistente:** a seção 2 ("configuração final") ainda tem `--readonly` nos args do filesystem-ro mesmo após a seção 3d provar que isso quebra o server. O arquivo final deveria ter o flag removido, com um comentário indicando que a proteção é feita via chmod.
2. **memory server sem escopo de path:** o server `memory` é configurado sem documentar em qual diretório persiste o grafo local — em diferentes ambientes (CI, dev, prod) isso pode variar.
3. **Evidência como texto reconstituído:** a transcrição usa path `/home/rafaelchaves/dev/DB1/novatech-assistant/` (Linux) diferente do path real do projeto no Windows. Os screenshots existem, mas a transcrição parece reconstituída. Recomendação: usar a transcrição exportada pelo Claude Code diretamente.

### Classificação
**Aprovado com distinção (3.0)**

---

## Avaliação do Exercício 2.2 — Implementação com SDD (plan → tasks → código)

### Resumo
SDD executado em três etapas rigorosas (plan → tasks → código), com tasks verdadeiramente atômicas e critérios de aceite verificáveis. O código da TASK-001 segue todos os padrões do cenário 1 (TypeScript strict, Zod safeParse, pino, Azure Functions v4, try/catch explícito) e inclui o comentário de ADR-0002. Revisão crítica documenta dois problemas reais — console.log e parse vs safeParse — com snippets do Copilot, impacto em produção e correção aplicada.

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | 3 | Decomposição em grafo de dependências explícita (não lista plana); entende por que TASK-001 é o único ponto de entrada isolável; entende por que TASK-006 (retry) depende de TASK-002/005 (precisa dos contratos de erro); checkpoint de qualidade documentado entre steps. |
| D2 — Uso de Ferramentas | 3 | Revisão crítica com snippets reais do Copilot — não "o Copilot pode cometer erros", mas o trecho exato gerado, o motivo pelo qual falha em produção (Application Insights vs console, 500 vs 400 ao atendente) e a correção aplicada. Dois problemas reais identificados e corrigidos. |
| D3 — Qualidade do Entregável | 3 | plan.md preenchido; tasks.md com 7 tasks, cada uma com ID, tamanho, dependências e critérios verificáveis (TASK-001 com 12 checkboxes prescritivos); código em `src/functions/query/` e `src/shared/` — paths exatos do Anexo C; TypeScript, Zod safeParse, pino, Azure Functions v4 app.http, try/catch duplo. **Nota:** handler.ts usa imports relativos (`'../../shared/logger.js'`) em vez de path aliases (`@/shared/logger`), contradizendo a Rule 2 da typescript-conventions.md escrita no Ex 2.3. |
| D4 — Pensamento Crítico | 3 | Justifica granularidade das tasks; explica o impacto real de parse vs safeParse (o atendente recebe "erro interno" sem saber que o problema é o input dele); explica por que console.log é invisível no Application Insights. |
| D5 — Aplicabilidade ao Projeto | 3 | Conecta explicitamente com o protótipo open-source do Ex 1.3 (Python + ChromaDB); explica como o protótipo motivou ADR-0002 e ADR-0003; ADR-0002 referenciada em comentário no handler.ts; TASK-007 cobre o cenário NovaTech-específico (PROC-042-v2 sobrepõe v1). |

**Score do exercício: 3.0**

### Verificação de Artefatos Machine-Readable
tasks.md tem critérios verificáveis por máquina (status HTTP, campos da resposta, paths de arquivo, anti-padrões explícitos como "Azure Functions v4 (`app.http(...)`, não `module.exports`)" e "Validação via `safeParse` (não `parse` que lança exceção)"). Um agente conseguiria usar tasks.md como input direto para implementação. Artefato aprovado.

### Pontos Fortes
1. Critérios de aceite da TASK-001 antecipam os anti-padrões do Copilot: o critério "Azure Functions v4 (`app.http(...)`, não `module.exports`)" foi criado a partir de observação real de geração, não de teoria.
2. A conexão com o Cenário 1 é substantiva: explica *por que* o protótipo Python motivou ADR-0002 e ADR-0003 com evidência empírica (respostas degradadas acima de 12K tokens, PROC-042-v1 retornado quando v2 era mais relevante).
3. Código de produção completo para TASK-001: todos os 5 arquivos implementados, sem stubs incompletos nos shared (types, errors, logger).

### Pontos de Melhoria
1. **Imports relativos no código:** handler.ts importa `'../../shared/logger.js'` com caminhos relativos — contradiz a Rule 2 da typescript-conventions.md ("nunca caminhos relativos com `../../`") escrita no mesmo ciclo. Esse inconsistência não foi capturada na revisão crítica.
2. **Duplicação de QueryRequest:** types.ts define `QueryRequest` como tipo plain; validator.ts também exporta `QueryRequest = z.infer<typeof QueryRequestSchema>`. Consolidar: usar apenas `z.infer` e remover o tipo duplicado de types.ts.
3. **Revisão crítica poderia incluir um terceiro problema:** a ausência de path aliases e a duplicação de QueryRequest são candidatos concretos com impacto real.

### Classificação
**Aprovado com distinção (3.0)**

---

## Avaliação do Exercício 2.3 — Estratégia de Skills do Projeto

### Resumo
Estratégia de skills coerente com o projeto: hierarquia Foundation → Domain → Artifact documentada, mapeamento de criação/consumo por papel com QA e PS como criadores (não só consumidores), e typescript-conventions.md prescritivo com exemplos de código do domínio NovaTech e anti-padrões reais do Copilot. A principal lacuna é a ausência de documentação explícita do processo iterativo com Copilot para a escrita da skill.

### Scores por Dimensão

| Dimensão | Score | Justificativa |
|----------|-------|---------------|
| D1 — Domínio Conceitual | 3 | Hierarquia Foundation → Domain → Artifact com semântica correta ("Foundation é consumida sempre; Domain é consumida em contexto específico"); distinção entre nível de seniority e domínio de conhecimento; typescript-conventions.md prescritivo com regras em imperativo, não narrativo. |
| D2 — Uso de Ferramentas | 2 | A skill typescript-conventions.md existe e tem qualidade alta, evidenciando trabalho real. Porém a evidência documenta *o que foi produzido* mas não o *processo* — sem prompts enviados, sem comparação v1 vs v2 da skill, sem registro de uso do Copilot. Regra de corte aplicada: "Evidência de uso de ferramenta ausente quando exigida → D2 ≤ 2." |
| D3 — Qualidade do Entregável | 3 | typescript-conventions.md é prescritivo: instrução de ativação direta ("Leia este arquivo antes de gerar qualquer arquivo `.ts`"), 5 regras DEVE em imperativo, 5 proibições explícitas, DO/DON'T com tipos do domínio NovaTech (QueryRequest, Chunk, vigencia), 6 anti-padrões com o código exato que o Copilot geraria. Arquivo no path correto: `skills/foundation/typescript-conventions.md`. |
| D4 — Pensamento Crítico | 3 | Justifica por que typescript-conventions é Foundation e testing-patterns é Domain com critério claro e não circular; justifica por que QA deve ser criador com argumento de domínio (quem sabe mockar Azure AI Search com msw, quem conhece os edge cases de chunk FAQ como não-normativo); insight sobre hierarquia de skills ≠ hierarquia de seniority. |
| D5 — Aplicabilidade ao Projeto | 3 | Anti-padrões citam comportamentos específicos do Copilot no contexto Azure Functions v4 (`module.exports` vs `app.http`); DO/DON'T usa `QueryRequest`, `Chunk`, `vigencia` como tipos do domínio; testing-patterns referencia msw, tests/fixtures/chunks.ts; paths seguem exatamente o Anexo C. |

**Score do exercício: 2.8**

### Verificação de Artefatos Machine-Readable
typescript-conventions.md é prescritivo e acionável: um agente consegue seguir as regras sem ambiguidade — as proibições citam o código exato a evitar, os exemplos DO mostram o padrão correto com o mesmo contexto. Não há linguagem narrativa ("deve-se considerar", "é recomendado") — as regras usam imperativo direto ("nunca", "sempre", "proibido"). Artefato aprovado.

### Pontos Fortes
1. typescript-conventions.md cita anti-padrões com o código que o Copilot realmente geraria neste projeto (ex: `module.exports` do Azure Functions v3, `parse()` sem `safeParse`) — não anti-padrões genéricos de TypeScript.
2. Insight estrutural correto: a hierarquia de skills mapeia para domínio de conhecimento, não para seniority. QA e PS como criadores de skills é uma decisão arquitetural justificada com impacto real na qualidade dos artefatos gerados.
3. Estratégia com frequência de uso documentada por skill (toda sessão de código, por função, por endpoint criado) — permite priorizar quais skills implementar primeiro.

### Pontos de Melhoria
1. **Sem evidência do processo iterativo:** a evidência documenta a estratégia e o resultado final, mas não o processo (prompts usados no Copilot ou Claude Chat, versões v1/v2 da skill, decisões tomadas durante a escrita). Documentar 2-3 prompts e uma iteração concreta elevaria D2 de 2 para 3.
2. **Conexão com AGENTS.md ausente:** o tópico do exercício inclui "AGENTS.md (como skills se conectam)" e a evidência não aborda como as skills seriam referenciadas ou ativadas a partir do AGENTS.md.
3. **Exemplos DO/DON'T poderiam incluir comentário inline na vigencia:** o campo `vigencia?: string` no tipo `Chunk` é central para a ADR-0003, mas o exemplo DO não explica o porquê do campo opcional. Um comentário `// ADR-0003: metadado de vigência` tornaria a skill autocontida.

### Classificação
**Aprovado com distinção (2.8)**

### Tópicos da Trilha para Reforço
Nenhum crítico. Para atingir 3.0: documentar processo iterativo com ferramentas (como na evidência do Ex 2.1, que transcreve tool calls).

---

## Artefatos avaliados

| Artefato | Exercício | Path |
|----------|-----------|------|
| Mapeamento MCP + evidência de uso | 2.1 | [ex-2.1-mcp-configuracao.md](ex-2.1-mcp-configuracao.md) |
| mcp.json final | 2.1 | `novatech-assistant/.mcp/mcp.json` |
| SDD + revisão crítica | 2.2 | [ex-2.2-sdd-tasks-e-revisao.md](ex-2.2-sdd-tasks-e-revisao.md) |
| plan.md | 2.2 | [ex-2.2-codigo-novatech/specs/query-endpoint/plan.md](ex-2.2-codigo-novatech/specs/query-endpoint/plan.md) |
| tasks.md | 2.2 | [ex-2.2-codigo-novatech/specs/query-endpoint/tasks.md](ex-2.2-codigo-novatech/specs/query-endpoint/tasks.md) |
| handler.ts | 2.2 | [ex-2.2-codigo-novatech/src/functions/query/handler.ts](ex-2.2-codigo-novatech/src/functions/query/handler.ts) |
| validator.ts | 2.2 | [ex-2.2-codigo-novatech/src/functions/query/validator.ts](ex-2.2-codigo-novatech/src/functions/query/validator.ts) |
| types.ts / errors.ts / logger.ts | 2.2 | [ex-2.2-codigo-novatech/src/shared/](ex-2.2-codigo-novatech/src/shared/) |
| Estratégia de skills | 2.3 | [ex-2.3-skills-estrategia.md](ex-2.3-skills-estrategia.md) |
| typescript-conventions.md | 2.3 | [ex-2.2-codigo-novatech/skills/foundation/typescript-conventions.md](ex-2.2-codigo-novatech/skills/foundation/typescript-conventions.md) |
