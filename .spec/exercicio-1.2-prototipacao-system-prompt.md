# Exercício 1.2 — Prototipação de Prompt com Engenharia de Contexto

**Participante:** Rafael Chaves  
**Papel:** Desenvolvedor  
**Data:** 2026-05-30

---

## System Prompt v1 (base fornecida pelo enunciado)

```
Você é o assistente de atendimento da NovaTech, empresa de logística.
Responda perguntas sobre procedimentos, SLAs e regras de frete.
Use apenas as informações dos documentos fornecidos.
Cite a fonte. Se não souber, diga que não sabe.
```

---

## Mapeamento: contexto estático vs. dinâmico

| Parte do contexto | Tipo | Tamanho estimado |
|---|---|---|
| System prompt (identidade, regras, formato) | Estático | ~500–800 tokens |
| Guardrails de comportamento | Estático | ~200 tokens |
| Metadados do cliente (tier, número do contrato) | Dinâmico por sessão | ~100 tokens |
| Chunks recuperados do vector store | Dinâmico por query | ~2.500–5.000 tokens |
| Pergunta do atendente | Dinâmico por query | ~30–150 tokens |
| Histórico de conversa | Dinâmico, crescente | ~500 tokens/turno |

**Total típico por query:** ~4.000–7.000 tokens (excluindo histórico longo).

---

## Testes com prompt v1

Chunks injetados no contexto:
- **Chunk POL-001-B** — Seção 3.2: exceções à devolução (cargas perigosas)
- **Chunk SLA-2024-B** — Seção 2: SLAs para chamados gerais
- **Chunk PROC-042v2-B** — Seção 2.1: multiplicadores regionais atualizados

---

### Pergunta 1: "Qual o prazo de devolução para carga perigosa?"

**Comportamento esperado:** Informar que cargas perigosas classes 1–6 da ANTT **NÃO** são elegíveis para devolução pelo processo padrão. Indicar Gestão de Riscos (ramal 4500).

**Falha do prompt v1:** Sem instrução explícita para tratar exceções como resposta primária, o modelo tende a apresentar a regra geral (7 dias úteis) primeiro e a restrição como adendo. Um atendente pode interpretar como "pode devolver em 7 dias, com ressalva" em vez de "não pode devolver pelo processo padrão".

**Falha identificada:** Ausência de instrução para priorizar exceções/restrições quando aplicáveis.

---

### Pergunta 2: "Meu cliente é Gold, qual o SLA de resolução?"

**Comportamento esperado:** Apresentar SLA de chamados gerais (24h) e SLA de incidentes críticos (4h), com citação de fonte.

**Falha do prompt v1:** O prompt não instrui o modelo a distinguir os dois tipos de SLA. A resposta provavelmente informa apenas o SLA geral (24h), omitindo o SLA crítico (4h) — informação relevante para o atendente.

**Falha identificada:** Falta instrução para apresentar informações complementares quando a pergunta é ambígua quanto ao escopo.

---

### Pergunta 3: "Quanto custa o frete para 600kg para Manaus?"

**Comportamento esperado:** Informar o multiplicador (1.8, região Norte) e o fator de peso (1.0), explicar que o valor base não está disponível no contexto e indicar onde encontrá-lo.

**Falha do prompt v1:** "Use apenas os documentos fornecidos" não é específico o suficiente sobre o que fazer quando a resposta é parcial. O modelo pode tentar inventar um valor base para completar o cálculo.

**Falha identificada:** Falta instrução explícita para respostas parciais (fórmula existe, dado de entrada ausente).

---

## System Prompt v2 (iterado)

```
## Identidade
Você é o Assistente de Atendimento da NovaTech, empresa de logística.
Seu papel é ajudar os atendentes a responderem dúvidas de clientes com
base exclusivamente na documentação oficial fornecida.

## Regras obrigatórias (sem exceção)
1. Use APENAS informações presentes nos documentos fornecidos abaixo.
2. Cite SEMPRE a fonte (nome do documento e seção) ao final de cada
   informação fornecida. Formato: [Fonte: NOME-DO-DOC, seção X.X]
3. Nunca invente prazos, valores numéricos ou procedimentos que não
   estejam explicitamente nos documentos.
4. Se uma pergunta tiver como resposta principal uma EXCEÇÃO ou
   RESTRIÇÃO, apresente a restrição primeiro, antes de qualquer regra
   geral. Exemplo: se a carga não é elegível para devolução, diga isso
   claramente na primeira frase.
5. Se a informação não estiver nos documentos fornecidos, responda
   exatamente: "Não encontrei essa informação na documentação disponível.
   Por favor, escale para o supervisor ou consulte diretamente a área
   responsável."
6. Quando a resposta for parcial (você tem a fórmula mas não o dado de
   entrada), apresente o que tem e indique explicitamente o que está
   faltando para completar o cálculo.
7. Quando existirem duas versões de um mesmo documento nos chunks
   fornecidos, priorize a versão com data mais recente e informe ao
   atendente que existe uma versão anterior.
8. Ao usar informação de um documento com versão mais recente, deixe
   explícito no texto qual versão está sendo usada e que existe uma
   versão anterior com valores diferentes. Use o formato:
   "Conforme [DOC] v[X] ([mês/ano]) [Fonte: ...]. Nota: existe versão
   anterior (v[Y]) com valores diferentes — confirme que o contrato do
   cliente referencia a versão vigente."
9. Responda em português formal e acessível. Evite jargão técnico sem
   explicação.

## Formato de resposta
- Resposta direta na primeira linha.
- Detalhes e contexto nos parágrafos seguintes, se necessário.
- Fonte entre colchetes ao final de cada afirmação factual.
- Se houver restrição ou exceção relevante, destacar com "ATENÇÃO:".

## Documentos fornecidos
{chunks_recuperados}

## Pergunta do atendente
{pergunta}
```

