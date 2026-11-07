"use client";

import { useState } from "react";
import type { FormEvent } from "react";

import { EXAMPLES, SOURCE_COPY, WELCOME, modelShortName } from "@/lib/constants";
import type { Meta, Turn } from "@/lib/types";

import { TurnCard } from "./turn-card";

interface ChatProps {
  meta: Meta;
  turns: Turn[];
  pending: boolean;
  error: string | null;
  onAsk: (question: string) => void;
}

export function Chat({ meta, turns, pending, error, onAsk }: ChatProps) {
  const [value, setValue] = useState("");
  const [validation, setValidation] = useState<string | null>(null);
  const model = modelShortName(meta.embedding_model);
  const dimension = meta.embedding_dimension ?? 384;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const question = value.trim();
    if (!question) {
      setValidation("Please enter a question.");
      return;
    }
    setValidation(null);
    setValue("");
    onAsk(question);
  }

  return (
    <div className="mx-auto w-full max-w-3xl px-4 pb-10 pt-6 sm:px-6">
      <section className="relative overflow-hidden rounded-2xl border border-outline-variant/40 bg-white/90 p-5 shadow-card backdrop-blur-xl sm:p-6">
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-primary to-transparent opacity-70"
        />
        <div className="flex items-center gap-1.5 font-label text-[10px] font-bold uppercase tracking-widest text-secondary">
          <span className="h-2 w-2 rounded-full bg-secondary shadow-[0_0_8px_#006b54]" />
          Knowledge base online
        </div>
        <h1 className="mt-2 font-headline text-xl font-extrabold tracking-tight text-on-surface sm:text-2xl">
          Ask the indexed pages, not the internet.
        </h1>
        <p className="mt-1.5 text-sm leading-relaxed text-on-surface-variant">
          {WELCOME}
        </p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          {[
            `${meta.chunk_count} chunks`,
            `${meta.source_count} sources`,
            `${model} · ${dimension}-d`,
            `cosine · k=${meta.retrieval_k}`,
          ].map((chip) => (
            <span
              key={chip}
              className="rounded-full border border-outline-variant/40 bg-surface-container-low px-2.5 py-1 font-label text-[9px] font-semibold text-on-surface-variant"
            >
              {chip}
            </span>
          ))}
        </div>
      </section>

      <div className="mt-5 flex items-center gap-2">
        <span className="font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Try an example
        </span>
        <span className="h-px flex-1 bg-outline-variant/40" />
      </div>
      <div className="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-3">
        {EXAMPLES.map((example) => (
          <button
            key={example.question}
            type="button"
            disabled={pending}
            onClick={() => onAsk(example.question)}
            className="group flex items-center gap-2.5 rounded-xl border border-outline-variant/40 bg-white/85 px-3 py-2.5 text-left shadow-tech-sm transition-all hover:-translate-y-0.5 hover:border-primary/30 hover:bg-surface-container-low disabled:cursor-not-allowed disabled:opacity-60"
          >
            <span className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-secondary-container/15 text-secondary transition-colors group-hover:bg-secondary-container/25">
              <span
                className="material-symbols-outlined text-[17px]"
                aria-hidden="true"
              >
                {example.icon}
              </span>
            </span>
            <span className="min-w-0 font-label text-[11px] font-semibold leading-snug text-on-surface">
              {example.label}
            </span>
          </button>
        ))}
      </div>

      <div className="mt-5 flex items-center gap-2">
        <span className="font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Ask a factual question
        </span>
        <span className="h-px flex-1 bg-outline-variant/40" />
      </div>

      <form onSubmit={submit} className="mt-2">
        <div className="flex flex-col gap-2 sm:flex-row">
          <div className="relative flex-1">
            <span
              className="material-symbols-outlined pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[18px] text-on-surface-variant"
              aria-hidden="true"
            >
              search
            </span>
            <input
              value={value}
              onChange={(event) => {
                setValue(event.target.value);
                setValidation(null);
              }}
              placeholder="Expense ratio, exit load, lock-in, minimum SIP, riskometer, or benchmark…"
              aria-label="Your question"
              disabled={pending}
              className="w-full rounded-xl border border-outline-variant/50 bg-white/90 py-3 pl-10 pr-3 text-sm text-on-surface shadow-tech-sm outline-none transition placeholder:text-on-surface-variant/60 focus:border-primary/60 focus:ring-2 focus:ring-primary/15 disabled:opacity-60"
            />
          </div>
          <button
            type="submit"
            disabled={pending}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-neon-pink via-primary to-neon-purple px-5 py-3 font-headline text-xs font-semibold text-white shadow-cta transition-all hover:brightness-105 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-60"
          >
            {pending ? (
              <>
                <span
                  className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white"
                  aria-hidden="true"
                />
                Asking…
              </>
            ) : (
              <>
                Ask Arth AI
                <span
                  className="material-symbols-outlined text-[16px]"
                  aria-hidden="true"
                >
                  send
                </span>
              </>
            )}
          </button>
        </div>
        {validation && (
          <p
            role="alert"
            className="mt-1.5 font-label text-[10px] font-medium text-primary"
          >
            {validation}
          </p>
        )}
      </form>

      {error && (
        <div
          role="alert"
          className="mt-3 rounded-xl border border-primary/20 bg-primary-fixed/40 px-3.5 py-3"
        >
          <div className="flex items-center gap-1.5 font-label text-[10px] font-bold uppercase tracking-wider text-primary">
            <span
              className="material-symbols-outlined text-[15px]"
              aria-hidden="true"
            >
              cloud_off
            </span>
            Request failed
          </div>
          <p className="mt-1 text-[11px] leading-relaxed text-on-surface-variant">
            {error}
          </p>
          <p className="mt-1 text-[11px] leading-relaxed text-on-surface-variant">
            Answers require the separately deployed Python RAG API. Check that
            it is running and that{" "}
            <code className="rounded bg-white/70 px-1 py-0.5 font-label text-[10px]">
              NEXT_PUBLIC_API_URL
            </code>{" "}
            points at it. Answers are never fabricated.
          </p>
        </div>
      )}

      {pending && (
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-outline-variant/40 bg-white/80 px-3.5 py-3 shadow-tech-sm">
          <span
            className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary/30 border-t-primary"
            aria-hidden="true"
          />
          <p className="font-label text-[11px] font-medium text-on-surface-variant">
            Retrieving from the indexed official pages…
          </p>
        </div>
      )}

      <div className="mt-5 flex items-center gap-2">
        <span className="font-label text-[10px] font-bold uppercase tracking-widest text-on-surface-variant">
          Conversation
        </span>
        <span className="h-px flex-1 bg-outline-variant/40" />
      </div>

      {turns.length === 0 ? (
        <div className="mt-2 rounded-xl border border-dashed border-outline-variant/60 bg-white/60 px-4 py-4 text-sm leading-relaxed text-on-surface-variant">
          <strong className="font-semibold text-on-surface">
            Answers appear here.
          </strong>{" "}
          Up to three sentences, one source link, and the last-updated timestamp
          of the cited page. No advice, no returns, no PII.
        </div>
      ) : (
        <div className="mt-2 space-y-4">
          {turns.map((turn) => (
            <TurnCard
              key={`${turn.result.query_id}-${turn.question}`}
              turn={turn}
            />
          ))}
        </div>
      )}

      <details className="group mt-5 overflow-hidden rounded-xl border border-outline-variant/40 bg-white/80 shadow-tech-sm">
        <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-4 py-2.5 font-label text-[10px] font-bold uppercase tracking-wider text-on-surface-variant [&::-webkit-details-marker]:hidden">
          Indexed sources &amp; guardrails
          <span
            className="material-symbols-outlined text-[16px] transition-transform group-open:rotate-180"
            aria-hidden="true"
          >
            expand_more
          </span>
        </summary>
        <div className="space-y-1.5 px-4 pb-3">
          {meta.sources.map((source) => {
            const copy = SOURCE_COPY[source.id] ?? {
              label: source.title,
              sub: "Indexed page",
            };
            return (
              <a
                key={source.id}
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between gap-2 rounded-lg border border-outline-variant/30 bg-surface/70 px-2.5 py-2 transition-colors hover:bg-surface-container"
              >
                <span className="min-w-0">
                  <span className="block truncate font-label text-[11px] font-semibold text-on-surface">
                    {copy.label}
                  </span>
                  <span className="block truncate font-label text-[9px] text-on-surface-variant">
                    {copy.sub}
                  </span>
                </span>
                <span className="flex-shrink-0 font-label text-[9px] text-on-surface-variant">
                  {source.chunks} chunks · {source.type}
                </span>
              </a>
            );
          })}
          <p className="pt-1 font-label text-[10px] leading-relaxed text-on-surface-variant">
            Only these {meta.source_count} Groww pages are indexed. Advice,
            performance comparisons, PII, and facts outside the corpus are
            refused.
          </p>
        </div>
      </details>
    </div>
  );
}
