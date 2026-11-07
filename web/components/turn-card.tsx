import type { Turn } from "@/lib/types";

const BADGES: Record<string, { label: string; className: string }> = {
  answer: {
    label: "Grounded answer",
    className: "border-secondary/25 bg-secondary-container/15 text-secondary",
  },
  not_in_corpus: {
    label: "Not in indexed pages",
    className:
      "border-tertiary-container/30 bg-tertiary-fixed/25 text-[#6e5e00]",
  },
  refuse_advice: {
    label: "Advice blocked",
    className: "border-primary/25 bg-primary-fixed/50 text-primary",
  },
  refuse_performance: {
    label: "Performance blocked",
    className: "border-primary/25 bg-primary-fixed/50 text-primary",
  },
  refuse_pii: {
    label: "PII protected",
    className: "border-primary/25 bg-primary-fixed/50 text-primary",
  },
  refuse_empty: {
    label: "Empty question",
    className:
      "border-tertiary-container/30 bg-tertiary-fixed/25 text-[#6e5e00]",
  },
  empty_index: {
    label: "Index empty",
    className:
      "border-tertiary-container/30 bg-tertiary-fixed/25 text-[#6e5e00]",
  },
};

function updatedLine(value: string | null): string | null {
  if (!value) {
    return null;
  }
  return value.startsWith("Last updated")
    ? value
    : `Last updated from sources: ${value}`;
}

export function TurnCard({ turn }: { turn: Turn }) {
  const { question, result } = turn;
  const badge = BADGES[result.decision] ?? {
    label: "Grounded response",
    className: BADGES.answer.className,
  };
  const link = result.citation_url || result.educational_link;
  const linkLabel = result.citation_url
    ? "View source on Groww"
    : "Educational resource";
  const updated = updatedLine(result.last_updated);

  return (
    <article className="space-y-2.5">
      <div className="flex justify-end">
        <div className="max-w-[92%] rounded-2xl rounded-tr-md bg-gradient-to-br from-primary to-neon-purple px-4 py-3 text-white shadow-tech">
          <span className="mb-1 block font-label text-[9px] font-bold uppercase tracking-widest text-white/70">
            You
          </span>
          <p className="whitespace-pre-line break-words text-sm leading-relaxed">
            {question}
          </p>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-outline-variant/40 bg-white/95 shadow-tech">
        <div className="flex flex-wrap items-center justify-between gap-2 border-b border-surface-container-high/60 px-4 py-2.5">
          <div className="flex items-center gap-1.5 font-headline text-xs font-semibold text-on-surface">
            <span
              className="material-symbols-outlined text-[16px] text-primary"
              aria-hidden="true"
            >
              auto_awesome
            </span>
            Arth AI
          </div>
          <span
            className={`rounded-full border px-2 py-0.5 font-label text-[9px] font-bold uppercase tracking-wider ${badge.className}`}
          >
            {badge.label}
          </span>
        </div>

        <div className="px-4 py-3.5">
          <p className="whitespace-pre-line break-words text-sm leading-relaxed text-on-surface">
            {result.answer}
          </p>

          {link && (
            <a
              href={link}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-3 inline-flex items-center gap-1.5 rounded-lg border border-secondary/25 bg-secondary-container/10 px-2.5 py-1.5 font-label text-[11px] font-semibold text-secondary transition-colors hover:bg-secondary-container/25"
            >
              <span
                className="material-symbols-outlined text-[15px]"
                aria-hidden="true"
              >
                link
              </span>
              {linkLabel}
            </a>
          )}

          {updated && (
            <p className="mt-2 flex items-center gap-1 font-label text-[10px] text-on-surface-variant">
              <span
                className="material-symbols-outlined text-[13px]"
                aria-hidden="true"
              >
                schedule
              </span>
              {updated}
            </p>
          )}
        </div>

        {result.hits.length > 0 && (
          <details className="group border-t border-surface-container-high/60 bg-surface-container-low/50">
            <summary className="flex cursor-pointer list-none items-center justify-between gap-2 px-4 py-2 font-label text-[10px] font-semibold uppercase tracking-wider text-on-surface-variant [&::-webkit-details-marker]:hidden">
              Retrieval hits · {result.hits.length} chunks
              <span
                className="material-symbols-outlined text-[16px] transition-transform group-open:rotate-180"
                aria-hidden="true"
              >
                expand_more
              </span>
            </summary>
            <div className="space-y-2 px-4 pb-3">
              {result.hits.map((hit) => (
                <div
                  key={hit.chunk_id}
                  className="rounded-lg border border-outline-variant/30 bg-white/80 p-2.5"
                >
                  <div className="flex items-center justify-between gap-2 font-label text-[9px] font-semibold text-on-surface">
                    <span className="truncate">{hit.chunk_id}</span>
                    <span className="flex-shrink-0 text-primary">
                      score {hit.score.toFixed(4)}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate font-label text-[9px] text-on-surface-variant">
                    {hit.section} · {hit.title}
                  </p>
                  <p className="mt-1.5 line-clamp-4 text-[11px] leading-relaxed text-on-surface-variant">
                    {hit.text}
                  </p>
                </div>
              ))}
            </div>
          </details>
        )}
      </div>
    </article>
  );
}
