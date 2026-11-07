import type { Meta } from "./types";

export const DISCLAIMER = "Facts-only. No investment advice.";
export const REDACTED_QUESTION = "[question withheld — PII detected]";

export const WELCOME =
  "Welcome. Ask factual questions about the indexed HDFC Mutual Fund Groww pages " +
  "(AMC overview and four Direct Growth schemes). Answers come only from those pages.";

export interface ExampleQuestion {
  label: string;
  question: string;
  icon: string;
}

export const EXAMPLES: ExampleQuestion[] = [
  {
    label: "Expense ratio · HDFC Large Cap",
    question: "What is the expense ratio of HDFC Large Cap Fund Direct Growth?",
    icon: "percent",
  },
  {
    label: "Lock-in · HDFC ELSS",
    question: "What is the lock-in for HDFC ELSS Tax Saver Fund Direct Plan Growth?",
    icon: "lock_clock",
  },
  {
    label: "Minimum SIP · HDFC Mid Cap",
    question: "What is the minimum SIP for HDFC Mid Cap Fund Direct Growth?",
    icon: "savings",
  },
];

export const SOURCE_COPY: Record<string, { label: string; sub: string }> = {
  "hdfc-amc": {
    label: "AMC Overview — HDFC Mutual Fund",
    sub: "Regulatory profile & fund list",
  },
  "hdfc-large-cap": {
    label: "Large Cap — HDFC Large Cap Fund Direct Growth",
    sub: "NAV, expense ratio & portfolio",
  },
  "hdfc-flexi-cap": {
    label: "Flexi Cap — HDFC Flexi Cap Direct Plan Growth",
    sub: "Expense ratio, exit load & holdings",
  },
  "hdfc-elss": {
    label: "ELSS — HDFC ELSS Tax Saver Fund Direct Plan Growth",
    sub: "Lock-in, tax & SIP details",
  },
  "hdfc-mid-cap": {
    label: "Mid Cap — HDFC Mid Cap Fund Direct Growth",
    sub: "Riskometer, benchmark & SIP",
  },
};

export const FALLBACK_META: Meta = {
  chunk_count: 152,
  source_count: 5,
  sources: [
    {
      id: "hdfc-amc",
      type: "amc",
      title: "HDFC Mutual Fund",
      url: "https://groww.in/mutual-funds/amc/hdfc-mutual-funds",
      chunks: 9,
    },
    {
      id: "hdfc-large-cap",
      type: "scheme",
      title: "HDFC Large Cap Fund Direct Growth",
      url: "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
      chunks: 36,
    },
    {
      id: "hdfc-flexi-cap",
      type: "scheme",
      title: "HDFC Flexi Cap Direct Plan Growth",
      url: "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
      chunks: 36,
    },
    {
      id: "hdfc-elss",
      type: "scheme",
      title: "HDFC ELSS Tax Saver Fund Direct Plan Growth",
      url: "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
      chunks: 37,
    },
    {
      id: "hdfc-mid-cap",
      type: "scheme",
      title: "HDFC Mid Cap Fund Direct Growth",
      url: "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
      chunks: 34,
    },
  ],
  embedding_model: "sentence-transformers/all-MiniLM-L6-v2",
  embedding_dimension: 384,
  collection: "groww_hdfc_mf",
  retrieval_k: 4,
  retrieval_min_score: 0.55,
  api_version: "1",
};

export function modelShortName(model: string): string {
  return model.split("/").pop() || model;
}
