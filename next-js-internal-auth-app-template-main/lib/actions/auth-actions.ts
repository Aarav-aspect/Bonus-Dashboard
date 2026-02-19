"use server";

import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { headers } from "next/headers";

export const signInSocial = async (provider: "github" | "microsoft") => {
  const { url } = await auth.api.signInSocial({
    body: {
      provider,
      callbackURL: "/dashboard",
    },
  });
  if (url) {
    redirect(url);
  }
};

export const signOut = async () => {
  const result = await auth.api.signOut({ headers: await headers() });
  return result;
};

export async function logoutAction() {
  try {
    await auth.api.signOut({
      headers: await headers(),
    });
  } catch (err: unknown) {
    console.error("Sign out error:", err);
    // fallthrough to redirect anyway
  }
  // redirect on server after sign out
  redirect("/login");
}
