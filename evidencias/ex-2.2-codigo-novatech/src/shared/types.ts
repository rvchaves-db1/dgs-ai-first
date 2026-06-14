export type QueryRequest = {
  question: string;
};

export type QueryResponse = {
  answer: string;
  source_document: string;
  confidence?: number;
};

export type Chunk = {
  id: string;
  content: string;
  source: string;
  vigencia?: string;
};
