import { DISCLAIMER } from "@/lib/constants";
import type { ApiStatus } from "@/lib/types";

import { ApiPill } from "./api-pill";

export function Header({ apiStatus }: { apiStatus: ApiStatus }) {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-surface-container-high/60 bg-white/80 backdrop-blur-xl shadow-[0_4px_24px_rgba(121,40,202,0.06)]">
      <div className="mx-auto flex h-16 w-full max-w-7xl items-center justify-between gap-3 px-4 sm:px-6">
        <div className="flex min-w-0 items-center gap-2.5">
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-tr from-neon-pink via-[#e40a65] to-neon-purple text-white shadow-neon-pink">
            <span
              className="material-symbols-outlined text-[20px]"
              aria-hidden="true"
            >
              account_balance
            </span>
          </div>
          <div className="flex min-w-0 flex-col">
            <div className="flex items-center gap-2">
              <span className="bg-gradient-to-r from-on-surface to-primary bg-clip-text font-display text-[18px] font-bold leading-none tracking-tight text-transparent">
                Arth AI
              </span>
              <span className="rounded-full bg-primary-fixed px-2 py-0.5 font-label text-[9px] font-bold uppercase tracking-widest text-primary">
                v2.4 Core
              </span>
            </div>
            <span className="mt-0.5 truncate font-label text-[9px] font-semibold uppercase tracking-wider text-on-surface-variant sm:text-[10px]">
              HDFC Mutual Fund Research Assistant
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden items-center gap-1.5 rounded-full border border-neon-cyan/40 bg-surface-container-low px-3 py-1.5 shadow-sm md:flex">
            <span className="h-2 w-2 rounded-full bg-neon-cyan shadow-[0_0_8px_#00e5ff]" />
            <span className="whitespace-nowrap font-label text-[11px] font-medium text-on-surface">
              {DISCLAIMER}
            </span>
          </div>
          <ApiPill status={apiStatus} />
          <div className="hidden h-9 w-9 items-center justify-center rounded-full border border-neon-pink/30 bg-gradient-to-tr from-surface-container-high to-surface-container-highest text-primary shadow-sm sm:flex">
            <span
              className="material-symbols-outlined text-[19px]"
              aria-hidden="true"
            >
              person
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-center gap-1.5 border-t border-surface-container-high/60 px-4 py-1.5 md:hidden">
        <span className="h-2 w-2 rounded-full bg-neon-cyan shadow-[0_0_8px_#00e5ff]" />
        <span className="text-center font-label text-[10px] font-semibold uppercase tracking-wider text-on-surface">
          {DISCLAIMER}
        </span>
      </div>
    </header>
  );
}
