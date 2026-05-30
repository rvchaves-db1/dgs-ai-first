# Evidência — Ciclo de Testes Completo: Respostas do LLM

**Data:** 2026-05-30
**Modelo LLM:** Claude Sonnet 4.6 (via Claude Code)
**Modelo embedding:** paraphrase-multilingual-MiniLM-L12-v2
**Método:** Cada prompt gerado pelo pipeline submetido em conversa independente, sem contexto adicional.

Critérios de avaliação por resposta (baseados no system prompt v2 do exercício 1.2):
- **C1:** Citou fonte no formato correto?
- **C2:** Apresentou restrições com "ATENÇÃO:" quando aplicável?
- **C3:** Inventou valor, prazo ou procedimento ausente nos chunks?
- **C4:** Resposta final correta do ponto de vista do atendente?

---

## Teste 1 — "Qual o prazo de devolução?"

**Retrieval:** FULL (POL-001 §3.1 recuperado)
**Armadilha:** Regra geral (7 dias) vs. exceção (cargas perigosas NÃO podem devolver)

**Resposta do LLM:**
> O prazo de devolução é de **7 (sete) dias úteis** contados a partir da data de recebimento
> confirmada no sistema de tracking. [Fonte: POL-001-politica-devolucao.md, seção 3.1]
>
> A contagem considera apenas dias úteis, excluindo sábados, domingos e feriados nacionais.
> [Fonte: POL-001-politica-devolucao.md, seção 3.1]
>
> ATENÇÃO: A data de início da contagem é a data de recebimento **confirmada no sistema de
> tracking**, não a data estimada de entrega.

**Gabarito esperado:** 7 dias úteis (§3.1) + exceção para cargas perigosas NÃO elegíveis (§3.2)

**Avaliação por critério:**
| Critério | Resultado | Observação |
|---|---|---|
| C1 — Citou fonte? | ✅ Sim | POL-001 §3.1 corretamente citado |
| C2 — ATENÇÃO quando aplicável? | ⚠️ Parcial | ATENÇÃO usado, mas sobre detalhe menor (data tracking), não sobre a exceção principal |
| C3 — Inventou informação? | ✅ Não | Sem alucinação |
| C4 — Resposta correta? | ⚠️ Parcial | Correto para a regra geral; ausente a exceção de carga perigosa |

**Veredito: PARCIAL**
**Causa raiz:** §3.2 (exceções) não foi recuperado pelo retrieval. O LLM respondeu corretamente com o que recebeu. Falha de retrieval, não de geração.

---

## Teste 2 — "Posso devolver carga perigosa?"

**Retrieval:** SOURCE_ONLY (POL-001 encontrado mas seção §3.2 ausente)
**Armadilha:** Resposta correta é NÃO — carga perigosa NÃO é elegível para devolução padrão

**Resposta do LLM:**
> A documentação disponível não detalha o processo de devolução específico para cargas
> perigosas, mas há restrições e informações parciais relevantes.
>
> ATENÇÃO: Cargas perigosas seguem regras específicas documentadas na PROC-043: Frete de
> Cargas Perigosas. Essa documentação **está atualmente em processo de revisão pelo Compliance**.
> [Fonte: PROC-042-v2-frete-especial-revisado.md, Seção 4]
>
> ATENÇÃO: Qualquer irregularidade de documentação ou rastreamento envolvendo carga perigosa
> é classificada como **incidente crítico**. [Fonte: SLA-2024-tabela-sla-clientes.md, Seção 3]
>
> Quanto à política geral de devolução, os custos seguem a seguinte lógica:
> - Defeito ou erro da NovaTech: devolução sem custo para o cliente.
> - Desistência do cliente: o custo do frete reverso é do cliente.
> - Prazo expirado (após 7 dias úteis): não elegível para devolução padrão.
> [Fonte: POL-001-politica-devolucao.md, Seção 3.5]
>
> Recomendação: Escale para o supervisor ou consulte a área de Compliance.

**Gabarito esperado:** "ATENÇÃO: Cargas perigosas NÃO são elegíveis para devolução pelo
processo padrão. Contate Gestão de Riscos pelo ramal 4500." [Fonte: POL-001 §3.2]

**Avaliação por critério:**
| Critério | Resultado | Observação |
|---|---|---|
| C1 — Citou fonte? | ✅ Sim | Fontes citadas corretamente |
| C2 — ATENÇÃO quando aplicável? | ⚠️ Parcial | ATENÇÃO usado para PROC-043 e incidente crítico, mas não para a regra de exclusão |
| C3 — Inventou informação? | ✅ Não | Sem alucinação; aplicou §3.5 (custos gerais) corretamente |
| C4 — Resposta correta? | ❌ Não | Não afirma que carga perigosa NÃO é elegível; pode induzir o atendente a aplicar regra geral de custos |

