# Exercício 1.1 — Análise de Viabilidade Técnica com Fundamentos de LLM e Engenharia de Contexto

**Participante:** Rafael Chaves  
**Papel:** Desenvolvedor  
**Data:** 2026-05-30

---

## Rodada 1: Análise inicial

---

### 1. Desafios por tipo de fonte

#### PDFs com tabelas complexas (tabelas de frete com 15+ colunas)

**Desafio para o pipeline:** Extratores de PDF padrão (PyMuPDF, pdfplumber) frequentemente serializam tabelas como texto plano, quebrando a estrutura de linhas e colunas. Uma tabela de multiplicadores regionais vira texto confuso como "Sul 1.2 Sudeste 1.0 Centro-Oeste 1.3..." sem delimitadores claros.

**Impacto na qualidade:** O chunking por tamanho fixo pode cortar uma tabela no meio, separando cabeçalho de dados. O LLM recebe metade de uma tabela sem contexto de qual coluna pertence a qual valor — o exato problema que ocorre com PROC-042 e seus multiplicadores.

**Estratégia:** Usar extração estruturada de tabelas (pdfplumber com detecção de bordas, ou Camelot para PDFs nativos). Converter tabelas para Markdown antes do chunking. Manter a tabela completa em um único chunk, mesmo que ultrapasse o tamanho-alvo.

---

#### PDFs escaneados (OCR necessário, ~15% da base)

**Desafio:** PDFs escaneados são imagens. Sem OCR, o texto não existe para o pipeline — o documento é ingerido como arquivo vazio. OCR introduz erros de caractere (ex: "1.2" vira "l.2") que corrompem silenciosamente dados numéricos críticos como multiplicadores de frete.

**Impacto na qualidade:** Erros de OCR em valores numéricos são especialmente perigosos no domínio logístico: um multiplicador lido incorretamente resulta em cálculo de frete errado passado ao atendente como fato.

**Estratégia:** Usar Azure AI Document Intelligence (disponível no stack Azure da NovaTech) para OCR com reconhecimento de layout. Implementar etapa de validação pós-OCR: checar se valores numéricos em documentos de frete estão dentro de faixas esperadas. Marcar chunks originados de OCR com metadado `source_quality: ocr` para tratamento diferenciado no prompt.

---

#### Wiki do Confluence (HTML/Wiki com links internos e macros)

**Desafio:** Links internos entre páginas criam dependências de contexto: uma página pode dizer "conforme descrito em [Procedimento X]" sem incluir o conteúdo. Macros customizadas do Confluence geram blocos que extratores HTML genéricos interpretam como texto literal ou ignoram completamente.

**Impacto na qualidade:** Chunks com referências a outras páginas sem resolver os links ficam semanticamente incompletos. O LLM recebe "conforme descrito em PROC-088" mas nunca vê o conteúdo da PROC-088.

**Estratégia:** Usar a API do Confluence para exportação (não scraping HTML), que retorna conteúdo estruturado com metadados de links. Resolver links internos no momento da ingestão: se a página A referencia a página B, incluir resumo da página B como metadado do chunk de A. Ignorar macros de navegação (breadcrumbs, índices automáticos) que não contêm conteúdo semântico.

---

#### Planilhas com fórmulas interdependentes (XLSX)

**Desafio:** Planilhas do Excel têm três camadas: estrutura (células/abas), fórmulas (lógica computacional) e valores calculados. Um extrator que lê a planilha como texto captura apenas os valores visíveis — mas sem o contexto de qual célula representa o quê, a tabela vira uma sequência de números sem semântica.

**Impacto na qualidade:** A tabela de fretes base (`frete-base-AAAAMM.xlsx`) mencionada no PROC-042 é atualizada mensalmente. Se o pipeline ingere valores estáticos sem capturar o contexto de cabeçalhos e abas, o LLM pode responder com valores de frete desatualizados sem saber que estão desatualizados.

