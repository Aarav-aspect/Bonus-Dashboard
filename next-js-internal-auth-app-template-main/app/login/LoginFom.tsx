"use client";
import React, { useActionState, JSX } from "react";
import { signInSocial } from "@/lib/actions/auth-actions";
import { MicrosoftIcon } from "./MicrosoftIcon";

type State = { ok: boolean; message?: string } | null;

export default function LoginForm(): JSX.Element {
  const [state, formAction, isPending] = useActionState<State, FormData>(
    async (_prev, formData) => {
      const provider = formData.get("provider") as "github" | "microsoft";
      try {
        await signInSocial(provider);
        return { ok: true, message: "Redirecting..." };
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : String(err ?? "Sign in failed");
        return { ok: false, message };
      }
    },
    null,
  );

  return (
    <div className="max-w-md w-full flex flex-col justify-center gap-4 shadow-md rounded-lg p-6 bg-white border border-grayscale-border-subtle">
      <div className="text-center mb-4">
        <h1 className="text-2xl font-bold text-grayscale-title mb-2">
          Welcome to Aspect Internal Tools
        </h1>
        <p className="text-grayscale-body">
          Sign in with your aspect microsoft account
        </p>
      </div>

      {/* Microsoft Sign In */}
      <form action={formAction}>
        <input type="hidden" name="provider" value="microsoft" />
        <button
          type="submit"
          disabled={isPending}
          className="w-full flex items-center justify-center gap-3 bg-white hover:bg-primary-subtle border border-primary text-primary hover:text-primary-darker font-medium py-3 px-4 rounded-md transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-grayscale-surface-disabled disabled:border-grayscale-border-disabled disabled:text-grayscale-disabled"
        >
          <MicrosoftIcon />
          {isPending ? "Signing in..." : "Continue with Aspect account"}
        </button>
      </form>

      {state?.message && (
        <div
          className={`text-sm text-center p-3 rounded-md ${
            state.ok
              ? "text-text-primary-label bg-primary-subtle border border-border-primary-subtle"
              : "text-text-error-label bg-error-subtle border border-border-error-subtle"
          }`}
        >
          {state.message}
        </div>
      )}
    </div>
  );
}
