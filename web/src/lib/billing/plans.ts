export const PLANS = {
  free: {
    name: "Free",
    exports_per_month: 3,
    features: ["3D preview", "Design editor", "3 exports/month"],
  },
  pro: {
    name: "Pro",
    exports_per_month: Infinity,
    features: ["Unlimited exports", "Priority support", "All surface types"],
    price_id_monthly: process.env.STRIPE_PRO_PRICE_ID_MONTHLY ?? "",
    price_id_yearly: process.env.STRIPE_PRO_PRICE_ID_YEARLY ?? "",
  },
} as const;

export type PlanId = keyof typeof PLANS;