**Estratégia:** Usar openpyxl para ler planilhas preservando cabeçalhos de linha e coluna. Converter cada aba em Markdown tabelado com contexto completo. Para planilhas com fórmulas, capturar apenas os valores calculados (não as fórmulas). Incluir data de modificação do arquivo como metadado obrigatório em cada chunk.

---

### 2. Estimativa do tamanho da base em tokens

Usando a regra prática: **1 token ≈ 0,75 palavras** (ou ~4 caracteres).

**PDFs do SharePoint:**
- 800 documentos × 10 páginas/doc × ~300 palavras/página = 2.400.000 palavras
- 2.400.000 ÷ 0,75 = **~3,2 milhões de tokens**

**Wiki do Confluence:**
- 400 páginas × 1.500 palavras/página = 600.000 palavras
- 600.000 ÷ 0,75 = **~800.000 tokens**

**Planilhas XLSX:**
- 50 planilhas × ~500 células com dados × ~5 caracteres/célula = ~125.000 caracteres
- ~125.000 ÷ 4 = **~31.000 tokens**

**Total estimado (Rodada 1): ~4 milhões de tokens na base indexada.**

> Relevante não para a janela de contexto (que é por query), mas para o custo de embeddings na ingestão inicial e dimensionamento do vector store.

---

### 3. Análise de orçamento de contexto por query

**Janela disponível no GPT-4o:** 128.000 tokens

**Distribuição estimada por query:**

| Componente | Tokens estimados | Tipo |
|---|---|---|
| System prompt + guardrails | ~2.000 | Estático |
| Metadados do cliente (tier, histórico) | ~200 | Dinâmico |
| Histórico de conversa (3 turnos) | ~1.500 | Dinâmico, crescente |
| Chunks recuperados | ~3.000–5.000 | Dinâmico |
| Pergunta do atendente | ~50–150 | Dinâmico |
| **Total típico por query** | **~7.000–9.000** | |

**Capacidade de chunks no orçamento:**
- Com chunks de ~500 tokens e reservando ~7.000 tokens para o restante do contexto:
  - (128.000 - 7.000) ÷ 500 = ~242 chunks cabem teoricamente
  - Na prática, com histórico crescente e margem de segurança, **6 a 10 chunks por query** é o limite razoável para manter qualidade

**Implicação crítica:** O problema não é a janela ser pequena demais — é que mais chunks não significa melhor resposta. Recuperar 20 chunks de 500 tokens cada adiciona 10.000 tokens de contexto, mas o efeito *lost in the middle* faz com que chunks posicionados no meio sejam subprocessados. O retrieval precisa ser preciso, não abrangente.

---

### 4. Estratégia de chunking recomendada

**Recomendação: chunking por seção semântica com overlap de 10%, tamanho máximo de 500 tokens.**

**Justificativa baseada no tipo de pergunta:**

Os atendentes fazem perguntas pontuais de domínio estreito: "Qual o SLA do cliente Gold?", "Posso devolver carga perigosa?". Essas perguntas têm resposta em seções específicas de documentos — não em documentos inteiros. Chunks por seção semântica (respeitando fronteiras de títulos e parágrafos) garantem que um chunk contenha uma unidade de informação completa.

**Por que não chunking fixo de 512 tokens:**
Chunking fixo ignora fronteiras semânticas. Uma tabela de multiplicadores regionais com 480 tokens pode ser cortada na linha "Norte | 1.8", deixando metade da tabela num chunk e a continuação no próximo. O retrieval pode trazer o chunk que contém "Sul | 1.3" mas perder o chunk com "Norte | 1.8" — exatamente a informação que o atendente precisa para Manaus.

**Por que overlap de 10% (não zero, não 50%):**
Overlap zero perde contexto em fronteiras de seção (uma frase introdutória que define o contexto da tabela que começa no próximo chunk). Overlap alto (50%+) duplica muito conteúdo no index, aumenta custo de embeddings e polui o retrieval com chunks quase idênticos concorrendo por posição.

