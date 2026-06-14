import { app, HttpRequest, HttpResponseInit, InvocationContext } from '@azure/functions';
import { QueryRequestSchema } from './validator.js';
import { logger } from '../../shared/logger.js';

async function queryHandler(request: HttpRequest, _context: InvocationContext): Promise<HttpResponseInit> {
  try {
    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return {
        status: 422,
        jsonBody: { error: 'Body inválido: esperado JSON.' },
      };
    }

    const result = QueryRequestSchema.safeParse(body);
    if (!result.success) {
      logger.warn({ issues: result.error.issues }, 'Validação de input falhou');
      return {
        status: 400,
        jsonBody: {
          error: 'Requisição inválida.',
          details: result.error.issues.map((i) => i.message),
        },
      };
    }

    const { question } = result.data;

    // ADR-0002: context budget ~4K tokens system prompt + ~8K tokens chunks (top-5 de ~1.500 tokens cada).
    // TASK-002 a TASK-005 implementarão: embedding → busca → montagem do prompt → chamada GPT-4o.
    logger.info({ question }, 'Query recebida');

    return {
      status: 200,
      jsonBody: {
        answer: 'Resposta stub — implementação completa na TASK-005.',
        source_document: 'stub',
      },
    };
  } catch (err) {
    logger.error({ err }, 'Erro inesperado no handler de query');
    return { status: 500, jsonBody: { error: 'Erro interno.' } };
  }
}

app.http('query', {
  methods: ['POST'],
  authLevel: 'anonymous',
  route: 'query',
  handler: queryHandler,
});
