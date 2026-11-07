import { API_BASE, API_CONFIGURED } from "@/lib/api";
import { SOURCE_COPY, modelShortName } from "@/lib/constants";
import type { ApiStatus, Meta } from "@/lib/types";

interface SplashProps {
  meta: Meta;
  apiStatus: ApiStatus;
  onEnter: () => void;
}

export function Splash({ meta, apiStatus, onEnter }: SplashProps) {
  const online = apiStatus === "online";
  const offline = apiStatus === "offline";
  const readyLabel = online ? "100% Ready" : offline ? "API offline" : "Checking…";
  const barWidth = online ? "w-full" : offline ? "w-1/3" : "w-3/5";
  const model = modelShortName(meta.embedding_model);
  const dimension = meta.embedding_dimension ?? 384;

  return (
    <section className="relative flex min-h-[calc(100vh-6rem)] w-full items-center justify-center overflow-hidden px-4 py-10">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-32 left-1/2 h-[360px] w-[720px] -translate-x-1/2 rounded-full bg-gradient-to-b from-primary/10 via-secondary-container/20 to-transparent blur-3xl"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-10 -left-20 h-80 w-80 rounded-full bg-secondary-fixed-dim/20 blur-[100px]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -right-20 bottom-10 h-80 w-80 rounded-full bg-primary/10 blur-[100px]"
      />

      <div className="relative w-full max-w-2xl overflow-hidden rounded-2xl border border-outline-variant/50 bg-white/90 p-5 shadow-card backdrop-blur-2xl sm:p-8">
        <div
          aria-hidden="true"
          className="absolute inset-x-0 top-0 h-[2px] bg-gradient-to-r from-transparent via-primary to-transparent opacity-80"
        />

        <div className="flex flex-col items-center justify-between gap-4 pb-1 sm:flex-row sm:items-start">
          <div className="flex items-center gap-3.5">
            <div className="relative flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-2xl bg-surface-container-low shadow-inner">
              <span className="absolute inset-0 animate-ping rounded-2xl bg-primary/15 opacity-60" />
              <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-primary via-primary-container to-secondary text-white shadow-md shadow-primary/30">
                <span
                  className="material-symbols-outlined text-[24px]"
                  aria-hidden="true"
                >
                  hub
                </span>
              </div>
              <svg
                aria-hidden="true"
                className="pointer-events-none absolute inset-0 h-full w-full -rotate-90"
                viewBox="0 0 56 56"
              >
                <circle
                  cx="28"
                  cy="28"
                  r="24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeDasharray="12 4"
                  className="text-secondary/30"
                />
                <circle
                  cx="28"
                  cy="28"
                  r="20"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeDasharray="8 8"
                  className="animate-spin text-primary/40 [animation-duration:9s]"
                />
              </svg>
            </div>
            <div className="flex flex-col text-center sm:text-left">
              <div className="flex items-center justify-center gap-2 sm:justify-start">
                <span className="font-headline text-xl font-bold tracking-tight text-on-surface sm:text-2xl">
                  Arth AI
                </span>
                <span className="rounded-full bg-primary-fixed px-2 py-0.5 font-label text-[9px] font-bold uppercase tracking-widest text-primary">
                  v2.4 Core
                </span>
              </div>
              <p className="mt-0.5 font-label text-[10px] font-medium tracking-tight text-on-surface-variant">
                Grounded Deterministic Engine
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 rounded-full bg-surface-container px-3 py-1.5 shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-secondary-fixed opacity-75" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-secondary" />
            </span>
            <span className="font-label text-[10px] font-semibold uppercase tracking-wider text-on-surface">
              Strict Grounded RAG
            </span>
          </div>
        </div>

        <div className="mt-5 text-center sm:text-left">
          <h1 className="font-headline text-2xl font-extrabold leading-tight tracking-tight text-on-surface sm:text-3xl">
            Indexed Knowledge Base Online
          </h1>
          <p className="mt-1.5 max-w-xl text-sm leading-relaxed text-on-surface-variant">
            {meta.chunk_count} chunks from the five authorized HDFC Mutual Fund
            Groww pages are indexed in the Chroma store. Every answer is
            retrieved from these pages and cited back to them.
          </p>
        </div>

        <div className="mt-4 rounded-xl bg-surface-container-low p-3.5 shadow-sm">
          <div className="flex items-center justify-between gap-2 font-label text-[10px]">
            <span className="flex items-center gap-1.5 font-semibold uppercase tracking-wider text-on-surface">
              <span
                className="material-symbols-outlined text-[15px] text-primary"
                aria-hidden="true"
              >
                sync
              </span>
              Pipeline integrity
            </span>
            <span className="text-[11px] font-bold tracking-tight text-primary">
              {readyLabel}
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded-full bg-surface-container p-0.5">
            <div
              className={`h-full rounded-full bg-gradient-to-r from-secondary via-secondary-container to-primary shadow-[0_0_12px_rgba(183,0,79,0.35)] transition-all duration-700 ease-out ${barWidth}`}
            />
          </div>
          <div className="mt-2 flex flex-wrap items-center justify-between gap-y-1 text-[10px] font-label text-on-surface-variant">
            <span className="flex items-center gap-1">
              <span
                className="material-symbols-outlined text-[13px] text-secondary"
                aria-hidden="true"
              >
                memory
              </span>
              {model} · {dimension}-d · cosine
            </span>
            <span className="flex items-center gap-1 font-medium text-on-surface">
              <span
                className="material-symbols-outlined text-[13px] text-primary"
                aria-hidden="true"
              >
                verified_user
              </span>
              PII &amp; advice guardrails enforced
            </span>
          </div>
        </div>

        {offline && (
          <div
            role="status"
            className="mt-3 rounded-xl border border-primary/20 bg-primary-fixed/40 px-3.5 py-3"
          >
            <div className="flex items-center gap-1.5 font-label text-[10px] font-bold uppercase tracking-wider text-primary">
              <span
                className="material-symbols-outlined text-[15px]"
                aria-hidden="true"
              >
                cloud_off
              </span>
              Frontend live · backend not connected
            </div>
            <p className="mt-1 text-[11px] leading-relaxed text-on-surface-variant">
              Answers require the separately deployed Python RAG API. Set{" "}
              <code className="rounded bg-white/70 px-1 py-0.5 font-label text-[10px]">
                NEXT_PUBLIC_API_URL
              </code>{" "}
              in Vercel to your FastAPI URL and redeploy. Answers are never
              fabricated.
            </p>
            <p className="mt-1 font-label text-[9px] text-on-surface-variant">
              API base: {API_BASE}
              {API_CONFIGURED ? "" : " (default)"}
            </p>
          </div>
        )}

        <div className="mt-4 flex items-center justify-between px-1">
          <span className="font-label text-[10px] font-bold uppercase tracking-wider text-on-surface-variant">
            Authorized knowledge nodes ({meta.source_count}/{meta.source_count})
          </span>
          <span className="font-label text-[10px] font-semibold text-secondary">
            {meta.chunk_count} chunks indexed
          </span>
        </div>

        <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
          {meta.sources.map((source) => {
            const copy = SOURCE_COPY[source.id] ?? {
              label: source.title,
              sub: "Indexed page",
            };
            return (
              <div
                key={source.id}
                className="flex min-w-0 items-center justify-between gap-2 rounded-xl border border-outline-variant/40 bg-surface/80 p-2.5 shadow-tech-sm transition-colors hover:bg-surface-container"
              >
                <div className="flex min-w-0 items-center gap-2.5">
                  <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-secondary-container/20 text-secondary">
                    <span
                      className="material-symbols-outlined text-[17px]"
                      aria-hidden="true"
                    >
                      check_circle
                    </span>
                  </div>
                  <div className="min-w-0">
                    <p className="truncate font-headline text-[11px] font-semibold text-on-surface">
                      {copy.label}
                    </p>
                    <p className="truncate font-label text-[9px] text-on-surface-variant">
                      {copy.sub} · {source.chunks} chunks
                    </p>
                  </div>
                </div>
                <span className="flex-shrink-0 rounded-full bg-secondary-container/20 px-2 py-0.5 font-label text-[9px] font-bold uppercase tracking-wider text-secondary">
                  Indexed
                </span>
              </div>
            );
          })}
        </div>

        <div className="mt-4 flex flex-col items-center justify-between gap-3 border-t border-surface-container-high/60 pt-4 sm:flex-row">
          <div className="flex items-center gap-2 text-[11px] font-label text-on-surface-variant">
            <span
              className={`h-2 w-2 animate-pulse rounded-full ${
                online ? "bg-secondary" : "bg-primary"
              }`}
            />
            <span>
              {online
                ? `${meta.source_count}/${meta.source_count} sources indexed · API ready`
                : offline
                  ? "Frontend ready · API offline"
                  : "Checking backend…"}
            </span>
          </div>
          <button
            type="button"
            onClick={onEnter}
            className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-neon-pink via-primary to-neon-purple px-5 py-2.5 font-headline text-xs font-semibold text-white shadow-cta transition-all hover:scale-[1.02] hover:brightness-105 active:scale-95 sm:w-auto"
          >
            Enter research assistant
            <span
              className="material-symbols-outlined text-[16px]"
              aria-hidden="true"
            >
              arrow_forward
            </span>
          </button>
        </div>
      </div>
    </section>
  );
}
