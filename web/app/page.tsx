"use client";

import { useCallback, useEffect, useState } from "react";

import { Chat } from "@/components/chat";
import { Composer } from "@/components/composer";
import { Header } from "@/components/header";
import { ApiError, askQuestion, getMeta } from "@/lib/api";
import { REDACTED_QUESTION } from "@/lib/constants";
import type { ApiStatus, Turn } from "@/lib/types";

export default function HomePage() {
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkStatus = useCallback(async () => {
    setApiStatus("checking");
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);

    try {
      await getMeta(controller.signal);
      setApiStatus("online");
    } catch {
      setApiStatus("offline");
    } finally {
      window.clearTimeout(timeout);
    }
  }, []);

  useEffect(() => {
    void checkStatus();
  }, [checkStatus]);

  const ask = useCallback(async (question: string) => {
    setPending(true);
    setError(null);

    try {
      const result = await askQuestion(question);
      setApiStatus("online");
      setTurns((previous) => [
        ...previous,
        {
          question:
            result.decision === "refuse_pii" ? REDACTED_QUESTION : question,
          result,
        },
      ]);
    } catch (failure) {
      if (failure instanceof ApiError && failure.status) {
        setApiStatus("online");
        setError(failure.message);
      } else {
        setApiStatus("offline");
        setError(
          "The knowledge base is unreachable right now. Check your connection and try again.",
        );
      }
    } finally {
      setPending(false);
    }
  }, []);

  return (
    <div className="flex min-h-dvh flex-col bg-canvas">
      <Header apiStatus={apiStatus} />

      <main className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 pb-40 pt-8 sm:px-6 sm:pb-44 sm:pt-12">
        <Chat
          turns={turns}
          pending={pending}
          error={error}
          apiStatus={apiStatus}
          onAsk={ask}
          onRetry={() => {
            void checkStatus();
          }}
        />
      </main>

      <Composer pending={pending} onAsk={ask} />
    </div>
  );
}
