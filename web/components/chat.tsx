"use client";

import { useEffect } from "react";

import type { ApiStatus, Turn } from "@/lib/types";

import { BrandMark } from "./brand-mark";
import { ErrorNotice } from "./error-notice";
import { TurnCard } from "./turn-card";
import { Welcome } from "./welcome";

interface ChatProps {
  turns: Turn[];
  pending: boolean;
  error: string | null;
  apiStatus: ApiStatus;
  onAsk: (question: string) => void;
  onRetry: () => void;
}

export function Chat({
  turns,
  pending,
  error,
  apiStatus,
  onAsk,
  onRetry,
}: ChatProps) {
  useEffect(() => {
    if (turns.length === 0 && !pending) {
      return;
    }
    window.scrollTo({
      top: document.body.scrollHeight,
      behavior: "smooth",
    });
  }, [turns.length, pending]);

  if (turns.length === 0 && !pending) {
    return (
      <Welcome
        apiStatus={apiStatus}
        pending={pending}
        error={error}
        onAsk={onAsk}
        onRetry={onRetry}
      />
    );
  }

  return (
    <div className="animate-rise">
      <div className="space-y-9">
        {turns.map((turn) => (
          <TurnCard
            key={`${turn.result.query_id}-${turn.question}`}
            turn={turn}
          />
        ))}
        {pending && <PendingTurn />}
      </div>

      {error && (
        <div className="mt-6">
          <ErrorNotice message={error} />
        </div>
      )}
    </div>
  );
}

function PendingTurn() {
  return (
    <div aria-live="polite" className="flex items-center gap-2.5">
      <BrandMark className="h-5 w-5" />
      <div className="flex items-center gap-2">
        <span className="flex gap-1" aria-hidden="true">
          {[0, 1, 2].map((index) => (
            <span
              key={index}
              className="h-1.5 w-1.5 animate-dot-bounce rounded-full bg-sage"
              style={{ animationDelay: `${index * 140}ms` }}
            />
          ))}
        </span>
        <span className="text-[11.5px] font-medium text-muted">
          Reading the indexed pages…
        </span>
      </div>
    </div>
  );
}
