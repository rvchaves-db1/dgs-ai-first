import { z } from 'zod';

export const QueryRequestSchema = z.object({
  question: z
    .string({ required_error: 'O campo question é obrigatório.' })
    .trim()
    .min(1, { message: 'A pergunta não pode ser vazia.' })
    .max(2000, { message: 'A pergunta não pode ter mais de 2.000 caracteres.' }),
});

export type QueryRequest = z.infer<typeof QueryRequestSchema>;
