"use client";

import { useCallback, useEffect, useState } from "react";

import { AmbientBackground } from "@/components/ambient-background";
import { Chat } from "@/components/chat";
import { Footer } from "@/components/footer";
import { Header } from "@/components/header";
import { Splash } from "@/components/splash";
import { API_BASE, ApiError, askQuestion, getMeta } from "@/lib/api";
import { FALLBACK_META, REDACTED_QUESTION } from "@/lib/constants";
import type { ApiStatus, Meta, Turn } from "@/lib/types";

export default function HomePage() {
  const [meta, setMeta] = useState<Meta>(FALLBACK_META);
  const [apiStatus, setApiStatus] = useState<ApiStatus>("checking");
  const [entered, setEntered] = useState(false);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 8000);

    getMeta(controller.signal)
      .then((payload) => {
        setMeta(payload);
        setApiStatus("online");
      })
      .catch(() => {
        setApiStatus("offline");
      })
      .finally(() => window.clearTimeout(timeout));

    return () => {
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, []);

  const ask = useCallback(async (question: string) => {
    setPending(true);
    setError(null);
    try {
      const result = await askQuestion(question);
      setApiStatus("online");
      setTurns((previous) => [
        {
          question:
            result.decision === "refuse_pii" ? REDACTED_QUESTION : question,
          result,
        },
        ...previous,
      ]);
    } catch (failure) {
      if (failure instanceof ApiError && failure.status) {
        setApiStatus("online");
        setError(failure.message);
      } else {
        setApiStatus("offline");
        setError(
          `The Python RAG API at ${API_BASE} could not be reached. Start the backend and try again.`,
        );
      }
    } finally {
      setPending(false);
    }
  }, []);

  return (
    <div className="relative flex min-h-screen flex-col overflow-x-hidden">
      <AmbientBackground />
      <Header apiStatus={apiStatus} />

      <main className="relative z-10 flex w-full flex-1 flex-col">
        {entered ? (
          <Chat
            meta={meta}
            turns={turns}
            pending={pending}
            error={error}
            onAsk={ask}
          />
        ) : (
          <Splash
            meta={meta}
            apiStatus={apiStatus}
            onEnter={() => setEntered(true)}
          />
        )}
      </main>

      <Footer count={meta.chunk_count} />
    </div>
  );
}