**Veredito: INCORRETO**
**Causa raiz:** §3.2 (regra de exclusão explícita) não foi recuperado. O LLM aplicou corretamente as regras que recebeu, mas sem o chunk crítico não pôde dar a resposta correta. A resposta gerada é perigosa: sugere que o processo geral de custos (§3.5) pode se aplicar, o que é falso para cargas perigosas.
**Tipo de falha:** Falha de retrieval (§3.2 ausente) com risco de resposta enganosa pelo LLM.

---

## Teste 3 — "Qual o SLA do cliente Gold?"

**Retrieval:** SOURCE_ONLY (SLA-2024 encontrado mas §2 com valores reais ausente)
**Armadilha:** Omitir SLA de incidentes críticos (4h). Resposta completa menciona chamados gerais E críticos.

**Resposta do LLM:**
> Não encontrei essa informação na documentação disponível. Por favor, escale para o
> supervisor ou consulte a área responsável.
>
> Os documentos recuperados contêm a **classificação e critérios de elegibilidade** para
> o tier Gold [Fonte: SLA-2024-tabela-sla-clientes.md, Seção 1], mas não incluem os
> prazos ou indicadores de SLA associados a esse tier.
>
> ATENÇÃO: Para referência, o tier Gold é atribuído a clientes com contrato anual acima
> de R$ 500.000 ou mais de 200 operações/mês, com revisão semestral.
> [Fonte: SLA-2024-tabela-sla-clientes.md, Seção 1]
>
> Recomendo consultar o documento SLA-2024-tabela-sla-clientes.md em sua versão integral.

**Gabarito esperado:** Gold: resposta 2h úteis, resolução 24h úteis; incidentes críticos: 4h
(sem pausa fora do horário comercial). [Fonte: SLA-2024 §2]

**Avaliação por critério:**
| Critério | Resultado | Observação |
|---|---|---|
| C1 — Citou fonte? | ✅ Sim | SLA-2024 §1 corretamente citado |
| C2 — ATENÇÃO quando aplicável? | ✅ Sim | ATENÇÃO usado para contexto adicional |
| C3 — Inventou informação? | ✅ Não | LLM recusou inventar os valores de SLA — comportamento correto |
| C4 — Resposta correta? | ⚠️ Parcial | O atendente não recebeu os valores de SLA; escalou corretamente em vez de alucinar |

**Veredito: PARCIAL**
**Nota importante:** O comportamento do LLM foi exemplar — aplicou a Regra 5 (escalada quando sem informação) em vez de inventar "2h/24h". O falso negativo é inteiramente de retrieval (§2 com os valores não foi recuperado). Em produção, esse comportamento é preferível à alucinação de valores contratuais de SLA.

---

## Teste 4 — "Qual o custo do frete para 600kg para Manaus?"

**Retrieval:** FULL (PROC-042-v2 §2 recuperado)
**Armadilha:** Misturar versões v1/v2 (Norte = 1.6 v1 vs 1.8 v2) e não inventar valor base ausente

**Resposta do LLM:**
> O frete especial para 600 kg com destino a Manaus é calculado pela fórmula:
>
> **Valor do frete = Valor base × Multiplicador regional × Fator de peso**
>
> Para 600 kg, o fator de peso aplicável é **1,0** (faixa de 500kg a 1.000kg).
> [Fonte: PROC-042-v2-frete-especial-revisado.md, Seção 2]
>
> No entanto, **não é possível concluir o cálculo** com as informações disponíveis, pois faltam:
> 1. **Valor base**: tarifa da tabela mensal de fretes — consultar tabela vigente.
> 2. **Multiplicador regional**: fator para Manaus (região Norte) — consultar seção 2.1 do
>    PROC-042-v2. [Fonte: PROC-042-v2-frete-especial-revisado.md, Seção 2]
>
> Para concluir o atendimento, obtenha os dois valores e aplique a fórmula.

**Gabarito esperado:** Fórmula + fator de peso 1.0 (500-1000kg) + multiplicador Norte 1.8
(v2) + ATENÇÃO sobre valor base ausente. Não usar Norte 1.6 (v1).

**Avaliação por critério:**
| Critério | Resultado | Observação |
|---|---|---|
| C1 — Citou fonte? | ✅ Sim | PROC-042-v2 §2 citado corretamente |
| C2 — ATENÇÃO quando aplicável? | ✅ Sim | Resposta parcial estruturada com clareza |
| C3 — Inventou informação? | ✅ Não | Não inventou o multiplicador regional nem o valor base |
| C4 — Resposta correta? | ✅ Sim | Regra 6 aplicada perfeitamente; fator de peso correto; v1 não usado |

