import type { ApiStatus } from "@/lib/types";

const COPY: Record<
  ApiStatus,
  { label: string; dot: string; className: string }
> = {
  online: {
    label: "API online",
    dot: "bg-secondary shadow-[0_0_8px_#006b54]",
    className:
      "border-secondary/25 bg-secondary-container/15 text-secondary",
  },
  checking: {
    label: "Checking API",
    dot: "bg-tertiary-container animate-pulse",
    className:
      "border-tertiary-container/30 bg-tertiary-fixed/25 text-[#6e5e00]",
  },
  offline: {
    label: "API offline",
    dot: "bg-neon-pink shadow-[0_0_8px_#ff2d78]",
    className: "border-primary/25 bg-primary-fixed/50 text-primary",
  },
};

export function ApiPill({ status }: { status: ApiStatus }) {
  const copy = COPY[status];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-label text-[10px] font-bold uppercase tracking-wider ${copy.className}`}
      title={
        status === "offline"
          ? "The separately deployed Python RAG API is unreachable."
          : undefined
      }
    >
      <span className={`h-1.5 w-1.5 rounded-full ${copy.dot}`} />
      {copy.label}
    </span>
  );
}
