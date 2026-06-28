import { z } from 'zod';
import { logger } from '../shared/logger';

const SAFE_RESPONSE =
  'Não foi possível processar esta resposta. Por favor, consulte um supervisor.';

export const AssistantResponseSchema = z
  .object({
    answer: z.string().min(1, 'Resposta não pode ser vazia'),
    source_document: z.string().min(1, 'Documento fonte é obrigatório'),
    confidence_score: z.number().min(0).max(1),
  })
  .strict();

export type AssistantResponse = z.infer<typeof AssistantResponseSchema>;

type ValidatedResult =
  | { valid: true; data: AssistantResponse }
  | {
      valid: false;
      reason: 'schema_invalid' | 'missing_source' | 'dangerous_goods_violation';
      safeResponse: string;
    };

// Detecta afirmações de devolução de carga perigosa.
// Verificação em duas etapas: (1) menciona "carga perigosa", (2) contém padrão afirmativo
// sem negação imediata ("não") nos 25 caracteres anteriores.
const DANGEROUS_AFFIRMATIVE_PATTERNS = [
  /pode(?:m)?\s+(?:ser\s+)?devolvid[ao]s?/i,
  /(?:é|são)\s+possíve[il]s?\s+devolver/i,
  /devolução\s+(?:é\s+)?(?:disponível|permitida|possível)/i,
  /pode(?:m)?\s+devolver/i,
  /é\s+devolvível/i,
  /processo\s+de\s+devolução\s+(?:está\s+)?disponível/i,
];

function hasDangerousGoodsViolation(answer: string): boolean {
  if (!answer.toLowerCase().includes('carga perigosa')) return false;

  for (const pattern of DANGEROUS_AFFIRMATIVE_PATTERNS) {
    const match = answer.match(pattern);
    if (!match) continue;

    const matchIndex = match.index ?? 0;
    const preceding = answer.slice(Math.max(0, matchIndex - 25), matchIndex);
    if (/não\s*$/i.test(preceding.trimEnd())) continue;

    return true;
  }

  return false;
}

export function validateResponse(raw: unknown): ValidatedResult {
  const result = AssistantResponseSchema.safeParse(raw);

  if (!result.success) {
    logger.warn({ issues: result.error.issues }, 'response-validator: schema inválido');
    return { valid: false, reason: 'schema_invalid', safeResponse: SAFE_RESPONSE };
  }

  const data = result.data;

  // Guardrail 1: reforço explícito — source_document não pode ser só espaços
  if (!data.source_document.trim()) {
    logger.warn('response-validator: source_document vazio após trim');
    return { valid: false, reason: 'missing_source', safeResponse: SAFE_RESPONSE };
  }

  // Guardrail 2: carga perigosa + afirmação de devolução sem negativa
  if (hasDangerousGoodsViolation(data.answer)) {
    logger.warn(
      { reason: 'dangerous_goods_violation' },
      'response-validator: resposta bloqueada — carga perigosa com devolução afirmativa',
    );
    return { valid: false, reason: 'dangerous_goods_violation', safeResponse: SAFE_RESPONSE };
  }

  return { valid: true, data };
}
