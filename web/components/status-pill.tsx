import type { ApiStatus } from "@/lib/types";

const COPY: Record<
  ApiStatus,
  { label: string; dot: string; className: string }
> = {
  online: {
    label: "Knowledge Base Online",
    dot: "bg-sage",
    className: "border-sage/20 bg-sage-soft text-sage-deep",
  },
  checking: {
    label: "Connecting",
    dot: "bg-amber animate-pulse",
    className: "border-line bg-white text-muted",
  },
  offline: {
    label: "Knowledge Base Offline",
    dot: "bg-alert",
    className: "border-line bg-white text-muted",
  },
};

export function StatusPill({ status }: { status: ApiStatus }) {
  const copy = COPY[status];

  return (
    <span
      role="status"
      aria-live="polite"
      className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-1 text-[11px] font-medium ${copy.className}`}
    >
      <span
        className={`h-1.5 w-1.5 rounded-full ${copy.dot}`}
        aria-hidden="true"
      />
      {copy.label}
    </span>
  );
}
