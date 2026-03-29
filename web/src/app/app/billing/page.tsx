import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { BillingActions } from "./BillingActions";

export default async function BillingPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  // Query the subscriptions table for an active subscription
  const { data: subscription } = await supabase
    .from("subscriptions")
    .select("*")
    .eq("user_id", user.id)
    .eq("status", "active")
    .maybeSingle();

  const isActive = !!subscription;

  return (
    <div className="mx-auto w-full max-w-2xl px-6 py-12">
      <h1 className="text-2xl font-bold text-gray-900">Billing</h1>
      <p className="mt-1 text-sm text-gray-500">
        Manage your plan and billing details.
      </p>

      <div className="mt-8 rounded-lg border border-gray-200 bg-white p-6">
        {isActive ? (
          <>
            <div className="flex items-center gap-2">
              <span className="inline-block rounded-full bg-brand-50 px-2.5 py-0.5 text-xs font-medium text-brand-700">
                Pro Plan
              </span>
              <span className="text-xs text-gray-500">
                Status: {subscription.status}
              </span>
            </div>
            {subscription.current_period_end && (
              <p className="mt-3 text-sm text-gray-600">
                Current period ends{" "}
                <time dateTime={subscription.current_period_end}>
                  {new Date(subscription.current_period_end).toLocaleDateString(
                    "en-US",
                    { year: "numeric", month: "long", day: "numeric" }
                  )}
                </time>
              </p>
            )}
            <div className="mt-6">
              <BillingActions mode="manage" />
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2">
              <span className="inline-block rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-700">
                Free Plan
              </span>
            </div>
            <p className="mt-3 text-sm text-gray-600">
              3 exports per month included. Upgrade to Pro for unlimited exports
              and priority support.
            </p>
            <div className="mt-6">
              <BillingActions mode="upgrade" />
            </div>
          </>
        )}
      </div>
    </div>
  );
}
