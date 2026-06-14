import type { ZodIssue } from 'zod';

export class ValidationError extends Error {
  override readonly name = 'ValidationError';

  constructor(
    message: string,
    readonly issues: ZodIssue[],
  ) {
    super(message);
  }
}

export class SearchError extends Error {
  override readonly name = 'SearchError';

  constructor(
    message: string,
    readonly cause?: unknown,
  ) {
    super(message);
  }
}

export class CompletionError extends Error {
  override readonly name = 'CompletionError';

  constructor(
    message: string,
    readonly cause?: unknown,
  ) {
    super(message);
  }
}