---

## Reteste com prompt v2

### Pergunta 1: "Qual o prazo de devolução para carga perigosa?"

**Resposta esperada com v2:**
> ATENÇÃO: Cargas perigosas classificadas nas classes 1 a 6 da ANTT **não são elegíveis** para devolução pelo processo padrão. [Fonte: POL-001, seção 3.2]
>
> O cliente deve entrar em contato com o setor de Gestão de Riscos pelo ramal 4500 para tratamento individual.

**Melhoria:** A instrução de apresentar exceções primeiro (regra 4) e o uso de "ATENÇÃO:" eliminam a ambiguidade da v1. O atendente recebe a informação crítica na primeira linha.

---

### Pergunta 2: "Meu cliente é Gold, qual o SLA de resolução?"

**Resposta esperada com v2:**
> Para clientes Gold, os SLAs de resolução são:
> - Chamados gerais: até **24 horas úteis**. [Fonte: SLA-2024, seção 2]
> - Incidentes críticos: até **4 horas** (sem pausa fora do horário comercial). [Fonte: SLA-2024, seção 2]
>
> Para verificar se um chamado é incidente crítico, consulte os critérios em SLA-2024, seção 3.

**Melhoria:** O formato estruturado do v2 induz o modelo a apresentar ambas as modalidades de SLA, eliminando a omissão da v1.

---

### Pergunta 3: "Quanto custa o frete para 600kg para Manaus?"

**Resposta esperada com v2:**
> Para cargas acima de 500kg com destino à região Norte, aplica-se:
> - Multiplicador regional: **1.8** [Fonte: PROC-042-v2, seção 2.1]
> - Fator de peso (faixa 500–1.000kg): **1.0** [Fonte: PROC-042-v2, seção 2]
>
> Fórmula: Valor do frete = Valor base × 1.8 × 1.0
>
> ATENÇÃO: O valor base é a tarifa publicada na tabela mensal de fretes (`frete-base-AAAAMM.xlsx`), que não está disponível neste contexto. Para obter o valor final, consulte a tabela do mês atual no servidor de arquivos da NovaTech.

**Melhoria:** A regra 6 (resposta parcial) elimina a tentação de inventar o valor base. O atendente recebe exatamente o que está documentado e sabe o que precisa buscar para completar o cálculo.

---

### Pergunta 4: "Qual o multiplicador para a região Norte?" *(teste da Regra 8)*

**Chunks injetados no contexto (ambas as versões):**
- **Chunk PROC-042-v1 §2.1** — "Multiplicadores regionais: Norte 1.6, Sudeste 1.0, Sul 1.2..."
- **Chunk PROC-042-v2 §2.1** — "Multiplicadores regionais atualizados (nov/2023): Norte 1.8, Sudeste 1.1..."

**Comportamento esperado com v2:**
> Conforme PROC-042 v2 (nov/2023), o multiplicador regional para a região Norte é **1.8**.
> [Fonte: PROC-042-v2-frete-especial-revisado.md, seção 2.1]
>
> Nota: existe versão anterior (v1) com multiplicador Norte = 1.6 — confirme que o contrato
> do cliente referencia a versão vigente antes de calcular.

**Melhoria:** A Regra 8 instrui o modelo a citar a versão explicitamente e alertar sobre a
existência da versão anterior com valores diferentes. Sem essa regra, o modelo poderia usar
v2 silenciosamente sem avisar o atendente sobre a discrepância — risco real no contrato
NovaTech onde v1 e v2 coexistem no SharePoint sem hierarquia formal.

---

## Análise comparativa v1 vs. v2

| Critério | v1 | v2 |
|---|---|---|
| Especificidade das regras | Genérico ("use apenas os documentos") | Regras numeradas e explícitas para cada caso-limite |
| Tratamento de exceções | Não instruído — modelo decide a ordem | Instrução explícita: restrições primeiro (Regra 4) |
| Respostas parciais | Risco de alucinação para completar | Regra 6: apresentar o que tem + indicar o que falta |
| Documentos contraditórios | Não endereçado | Regra 7 + 8: priorizar recente, citar versão, alertar sobre anterior |
| Formato de saída | Livre | Estruturado com "ATENÇÃO:", fontes em colchetes |
| Fallback (sem resposta) | "diga que não sabe" | Texto exato prescrito para consistência (Regra 5) |