**Veredito: CORRETO**
**Nota:** §2.1 (multiplicadores regionais com Norte=1.8) não estava no contexto, mas o LLM
corretamente apontou que o multiplicador precisa ser consultado em §2.1. Não inventou 1.8
nem 1.6. Comportamento correto dado o contexto.

---

## Teste 5 — "Qual o SLA do cliente Platinum?"

**Retrieval:** FULL (FAQ Item 15 + SLA Introdução recuperados)
**Armadilha:** Tier Platinum não existe — não inventar SLAs

**Resposta do LLM:**
> **Não existe o tier "Platinum" na NovaTech.**
>
> ATENÇÃO: O nível "Platinum" não faz parte da estrutura de tiers atual da empresa. Se o
> cliente mencionar esse tier, é provável que esteja confundindo com outra transportadora ou
> com o programa de fidelidade antigo, que foi descontinuado em 2022.
> [Fonte: FAQ-atendimento.md, Item 15]
>
> Os tiers vigentes na NovaTech são: **Gold**, **Silver** e **Standard**.
>
> Oriente o cliente a verificar seu tier correto e solicite o número do contrato para
> consulta. [Fonte: FAQ-atendimento.md, Item 15]

**Gabarito esperado:** Platinum não existe, tiers são Gold/Silver/Standard, não inventar SLAs.

**Avaliação por critério:**
| Critério | Resultado | Observação |
|---|---|---|
| C1 — Citou fonte? | ✅ Sim | FAQ Item 15 citado corretamente |
| C2 — ATENÇÃO quando aplicável? | ✅ Sim | ATENÇÃO na primeira afirmação relevante |
| C3 — Inventou informação? | ✅ Não | Não criou SLAs para Platinum |
| C4 — Resposta correta? | ✅ Sim | Tier inexistente identificado corretamente |

**Veredito: CORRETO**

---

## Tabela-resumo final

| # | Pergunta | Retrieval | C1 Fonte | C2 ATENÇÃO | C3 Sem invenção | C4 Correto | Veredito |
|---|---|---|---|---|---|---|---|
| 1 | Prazo de devolução? | FULL | ✅ | ⚠️ | ✅ | ⚠️ | **PARCIAL** |
| 2 | Devolver carga perigosa? | SOURCE_ONLY | ✅ | ⚠️ | ✅ | ❌ | **INCORRETO** |
| 3 | SLA cliente Gold? | SOURCE_ONLY | ✅ | ✅ | ✅ | ⚠️ | **PARCIAL** |
| 4 | Frete 600kg Manaus? | FULL | ✅ | ✅ | ✅ | ✅ | **CORRETO** |
| 5 | SLA cliente Platinum? | FULL | ✅ | ✅ | ✅ | ✅ | **CORRETO** |

**Resultado end-to-end: 2/5 corretos, 2/5 parciais, 1/5 incorreto**

---

## Análise consolidada

### O que o pipeline acertou
- **Zero alucinações** em todos os 5 testes — o LLM nunca inventou valores, prazos ou tiers.
- **Comportamento defensivo correto:** quando o contexto era insuficiente (Teste 3), o LLM
  escalou em vez de inventar. Criticamente diferente de alucinar "2h/24h para Gold".
- **Versão correta usada:** Teste 4 não misturou v1/v2 — a deduplicação funcionou.
- **Trap do Platinum resolvida:** Teste 5 completamente correto.

### Onde o pipeline falhou
- **Teste 2 (carga perigosa):** Falha crítica — a pergunta mais importante do ponto de vista
  de segurança operacional. O chunk §3.2 (regra de exclusão) ainda não é recuperado com o
  modelo multilingual. Causa: semanticamente, "posso devolver carga perigosa?" não se
  aproxima do texto "não são elegíveis para devolução pelo processo padrão".
- **Teste 1 (prazo geral):** Correto para regra, mas incompleto — a exceção do §3.2 faz
  parte do gabarito e não veio no contexto.
- **Teste 3 (SLA Gold):** Falha de retrieval (§2 ausente) resultando em escalada correta mas
  sem informação útil para o atendente.

### Conclusão sobre o critério ≥3/5 do rubric
Ao nível de **comportamento do LLM** (seguiu as regras do system prompt?): **5/5** — zero
infrações de regras, zero alucinações.
Ao nível **end-to-end** (atendente recebeu resposta correta?): **2/5** — abaixo do critério.

O gargalo é retrieval, não geração. A solução de médio prazo para Teste 2 é HyDE
(Hypothetical Document Embeddings): gerar uma resposta hipotética para a pergunta e usar
como query de busca, aproximando-se do texto "não são elegíveis" sem depender da pergunta
literal.
