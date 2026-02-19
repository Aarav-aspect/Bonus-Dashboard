import { createAuthClient } from "better-auth/react";

// Auth client for client-side authentication operations
export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_BASE_URL || "http://localhost:3000",
});
