import type { AskResult, Meta } from "./types";

const configured = (process.env.NEXT_PUBLIC_API_URL || "").trim();

export const API_BASE = (configured || "http://localhost:8000").replace(/\/+$/, "");
export const API_CONFIGURED = configured.length > 0;

export class ApiError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const payload = (await response.json()) as { detail?: unknown };
    if (typeof payload.detail === "string" && payload.detail.trim()) {
      return payload.detail;
    }
  } catch {
    // Fall through to the status-based message.
  }
  return `Request failed with status ${response.status}.`;
}

export async function getMeta(signal?: AbortSignal): Promise<Meta> {
  const response = await fetch(`${API_BASE}/api/meta`, {
    cache: "no-store",
    signal,
  });
  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }
  return (await response.json()) as Meta;
}

export async function askQuestion(question: string): Promise<AskResult> {
  const response = await fetch(`${API_BASE}/api/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!response.ok) {
    throw new ApiError(await errorMessage(response), response.status);
  }
  return (await response.json()) as AskResult;
}
