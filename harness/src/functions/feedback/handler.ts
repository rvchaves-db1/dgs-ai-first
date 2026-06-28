import { app, HttpRequest, HttpResponseInit, InvocationContext } from '@azure/functions';
import { CosmosClient } from '@azure/cosmos';
import { z } from 'zod';
import { logger } from '../../shared/logger';

const FeedbackRequestSchema = z.object({
  queryId: z.string().min(1, 'queryId é obrigatório'),
  rating: z.number().int().min(1).max(5, 'rating deve ser entre 1 e 5'),
  comment: z.string().optional(),
  attendantEmail: z.string().email('e-mail inválido').optional(),
});

type FeedbackRequest = z.infer<typeof FeedbackRequestSchema>;

const cosmosClient = new CosmosClient(process.env.COSMOS_CONNECTION_STRING ?? '');
const container = cosmosClient.database('novatech').container('feedbacks');

export async function feedbackHandler(
  request: HttpRequest,
  _context: InvocationContext,
): Promise<HttpResponseInit> {
  const body = await request.json().catch(() => null);
  const parsed = FeedbackRequestSchema.safeParse(body);

  if (!parsed.success) {
    logger.warn({ issues: parsed.error.issues }, 'feedback: input inválido');
    return {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Input inválido', details: parsed.error.issues }),
    };
  }

  // Separar dado pessoal antes de qualquer log
  const { attendantEmail, ...safeFields } = parsed.data;

  try {
    await container.items.create({
      ...parsed.data,
      timestamp: new Date().toISOString(),
    });

    logger.info(
      { queryId: safeFields.queryId, rating: safeFields.rating },
      'feedback: registrado com sucesso',
    );

    return {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ok: true }),
    };
  } catch (err) {
    logger.error(
      { err, queryId: safeFields.queryId },
      'feedback: falha ao salvar no Cosmos DB',
    );
    return {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ error: 'Erro interno ao registrar feedback' }),
    };
  }
}

app.http('feedback', {
  methods: ['POST'],
  authLevel: 'anonymous',
  route: 'feedback',
  handler: feedbackHandler,
});
