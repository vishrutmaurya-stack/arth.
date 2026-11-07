"use client";

import { useEffect, useRef, useState } from "react";
import type { KeyboardEvent } from "react";

import { DISCLAIMER } from "@/lib/constants";

import { ArrowUpIcon } from "./icons";

interface ComposerProps {
  pending: boolean;
  onAsk: (question: string) => void;
}

export function Composer({ pending, onAsk }: ComposerProps) {
  const [value, setValue] = useState("");
  const [validation, setValidation] = useState<string | null>(null);
  const textarea = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const element = textarea.current;
    if (!element) {
      return;
    }
    element.style.height = "auto";
    element.style.height = `${Math.min(element.scrollHeight, 160)}px`;
  }, [value]);

  function submit() {
    const question = value.trim();
    if (!question) {
      setValidation("Type a question to get started.");
      textarea.current?.focus();
      return;
    }
    if (pending) {
      return;
    }
    setValidation(null);
    setValue("");
    onAsk(question);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !event.nativeEvent.isComposing
    ) {
      event.preventDefault();
      submit();
    }
  }

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-30 bg-gradient-to-t from-canvas via-canvas/95 to-transparent pb-[env(safe-area-inset-bottom)] pt-8">
      <div className="pointer-events-auto mx-auto w-full max-w-3xl px-4 pb-4 sm:px-6 sm:pb-5">
        <form
          onSubmit={(event) => {
            event.preventDefault();
            submit();
          }}
          className="rounded-[22px] border border-line bg-white shadow-composer transition-shadow focus-within:border-sage/35 focus-within:ring-4 focus-within:ring-sage/10"
        >
          <div className="flex items-end gap-2 p-2 pl-4">
            <textarea
              ref={textarea}
              rows={1}
              value={value}
              onChange={(event) => {
                setValue(event.target.value);
                if (validation) {
                  setValidation(null);
                }
              }}
              onKeyDown={onKeyDown}
              placeholder="Ask anything about HDFC Mutual Funds..."
              aria-label="Ask a question about HDFC Mutual Funds"
              className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent py-3 text-[15px] leading-6 text-ink outline-none placeholder:text-muted"
            />
            <button
              type="submit"
              disabled={pending || value.trim().length === 0}
              aria-label="Send question"
              className={`mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white disabled:cursor-not-allowed ${
                pending
                  ? "bg-sage"
                  : "bg-sage hover:bg-sage-deep disabled:bg-line disabled:text-muted/50"
              }`}
            >
              {pending ? (
                <span
                  className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"
                  aria-hidden="true"
                />
              ) : (
                <ArrowUpIcon className="h-4 w-4" />
              )}
            </button>
          </div>
        </form>

        {validation && (
          <p role="alert" className="mt-2 px-1 text-[11.5px] text-alert">
            {validation}
          </p>
        )}

        <div className="mt-2.5 flex items-center justify-between gap-3 px-1">
          <p className="text-[11.5px] text-muted">{DISCLAIMER}</p>
          <p className="hidden text-[11px] text-muted sm:block">
            Enter to send · Shift + Enter for a new line
          </p>
        </div>
      </div>
    </div>
  );
}
