from __future__ import annotations

SYSTEM_PROMPT = """\
## Identidade
Você é o Assistente de Atendimento da NovaTech, empresa de logística.
Seu papel é ajudar os atendentes a responderem dúvidas de clientes com
base exclusivamente na documentação oficial fornecida.

## Regras obrigatórias (sem exceção)
1. Use APENAS informações presentes nos documentos fornecidos abaixo.
2. Cite SEMPRE a fonte ao final de cada afirmação. Formato: [Fonte: NOME-DO-DOC, seção X.X]
3. Nunca invente prazos, valores numéricos ou procedimentos que não estejam nos documentos.
4. Se a resposta principal for uma EXCEÇÃO ou RESTRIÇÃO, apresente a restrição PRIMEIRO,
   antes de qualquer regra geral.
5. Se a informação não estiver nos documentos, responda exatamente:
   "Não encontrei essa informação na documentação disponível.
    Por favor, escale para o supervisor ou consulte a área responsável."
6. Quando a resposta for parcial (fórmula presente, mas dado de entrada ausente),
   apresente o que tem e indique o que falta para completar o cálculo.
7. Se existirem duas versões de um mesmo documento, priorize a mais recente e informe
   ao atendente que existe uma versão anterior.
8. Responda em português formal e acessível.

## Formato de resposta
- Primeira linha: resposta direta.
- Parágrafos seguintes: detalhes e contexto, se necessário.
- Fonte entre colchetes ao final de cada afirmação factual.
- Restrições ou exceções relevantes devem ser destacadas com "ATENÇÃO:".\
"""

MAX_PROMPT_TOKENS = 8_000
MAX_HISTORY_TURNS = 6


def estimate_tokens(text: str) -> int:
    return len(text) // 4


def _order_lost_in_middle(chunks: list[dict]) -> list[dict]:
    """Best score first, second-best last, rest in the middle."""
    if len(chunks) <= 2:
        return chunks
    s = sorted(chunks, key=lambda x: x["similarity_score"], reverse=True)
    return [s[0]] + s[2:] + [s[1]]


def _contradiction_warning(chunks: list[dict]) -> str | None:
    families: dict[str, list[dict]] = {}
    for chunk in chunks:
        source = chunk["metadata"].get("source", "")
        name = source.replace(".md", "")
        parts = name.split("-")
        family = f"{parts[0]}-{parts[1]}" if len(parts) >= 2 else name
        families.setdefault(family, []).append(chunk)

    warnings = []
    for family, fam_chunks in families.items():
        sources = {c["metadata"]["source"] for c in fam_chunks}
        if len(sources) > 1:
            dates = {c["metadata"]["source"]: c["metadata"].get("doc_date", "") for c in fam_chunks}
            newest = max(dates, key=lambda k: dates[k])
            warnings.append(
                f"[AVISO: Múltiplas versões de {family} encontradas. "
                f"Versão mais recente: {newest} ({dates[newest]}). "
                f"Priorize-a e informe ao atendente sobre a versão anterior.]"
            )
    return "\n".join(warnings) if warnings else None


def _faq_only(chunks: list[dict]) -> bool:
    return bool(chunks) and all(
        c["metadata"].get("source", "").upper().startswith("FAQ") for c in chunks
    )


def build_prompt(
    query: str,
    chunks: list[dict],
    client_tier: str | None = None,
    conversation_history: list[dict] | None = None,
) -> str:
    parts: list[str] = [SYSTEM_PROMPT]

    if client_tier:
        parts.append(f"\n## Contexto do atendimento\nTier do cliente: **{client_tier}**")

    warn = _contradiction_warning(chunks)
    if warn:
        parts.append(f"\n{warn}")

    if _faq_only(chunks):
        parts.append(
            "\n[ATENÇÃO: Todos os trechos recuperados são do FAQ informal. "
            "Confirme com a documentação normativa antes de informar ao cliente.]"
        )

    ordered = _order_lost_in_middle(chunks)
    doc_section = "\n## Documentos recuperados\n"
    for i, chunk in enumerate(ordered, 1):
        m = chunk["metadata"]
        doc_section += (
            f"\n--- Documento {i} ---\n"
            f"Fonte: {m.get('source', '?')} | Seção: {m.get('section', '?')} | "
            f"Versão: {m.get('doc_version', '?')} | Data: {m.get('doc_date', '?')} | "
            f"Score: {chunk.get('similarity_score', 0):.4f}\n"
            f"{chunk['text']}\n"
        )
    parts.append(doc_section)

    if conversation_history:
        history_section = "\n## Histórico da conversa\n"
        for turn in conversation_history[-MAX_HISTORY_TURNS:]:
            role = "Atendente" if turn["role"] == "user" else "Assistente"
            history_section += f"{role}: {turn['content']}\n"
        parts.append(history_section)

    parts.append(f"\n## Pergunta do atendente\n{query}")

    prompt = "\n".join(parts)
    tokens = estimate_tokens(prompt)
    if tokens > MAX_PROMPT_TOKENS:
        print(f"  [AVISO] Prompt estimado em {tokens} tokens — acima do orçamento de {MAX_PROMPT_TOKENS}.")

    return prompt


if __name__ == "__main__":
    sample = [
        {
            "text": "O cliente pode solicitar devolução em até 7 dias úteis.",
            "metadata": {
                "source": "POL-001-politica-devolucao.md",
                "section": "3.1 Prazo geral",
                "doc_version": "3.1",
                "doc_date": "2024-01-15",
            },
            "similarity_score": 0.92,
        }
    ]
    prompt = build_prompt("Qual o prazo de devolução?", sample, client_tier="Gold")
    print(prompt)
    print(f"\nTokens estimados: {estimate_tokens(prompt)}")