**Tratamento especial para tabelas:**
Tabelas inteiras devem ser mantidas como um único chunk independentemente do tamanho, com cabeçalho repetido. Uma tabela de 800 tokens é melhor como um chunk de 800 tokens do que dois chunks de 400 que perdem a estrutura.

**Consideração sobre *lost in the middle*:**
Ao montar o contexto da query, posicionar os chunks mais relevantes (maior score de similaridade) no início e no final do bloco de contexto, reservando o meio para chunks de suporte. Isso mitiga o efeito de "esquecimento" de informação central.

---

## Rodada 2: Revisão crítica (iteração com Claude)

> Prompt enviado ao Claude: *"Revise a análise técnica acima. Identifique pontos fracos, estimativas otimistas demais ou riscos que não foram considerados."*

**Pontos identificados na revisão:**

### Ponto 1 — Estimativa de tokens para PDFs subestimada

A conta usou 300 palavras/página como média, mas documentos normativos densos (como políticas de compliance) facilmente chegam a 500–600 palavras/página.

Reestimando com 450 palavras/página:
- 800 × 10 × 450 ÷ 0,75 = ~4,8M tokens só nos PDFs
- **Total revisado: ~5,6 milhões de tokens na base**

### Ponto 2 — Crescimento do histórico de conversa não considerado

No Teams, uma sessão pode acumular 10–15 turnos. Com 10 turnos de ~500 tokens cada = 5.000 tokens só de histórico — comprimindo o espaço disponível para chunks.

**Mitigação necessária:** Implementar mecanismo de compressão/sumarização do histórico após N turnos. Sem isso, em conversas longas o sistema automaticamente reduz o número de chunks recuperados, degradando a qualidade silenciosamente (*context rot*).

### Ponto 3 — Documentos contraditórios não endereçados na estratégia de chunking

PROC-042 e PROC-042-v2 produzirão chunks concorrentes com scores de similaridade semelhantes para perguntas sobre frete especial. O pipeline pode retornar chunks das duas versões na mesma query.

**Mitigação necessária:** Incluir metadados de versão e data de vigência em cada chunk. Implementar filtro de deduplicação por documento-fonte no retrieval quando houver versões múltiplas do mesmo procedimento.

### Ponto 4 — Perguntas multi-domínio não tratadas

Uma pergunta como "Posso devolver carga perigosa com frete especial?" cruza POL-001, PROC-042 e possivelmente FAQ. Com retrieval puramente por similaridade semântica, a query pode não recuperar todos os domínios relevantes.

**Mitigação necessária:** Implementar query expansion — decompor a pergunta em sub-queries por domínio antes do retrieval, consolidando os chunks resultantes.

---

## Análise técnica final (versão consolidada)

| Tipo de fonte | Principal desafio | Estratégia |
|---|---|---|
| PDFs com tabelas | Serialização destrói estrutura | pdfplumber/Camelot + Markdown; tabelas = chunk único |
| PDFs escaneados | OCR silenciosamente corrompe números | Azure AI Document Intelligence; metadado `source_quality: ocr` |
| Wiki Confluence | Links não resolvidos geram chunks incompletos | API Confluence; resolução de links na ingestão |
| Planilhas XLSX | Valores sem contexto de cabeçalho | openpyxl; Markdown tabelado; metadado de data de modificação |

**Base estimada:** ~5,6 milhões de tokens (revisado para cima após crítica).

**Orçamento de contexto por query:** 6–10 chunks de 500 tokens, com compressão de histórico após N turnos para evitar context rot.

**Chunking:** por seção semântica, máx. 500 tokens, overlap 10%, tabelas preservadas inteiras, metadados obrigatórios de versão e vigência.

**Retrieval:** posicionamento dos chunks mais relevantes no início/fim do contexto (*lost in the middle* mitigation); filtro de deduplicação para documentos contraditórios; query expansion para perguntas multi-domínio.
