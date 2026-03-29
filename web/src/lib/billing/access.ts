import { createClient } from "@/lib/supabase/server";
import { enableBilling } from "@/lib/flags";

export async function canExport(userId: string): Promise<{ allowed: boolean; reason?: string }> {
  if (!enableBilling) return { allowed: true }; // billing not enabled yet

  const supabase = await createClient();

  // Check for active subscription
  const { data: sub } = await supabase
    .from("subscriptions")
    .select("status, plan")
    .eq("user_id", userId)
    .in("status", ["active", "trialing"])
    .limit(1)
    .single();

  if (sub) return { allowed: true }; // Pro user

  // Free user -- check monthly export count
  const startOfMonth = new Date();
  startOfMonth.setDate(1);
  startOfMonth.setHours(0, 0, 0, 0);

  const { count } = await supabase
    .from("usage_events")
    .select("*", { count: "exact", head: true })
    .eq("user_id", userId)
    .eq("event_type", "export")
    .gte("created_at", startOfMonth.toISOString());

  const used = count ?? 0;
  if (used >= 3) {
    return {
      allowed: false,
      reason: "You've used all 3 free exports this month. Upgrade to Pro for unlimited exports.",
    };
  }

  return { allowed: true };
}
