import json
import os
from search import search
from prompt_builder import build_prompt, estimate_tokens

TESTS = [
    {
        "id": 1,
        "question": "Qual o prazo de devolução?",
        "expected_chunks": ["POL-001-A", "POL-001-B"],
        "expected_sources": ["POL-001-politica-devolucao.md"],
        "trap": "Regra geral (7 dias) vs. exceção (cargas perigosas NÃO podem). Resposta correta menciona ambas.",
    },
    {
        "id": 2,
        "question": "Posso devolver carga perigosa?",
        "expected_chunks": ["POL-001-B"],
        "expected_sources": ["POL-001-politica-devolucao.md"],
        "trap": "Inversão da regra — resposta correta é NÃO pelo processo padrão.",
    },
    {
        "id": 3,
        "question": "Qual o SLA do cliente Gold?",
        "expected_chunks": ["SLA-2024-B"],
        "expected_sources": ["SLA-2024-tabela-sla-clientes.md"],
        "trap": "Omitir SLA de incidentes críticos (4h). Resposta completa menciona chamados gerais E críticos.",
    },
    {
        "id": 4,
        "question": "Qual o custo do frete para 600kg para Manaus?",
        "expected_chunks": ["PROC-042v2-B", "PROC-042v2-A"],
        "expected_sources": ["PROC-042-v2-frete-especial-revisado.md"],
        "trap": "Misturar versões v1/v2. Deve usar Norte=1.8 (v2), não Norte=1.6 (v1).",
    },
    {
        "id": 5,
        "question": "Qual o SLA do cliente Platinum?",
        "expected_chunks": ["SLA-2024-A"],
        "expected_sources": ["SLA-2024-tabela-sla-clientes.md"],
        "trap": "Tier Platinum não existe. Resposta correta informa isso sem inventar SLAs.",
    },
]


def evaluate_retrieval(retrieved: list[dict], expected_sources: list[str]) -> str:
    retrieved_sources = {r["metadata"].get("source", "") for r in retrieved}
    matches = [s for s in expected_sources if any(s in rs for rs in retrieved_sources)]
    if len(matches) == len(expected_sources):
        return "full"
    return "partial" if matches else "miss"


def run_tests(output_path: str = "test_results.json") -> None:
    print("=" * 65)
    print("TESTES DO PIPELINE RAG — NovaTech")
    print("=" * 65)

    results = []

    for test in TESTS:
        print(f"\n[Teste {test['id']}/5] {test['question']}")
        print(f"  Armadilha: {test['trap']}")

        chunks = search(test["question"], n_results=5)

        print(f"  Chunks recuperados:")
        for c in chunks:
            print(
                f"    score={c['similarity_score']:.4f} | "
                f"{c['metadata']['source']} | {c['metadata']['section']}"
            )

        match = evaluate_retrieval(chunks, test["expected_sources"])
        symbol = "[OK]" if match == "full" else ("[~]" if match == "partial" else "[X]")
        print(f"  Retrieval vs gabarito: {symbol} {match.upper()}")

        prompt = build_prompt(test["question"], chunks)
        tokens = estimate_tokens(prompt)
        print(f"  Prompt: ~{tokens} tokens")

        results.append({
            "id": test["id"],
            "question": test["question"],
            "trap": test["trap"],
            "retrieved_chunks": [
                {
                    "source": c["metadata"]["source"],
                    "section": c["metadata"]["section"],
                    "version": c["metadata"].get("doc_version"),
                    "score": c["similarity_score"],
                }
                for c in chunks
            ],
            "expected_chunks": test["expected_chunks"],
            "expected_sources": test["expected_sources"],
            "retrieval_match": match,
            "prompt": prompt,
            "prompt_tokens": tokens,
            "llm_response": "[colar resposta do Claude após enviar o prompt acima]",
            "evaluation": "[correct | partial | incorrect]",
            "notes": "[análise após obter a resposta do LLM]",
        })

    out = os.path.join(os.path.dirname(__file__), output_path)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 65}")
    print(f"Resultados salvos em {output_path}")
    print("Próximo passo: colar cada prompt no Claude e preencher llm_response + evaluation.")


if __name__ == "__main__":
    run_tests()
