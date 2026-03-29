import { NextResponse } from "next/server";
import { stripe } from "@/lib/stripe/server";
import { createClient as createServerClient } from "@supabase/supabase-js";
import type Stripe from "stripe";

function createAdminClient() {
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!
  );
}

async function getUserIdByCustomer(stripeCustomerId: string): Promise<string | null> {
  const admin = createAdminClient();
  const { data } = await admin
    .from("billing_customers")
    .select("user_id")
    .eq("stripe_customer_id", stripeCustomerId)
    .limit(1)
    .single();
  return data?.user_id ?? null;
}

async function upsertSubscription(
  userId: string,
  sub: Stripe.Subscription
) {
  const admin = createAdminClient();

  // In Stripe v21+, period info lives on subscription items, not the subscription itself
  const item = sub.items.data[0];
  const periodStart = item?.current_period_start
    ? new Date(item.current_period_start * 1000).toISOString()
    : null;
  const periodEnd = item?.current_period_end
    ? new Date(item.current_period_end * 1000).toISOString()
    : null;

  await admin
    .from("subscriptions")
    .upsert(
      {
        user_id: userId,
        stripe_subscription_id: sub.id,
        status: sub.status,
        plan: "pro",
        current_period_start: periodStart,
        current_period_end: periodEnd,
        updated_at: new Date().toISOString(),
      },
      { onConflict: "stripe_subscription_id" }
    );
}

/**
 * POST /api/stripe/webhook
 * Handles Stripe webhook events for subscription lifecycle.
 */
export async function POST(request: Request) {
  const body = await request.text();
  const sig = request.headers.get("stripe-signature");

  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    console.error("STRIPE_WEBHOOK_SECRET is not set");
    return NextResponse.json({ error: "Webhook secret not configured" }, { status: 500 });
  }

  if (!sig) {
    return NextResponse.json({ error: "Missing stripe-signature header" }, { status: 400 });
  }

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(body, sig, webhookSecret);
  } catch (err) {
    console.error("Webhook signature verification failed:", err);
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as Stripe.Checkout.Session;
      if (session.mode !== "subscription" || !session.customer || !session.subscription) break;

      const customerId = typeof session.customer === "string" ? session.customer : session.customer.id;
      const userId = await getUserIdByCustomer(customerId);
      if (!userId) {
        console.error("No user found for Stripe customer:", customerId);
        break;
      }

      const subscriptionId = typeof session.subscription === "string"
        ? session.subscription
        : session.subscription.id;

      const sub = await stripe.subscriptions.retrieve(subscriptionId);
      await upsertSubscription(userId, sub);
      break;
    }

    case "customer.subscription.updated": {
      const sub = event.data.object as Stripe.Subscription;
      const customerId = typeof sub.customer === "string" ? sub.customer : sub.customer.id;
      const userId = await getUserIdByCustomer(customerId);
      if (!userId) {
        console.error("No user found for Stripe customer:", customerId);
        break;
      }
      await upsertSubscription(userId, sub);
      break;
    }

    case "customer.subscription.deleted": {
      const sub = event.data.object as Stripe.Subscription;
      const customerId = typeof sub.customer === "string" ? sub.customer : sub.customer.id;
      const userId = await getUserIdByCustomer(customerId);
      if (!userId) {
        console.error("No user found for Stripe customer:", customerId);
        break;
      }
      const admin = createAdminClient();
      await admin
        .from("subscriptions")
        .update({ status: "canceled", updated_at: new Date().toISOString() })
        .eq("stripe_subscription_id", sub.id);
      break;
    }
  }

  return NextResponse.json({ received: true }, { status: 200 });
}
