import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";

export default async function DashboardPage() {
  const session = await auth.api.getSession({ headers: await headers() });

  if (!session) {
    redirect("/login");
  }

  return (
    <div className="min-h-screen bg-primary-subtle">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="bg-white rounded-lg shadow-sm p-8 border border-grayscale-border-subtle">
          <h1 className="text-3xl font-bold text-grayscale-title mb-4">
            Welcome, {session.user.name}!
          </h1>
          <p className="text-grayscale-body mb-6">
            You have successfully logged in to your dashboard.
          </p>

          <div className="border-t border-grayscale-border pt-6">
            <h2 className="text-xl font-semibold text-grayscale-title mb-4">
              Account Information
            </h2>
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium text-grayscale-subtle">
                  Email:
                </span>
                <p className="text-grayscale-body">{session.user.email}</p>
              </div>
              <div>
                <span className="text-sm font-medium text-grayscale-subtle">
                  User ID:
                </span>
                <p className="text-grayscale-body font-mono text-sm">
                  {session.user.id}
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 p-4 bg-primary-subtle border border-border-primary-subtle rounded-lg">
            <h3 className="text-sm font-medium text-text-primary-label mb-2">
              Getting Started
            </h3>
            <p className="text-sm text-primary-darker">
              This is a basic authentication starter template. You can now add
              your own features and functionality!
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
