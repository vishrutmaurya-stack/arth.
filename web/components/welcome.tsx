import { EXAMPLES } from "@/lib/constants";
import type { ApiStatus } from "@/lib/types";

import { ErrorNotice } from "./error-notice";
import { ArrowUpRightIcon } from "./icons";

interface WelcomeProps {
  apiStatus: ApiStatus;
  pending: boolean;
  error: string | null;
  onAsk: (question: string) => void;
  onRetry: () => void;
}

export function Welcome({
  apiStatus,
  pending,
  error,
  onAsk,
  onRetry,
}: WelcomeProps) {
  return (
    <section className="flex flex-1 flex-col justify-center pb-6">
      <h1 className="max-w-2xl text-balance text-[34px] font-semibold leading-[1.06] tracking-[-0.035em] text-ink sm:text-[46px]">
        Understand your mutual funds.
      </h1>
      <p className="mt-4 max-w-xl text-[15px] leading-7 text-muted sm:text-base">
        Ask questions about HDFC Mutual Funds. Get clear, factual answers backed
        by indexed source documents.
      </p>

      {apiStatus === "offline" && (
        <div
          role="status"
          className="mt-6 flex flex-col gap-3 rounded-xl border border-line bg-white px-4 py-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <p className="text-[12.5px] leading-5 text-muted">
            <span className="font-medium text-ink">
              Knowledge base offline.
            </span>{" "}
            Answers are unavailable until the API reconnects.
          </p>
          <button
            type="button"
            onClick={onRetry}
            className="self-start rounded-full border border-line px-3 py-1.5 text-[11px] font-medium text-ink transition-colors hover:border-sage/40 hover:text-sage-deep focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30 sm:self-auto"
          >
            Retry
          </button>
        </div>
      )}

      <div className="mt-8 sm:mt-10">
        <p className="text-[10.5px] font-semibold uppercase tracking-[0.14em] text-muted">
          Try asking
        </p>
        <div className="mt-3 grid gap-2.5 sm:grid-cols-3">
          {EXAMPLES.map((example) => (
            <button
              key={example.question}
              type="button"
              disabled={pending}
              onClick={() => onAsk(example.question)}
              className="group relative flex min-h-[108px] flex-col justify-between rounded-2xl border border-line bg-white p-3.5 text-left shadow-soft transition-all duration-200 hover:-translate-y-0.5 hover:border-sage/30 hover:shadow-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/30 disabled:cursor-not-allowed disabled:opacity-60 sm:min-h-[136px] sm:p-4"
            >
              <span className="text-[10px] font-semibold uppercase tracking-[0.12em] text-sage">
                {example.category}
              </span>
              <span className="mt-4 block text-[13px] font-medium leading-[1.45] text-ink sm:text-[13.5px]">
                {example.question}
              </span>
              <ArrowUpRightIcon className="absolute right-3.5 top-3.5 h-4 w-4 text-muted/40 opacity-0 transition-opacity duration-200 group-hover:opacity-100" />
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mt-6">
          <ErrorNotice message={error} />
        </div>
      )}
    </section>
  );
}
