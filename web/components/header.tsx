import type { ApiStatus } from "@/lib/types";

import { BrandMark } from "./brand-mark";
import { BookIcon } from "./icons";
import { StatusPill } from "./status-pill";

export function Header({ apiStatus }: { apiStatus: ApiStatus }) {
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-canvas/85 backdrop-blur-md">
      <div className="mx-auto flex h-16 w-full max-w-5xl items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex items-center gap-2.5">
          <BrandMark className="h-8 w-8" />
          <span className="text-[17px] font-semibold tracking-[-0.02em] text-ink">
            Arth AI
          </span>
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          <span className="hidden items-center gap-1.5 text-[11.5px] font-medium text-muted md:flex">
            <BookIcon className="h-3.5 w-3.5" />
            HDFC Mutual Fund Knowledge Base
          </span>
          <span
            className="hidden h-4 w-px bg-line md:block"
            aria-hidden="true"
          />
          <StatusPill status={apiStatus} />
        </div>
      </div>
    </header>
  );
}
