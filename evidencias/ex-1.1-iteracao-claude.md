# Evidência — Exercício 1.1: Iteração com Claude

## Prompt 1 (análise inicial)

**Contexto fornecido ao Claude:**
> Cenário completo da NovaTech + tabela de fontes (SharePoint, Confluence, planilhas).
> Informações técnicas adicionais sobre tipos de documento (PDFs com tabelas complexas,
> PDFs escaneados, wiki com links, planilhas com fórmulas).
> Conceito de context engineering aplicado a RAG (lost in the middle, orçamento de atenção).

**Prompt enviado:**
> "Produza uma análise técnica cobrindo: desafios de cada tipo de fonte para o pipeline de RAG,
> estimativa do tamanho da base em tokens, análise de orçamento de contexto por query, e
> recomendação de estratégia de chunking justificada pelo tipo de pergunta e pelo efeito
> lost in the middle."

**Output:** ver `.spec/exercicio-1.1-analise-viabilidade-tecnica.md` — seção "Rodada 1".

---

## Prompt 2 (revisão crítica)

**Prompt enviado:**
> "Revise a análise técnica acima. Identifique pontos fracos, estimativas otimistas demais
> ou riscos que não foram considerados."

**Pontos levantados pelo Claude:**
1. Estimativa de tokens para PDFs subestimada (300 vs 450 palavras/página)
2. Crescimento do histórico de conversa não considerado (context rot em sessões longas no Teams)
3. Documentos contraditórios (PROC-042 v1/v2) não endereçados na estratégia de chunking
4. Perguntas multi-domínio sem tratamento (query expansion necessária)

**Output:** ver `.spec/exercicio-1.1-analise-viabilidade-tecnica.md` — seção "Rodada 2".

---

## Análise da iteração

A Rodada 2 melhorou o documento de forma verificável:
- Estimativa da base revisada de ~4M para ~5,6M tokens
- Adicionada estratégia de compressão de histórico para evitar context rot
- Adicionado filtro de deduplicação por versão de documento no retrieval
- Adicionada query expansion como estratégia complementar para perguntas multi-domínio
