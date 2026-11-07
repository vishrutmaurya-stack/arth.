import type { Turn } from "@/lib/types";

import { BrandMark } from "./brand-mark";
import { ArrowUpRightIcon, ClockIcon, LinkIcon } from "./icons";

const DECISION_LABEL: Record<string, string> = {
  not_in_corpus: "Not in indexed pages",
  refuse_advice: "Advice guardrail",
  refuse_performance: "Performance guardrail",
  refuse_pii: "PII protected",
  refuse_empty: "Empty question",
  empty_index: "Index unavailable",
};

function updatedLine(value: string | null): string | null {
  if (!value) {
    return null;
  }
  if (value.startsWith("Last updated")) {
    return value;
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return `Last updated ${value}`;
  }

  const formatted = new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(parsed);

  return `Last updated ${formatted}`;
}

export function TurnCard({ turn }: { turn: Turn }) {
  const { question, result } = turn;
  const notice = DECISION_LABEL[result.decision];
  const href = result.citation_url || result.educational_link;
  const cited = result.citation_url
    ? result.hits.find((hit) => hit.url === result.citation_url)
    : undefined;
  const sourceTitle =
    cited?.title ||
    (result.citation_url ? "Groww source page" : "Educational resource");
  const sourceLabel = result.citation_url ? "Source" : "Learn more";
  const updated = updatedLine(result.last_updated);
  const paragraphs = result.answer
    .split(/\n{2,}/)
    .filter((part) => part.trim().length > 0);

  return (
    <article className="animate-rise">
      <div className="flex justify-end">
        <div className="max-w-[85%] rounded-2xl rounded-br-md border border-line bg-white/80 px-4 py-3 text-[14px] leading-6 text-ink shadow-soft">
          <p className="whitespace-pre-line break-words">{question}</p>
        </div>
      </div>

      <div className="mt-5">
        <div className="flex items-center gap-2">
          <BrandMark className="h-5 w-5" />
          <span className="text-[10.5px] font-semibold uppercase tracking-[0.12em] text-muted">
            Arth AI
          </span>
          {notice && (
            <span className="ml-auto rounded-full border border-line bg-white px-2 py-0.5 text-[10px] font-medium text-muted">
              {notice}
            </span>
          )}
        </div>

        <div className="mt-3 space-y-3 text-[15px] leading-7 text-ink sm:text-[15.5px]">
          {paragraphs.map((paragraph, index) => (
            <p key={index} className="whitespace-pre-line break-words">
              {paragraph}
            </p>
          ))}
        </div>

        {(href || updated) && (
          <div className="mt-4 border-t border-line pt-3">
            {href && (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                title={sourceTitle}
                className="group inline-flex max-w-full items-center gap-2.5 rounded-lg py-1 pr-1 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30"
              >
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md border border-line bg-white text-muted transition-colors group-hover:border-sage/30 group-hover:text-sage-deep">
                  <LinkIcon className="h-3.5 w-3.5" />
                </span>
                <span className="min-w-0">
                  <span className="block text-[9.5px] font-semibold uppercase tracking-[0.12em] text-muted">
                    {sourceLabel}
                  </span>
                  <span className="mt-0.5 block truncate text-[12.5px] font-medium text-ink underline decoration-line decoration-1 underline-offset-4 transition-colors group-hover:text-sage-deep group-hover:decoration-sage/40">
                    {sourceTitle}
                  </span>
                </span>
                <ArrowUpRightIcon className="h-3.5 w-3.5 shrink-0 text-muted/60 transition-colors group-hover:text-sage" />
              </a>
            )}

            {updated && (
              <p className="mt-2 flex items-center gap-1.5 text-[11px] text-muted">
                <ClockIcon className="h-3 w-3" />
                <span>{updated}</span>
              </p>
            )}
          </div>
        )}
      </div>
    </article>
  );
}
