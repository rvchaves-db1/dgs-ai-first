# Evidência — Ex 2.3: Estratégia de Skills

## 1. Árvore de skills do projeto

```
novatech-assistant/skills/
│
├── foundation/                          # Convenções globais — lidas antes de qualquer outra skill
│   ├── typescript-conventions.md        # ✅ Implementada (Dev — Ex 2.3)
│   ├── error-handling.md                # Tech Lead — fase futura
│   └── project-structure.md            # Tech Lead — fase futura
│
├── domain/                              # Padrões por camada técnica
│   ├── azure-functions-endpoint.md      # Tech Lead — Ex 2.3 do papel TL
│   ├── azure-ai-search-integration.md   # Dev Sênior — fase futura
│   ├── react-components.md              # Tech Lead — fase futura
│   └── testing-patterns.md             # QA — Ex 2.3 do papel QA
│
└── artifact/                            # Receitas completas de geração de artefatos
    ├── create-rag-endpoint.md           # Tech Lead + Dev Sênior — fase futura
    ├── create-integration-test.md       # QA — Ex 2.3 do papel QA
    └── create-react-card.md             # Tech Lead — fase futura
```

**Hierarquia de leitura:** Foundation → Domain → Artifact. Uma skill de artefato pressupõe que as skills de foundation e domain relevantes já foram lidas. Ex: `create-rag-endpoint` pressupõe `typescript-conventions`, `error-handling` e `azure-functions-endpoint`.

---

## 2. Mapeamento criação/consumo por papel

| Skill | Cria | Consome (Papéis) | Consome (Agentes) | Freq. de uso |
|-------|------|------------------|-------------------|-------------|
| `typescript-conventions` | **Dev (Ex 2.3)** | Dev, QA, TL | Copilot, Claude Code | Toda sessão de código `.ts` |
| `error-handling` | Tech Lead | Dev | Copilot | Por função que pode falhar |
| `project-structure` | Tech Lead | Dev, QA | Copilot | Onboarding + novas pastas |
| `azure-functions-endpoint` | Tech Lead | Dev | Copilot | Por endpoint criado |
| `azure-ai-search-integration` | Dev Sênior | Dev | Copilot | Por integração de busca |
| `react-components` | Tech Lead | Dev (frontend) | Copilot | Por componente criado |
| `testing-patterns` | **QA** | Dev, QA | Copilot, Claude Code | Por test suite |
| `create-rag-endpoint` | TL + Dev Sênior | Dev Pleno | Copilot | Por endpoint RAG novo |
| `create-integration-test` | **QA** | Dev, QA | Copilot | Por módulo testado |
| `create-react-card` | Tech Lead | Dev (frontend) | Copilot | Por card no painel |
| Spec SDD template | **Product Specialist** | PS, TL, Dev | Claude Code | Por módulo especificado |

---

## 3. Raciocínio das escolhas

### Por que QA e PS são criadores, não só consumidores?

**QA como criador de `testing-patterns` e `create-integration-test`:**

Patterns de teste para este projeto não são genéricos — incluem detalhes específicos do domínio: como mockar o Azure AI Search com msw, como usar os fixtures de `tests/fixtures/chunks.ts`, como testar o tratamento de documentos contraditórios (PROC-042-v1 vs v2). O QA é o único papel que sabe quais cenários de borda importam para a NovaTech (ex: chunk de FAQ como fonte não-normativa, pergunta sobre tier Platinum que não existe). Se um dev escrevesse essas skills, resultariam em convenções técnicas sem cobertura dos edge cases de negócio.

**Product Specialist como criador do Spec SDD template:**

O template de spec (requirements.md + plan.md + tasks.md) define o formato que o PS usa para especificar novos módulos. Se o Dev ou TL definissem o template, ele seria otimizado para o que o dev quer ler — não para o que o PS precisa escrever. O PS sabe quais campos são necessários para que o TL possa criar um plan sem ambiguidade, e quais critérios de aceite são verificáveis pela QA.

**Insight:** a hierarquia de skills não mapeia para a hierarquia de seniority — ela mapeia para quem tem o conhecimento de domínio específico. QA tem conhecimento de teste; PS tem conhecimento de spec; o Dev tem conhecimento de convenções de código.

### Por que `typescript-conventions` é Foundation (não Domain)?

Porque se aplica a **todos** os arquivos `.ts` do projeto, independente da camada: handler, service, test, pipeline. Uma skill Domain como `azure-functions-endpoint` é consumida apenas quando alguém está criando um endpoint — `typescript-conventions` é consumida sempre. Ela é o substrato sobre o qual todas as outras skills se apoiam.

### Por que `testing-patterns` é Domain (não Foundation)?

Porque é específica para a camada de testes, não para todo o código TypeScript. Um dev escrevendo um serviço de busca não precisa ler `testing-patterns` — mas um dev escrevendo os testes desse serviço precisa. Domain significa "consumido em contexto específico", não "menos importante".

---

## 4. SKILL.md implementado

O arquivo `novatech-assistant/skills/foundation/typescript-conventions.md` foi criado com a seguinte estrutura:

- **Ativação:** "Leia este arquivo antes de gerar qualquer arquivo `.ts` no projeto."
- **Contexto:** explica por que a skill existe — anti-padrões reais que o Copilot gera.
- **Regras DEVE:** 5 regras prescritivas (strict, path aliases, naming, try/catch, pino).
- **Proibições NÃO DEVE:** 5 proibições com exemplos do que exatamente proibir.
- **Exemplos DO/DON'T:** usa tipos do domínio NovaTech (`QueryRequest`, `Chunk`, `QueryRequestSchema`).
- **Anti-padrões do Copilot:** 6 anti-padrões que o Copilot realmente gera neste projeto (ex: `module.exports` em vez de `app.http`, `parse` em vez de `safeParse`).
- **Dependências:** nenhuma — é Foundation.

Referência: [`novatech-assistant/skills/foundation/typescript-conventions.md`](../../../novatech-assistant/skills/foundation/typescript-conventions.md)
