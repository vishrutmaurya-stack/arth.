import { DISCLAIMER } from "@/lib/constants";

export function Footer({ count }: { count: number }) {
  return (
    <footer className="relative z-10 w-full border-t border-surface-container-high/60 bg-white/70 backdrop-blur-md">
      <div className="mx-auto flex w-full max-w-7xl flex-col items-center justify-between gap-1 px-4 py-4 text-center font-label text-[10px] text-on-surface-variant sm:flex-row sm:px-6 sm:text-left">
        <p>
          <strong className="font-semibold text-on-surface">Arth AI</strong> ·{" "}
          {DISCLAIMER}
        </p>
        <p>Sourced strictly from the indexed Groww pages · {count} chunks</p>
      </div>
    </footer>
  );
}
