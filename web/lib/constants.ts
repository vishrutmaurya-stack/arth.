export const DISCLAIMER = "Facts only. No investment advice.";
export const REDACTED_QUESTION = "[question withheld — PII detected]";

export interface ExampleQuestion {
  category: string;
  question: string;
}

export const EXAMPLES: ExampleQuestion[] = [
  {
    category: "Expense ratio",
    question: "What is the expense ratio of HDFC Large Cap Fund?",
  },
  {
    category: "Lock-in period",
    question: "What is the lock-in period for HDFC ELSS Tax Saver Fund?",
  },
  {
    category: "Minimum SIP",
    question: "What is the minimum SIP for HDFC Mid Cap Fund?",
  },
];
