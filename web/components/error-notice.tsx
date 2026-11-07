import { AlertIcon } from "./icons";

export function ErrorNotice({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="flex gap-2.5 rounded-xl border border-alert/15 bg-alert-soft px-4 py-3"
    >
      <AlertIcon className="mt-0.5 h-4 w-4 shrink-0 text-alert" />
      <div className="min-w-0">
        <p className="text-[12.5px] font-medium text-alert">
          We couldn’t complete that request.
        </p>
        <p className="mt-0.5 break-words text-[12px] leading-5 text-muted">
          {message}
        </p>
      </div>
    </div>
  );
}
