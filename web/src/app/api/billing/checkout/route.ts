import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { stripe } from "@/lib/stripe/server";
import { PLANS } from "@/lib/billing/plans";
import { z } from "zod";
import type { ApiError } from "@/types/schema";

function apiError(code: string, message: string, status = 400): NextResponse<ApiError> {
  return NextResponse.json({ error: { code, message } }, { status });
}

const RequestSchema = z.object({
  interval: z.enum(["monthly", "yearly"]),
});

/**
 * POST /api/billing/checkout
 * Creates a Stripe Checkout session for the Pro plan.
 */
export async function POST(request: Request) {
  const supabase = await createClient();
  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) return apiError("unauthenticated", "Authentication required.", 401);

  let body: unknown;
  try { body = await request.json(); } catch {
    return apiError("invalid_json", "Request body must be valid JSON.");
  }

  const parsed = RequestSchema.safeParse(body);
  if (!parsed.success) {
    return apiError("validation_error", parsed.error.errors.map((e) => e.message).join("; "));
  }

  const { interval } = parsed.data;
  const priceId = interval === "monthly"
    ? PLANS.pro.price_id_monthly
    : PLANS.pro.price_id_yearly;

  if (!priceId) {
    return apiError("config_error", "Stripe price ID is not configured for this interval.", 500);
  }

  // Look up or create Stripe customer
  const { data: existing } = await supabase
    .from("billing_customers")
    .select("stripe_customer_id")
    .eq("user_id", user.id)
    .limit(1)
    .single();

  let stripeCustomerId: string;

  if (existing) {
    stripeCustomerId = existing.stripe_customer_id;
  } else {
    const customer = await stripe.customers.create({
      email: user.email,
      metadata: { supabase_user_id: user.id },
    });
    stripeCustomerId = customer.id;

    await supabase
      .from("billing_customers")
      .insert({ user_id: user.id, stripe_customer_id: stripeCustomerId });
  }

  const origin = new URL(request.url).origin;

  const session = await stripe.checkout.sessions.create({
    mode: "subscription",
    customer: stripeCustomerId,
    line_items: [{ price: priceId, quantity: 1 }],
    success_url: `${origin}/app?billing=success`,
    cancel_url: `${origin}/app?billing=cancel`,
  });

  return NextResponse.json({ url: session.url });
}
