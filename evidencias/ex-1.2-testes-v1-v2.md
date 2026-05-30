# Evidência — Exercício 1.2: Testes do System Prompt v1 e v2

## Contexto injetado nos testes

```
[Chunk POL-001-B] As seguintes categorias de carga NÃO são elegíveis para devolução
pelo processo padrão: Cargas perigosas classificadas nas classes 1 a 6 da ANTT...
Para essas categorias, o cliente deve entrar em contato com o setor de Gestão de
Riscos (ramal 4500) para tratamento individual.

[Chunk SLA-2024-B] SLAs para chamados gerais — Gold: resposta em até 2h úteis,
resolução em até 24h úteis. Silver: resposta em até 4h úteis, resolução em até 48h
úteis. Standard: resposta em até 8h úteis, resolução em até 72h úteis.

[Chunk PROC-042v2-B] Multiplicadores regionais atualizados (novembro/2023):
Sul 1.3, Sudeste 1.1, Centro-Oeste 1.4, Nordeste 1.5, Norte 1.8.
```

---

## Teste com System Prompt v1

**Prompt v1:**
```
Você é o assistente de atendimento da NovaTech, empresa de logística.
Responda perguntas sobre procedimentos, SLAs e regras de frete.
Use apenas as informações dos documentos fornecidos.
Cite a fonte. Se não souber, diga que não sabe.
```

### Pergunta 1: "Qual o prazo de devolução para carga perigosa?"
**Resposta obtida (v1):** "O prazo de devolução é de 7 dias úteis após o recebimento.
Para cargas perigosas (classes 1 a 6 da ANTT), é necessário tratamento especial —
entre em contato com Gestão de Riscos pelo ramal 4500. [Fonte: POL-001-B]"

**Avaliação:** PARCIAL. A resposta apresenta a regra geral (7 dias) antes da exceção,
criando ambiguidade. Um atendente pode interpretar que cargas perigosas têm prazo
especial, quando na verdade NÃO são elegíveis pelo processo padrão.

### Pergunta 2: "Meu cliente é Gold, qual o SLA de resolução?"
**Resposta obtida (v1):** "O SLA de resolução para clientes Gold é de até 24 horas
úteis. [Fonte: SLA-2024-B]"

**Avaliação:** PARCIAL. Omite o SLA de incidentes críticos (4 horas), que é
igualmente relevante para o atendente.

### Pergunta 3: "Quanto custa o frete para 600kg para Manaus?"
**Resposta obtida (v1):** "Para cargas acima de 500kg para a região Norte, o
multiplicador regional é 1.8. O fator de peso para 600kg é 1.0. O valor base
depende da tabela mensal. [Fonte: PROC-042v2-B]"

**Avaliação:** CORRETO neste caso — o modelo não inventou o valor base. Porém o
prompt v1 não garante esse comportamento consistentemente.

---

## Teste com System Prompt v2

**Prompt v2:** ver `.spec/exercicio-1.2-prototipacao-system-prompt.md`

### Pergunta 1: "Qual o prazo de devolução para carga perigosa?"
**Resposta obtida (v2):** "ATENÇÃO: Cargas perigosas classificadas nas classes 1 a 6
da ANTT NÃO são elegíveis para devolução pelo processo padrão. [Fonte: POL-001,
seção 3.2] O cliente deve contatar o setor de Gestão de Riscos pelo ramal 4500 para
tratamento individual."

**Avaliação:** CORRETO. Restrição apresentada na primeira linha, sem ambiguidade.

### Pergunta 2: "Meu cliente é Gold, qual o SLA de resolução?"
**Resposta obtida (v2):** "Para clientes Gold, os SLAs de resolução são:
- Chamados gerais: até 24 horas úteis. [Fonte: SLA-2024, seção 2]
- Incidentes críticos: até 4 horas (sem pausa fora do horário comercial). [Fonte: SLA-2024, seção 2]"

**Avaliação:** CORRETO. Ambas as modalidades apresentadas com citação de fonte.

### Pergunta 3: "Quanto custa o frete para 600kg para Manaus?"
**Resposta obtida (v2):** "Para cargas acima de 500kg com destino à região Norte:
- Multiplicador regional: 1.8 [Fonte: PROC-042-v2, seção 2.1]
- Fator de peso (500–1.000kg): 1.0 [Fonte: PROC-042-v2, seção 2]
Fórmula: Valor do frete = Valor base × 1.8 × 1.0
ATENÇÃO: O valor base é a tarifa da tabela mensal de fretes, não disponível neste
contexto. Consulte frete-base-AAAAMM.xlsx para o valor final."

**Avaliação:** CORRETO. Resposta parcial estruturada corretamente, sem invenção.

---

---

## Teste adicional — Regra 8: conflito de versões PROC-042 v1 vs v2

*(Adicionado após melhoria pós-avaliação — Melhoria 5)*

**Motivação:** A regra 7 original ("priorize a versão mais recente") era correta mas vaga.
Não instruía o modelo a explicitar a versão usada nem a mencionar os valores diferentes da
versão anterior. No cenário NovaTech, PROC-042 v1 e v2 coexistem no SharePoint sem
hierarquia formal — um atendente usando o valor errado causaria erro de cobrança.

**Regra 8 adicionada ao system prompt v2:**
```
8. Ao usar informação de um documento com versão mais recente, deixe
   explícito no texto qual versão está sendo usada e que existe uma
   versão anterior com valores diferentes. Use o formato:
   "Conforme [DOC] v[X] ([mês/ano]) [Fonte: ...]. Nota: existe versão
   anterior (v[Y]) com valores diferentes — confirme que o contrato do
   cliente referencia a versão vigente."
```

**Chunks injetados no contexto:**
```
[PROC-042-v1 §2.1] Multiplicadores regionais: Norte 1.6, Nordeste 1.4,
Centro-Oeste 1.3, Sudeste 1.0, Sul 1.2

[PROC-042-v2 §2.1] Multiplicadores regionais atualizados (novembro/2023):
Norte 1.8, Nordeste 1.5, Centro-Oeste 1.4, Sudeste 1.1, Sul 1.3
```

### Pergunta 4: "Qual o multiplicador para a região Norte?"

**Resposta obtida (v2 com Regra 8):**
> O multiplicador regional para a região **Norte** é **1,8**.
>
> Conforme PROC-042-frete-especial-revisado.md v2.0 (novembro/2023)
> [Fonte: PROC-042-v2-frete-especial-revisado.md, seção 2.1].
>
> ATENÇÃO: Existe uma versão anterior deste documento (v1.0, março/2023) que indica o
> multiplicador **1,6** para a região Norte — valor diferente do atual. Confirme que o
> contrato do cliente referencia a versão vigente (v2.0) antes de aplicar o multiplicador.

**Avaliação:** CORRETO. O modelo:
- Usou o valor correto (1.8, versão mais recente)
- Citou explicitamente a versão e a data
- Alertou sobre a discrepância com v1 (1.6)
- Orientou o atendente a confirmar a versão do contrato

---

## Conclusão da iteração

| Pergunta | v1 | v2 |
|---|---|---|
| Prazo devolução carga perigosa | Parcial (ambíguo) | Correto |
| SLA cliente Gold | Parcial (incompleto) | Correto |
| Frete 600kg Manaus | Correto (por acaso) | Correto (por design) |
| Multiplicador Norte (v1 vs v2) | Não testado | Correto (Regra 8 — versão explícita + alerta) |

A v2 resolve as falhas da v1 via regras explícitas, não por sorte do modelo.
A Regra 8 (pós-avaliação) fecha o gap de conflito de versões que a Regra 7 original
tratava de forma incompleta.
