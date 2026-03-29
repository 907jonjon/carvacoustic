import Link from "next/link";

const plans = [
  {
    name: "Free",
    price: "$0",
    interval: "",
    description: "Get started designing panels at no cost.",
    features: [
      "3D design preview",
      "Full design editor",
      "3 exports per month",
      "Wave, contour, and slat-rib patterns",
    ],
    cta: "Get started",
    ctaHref: "/login",
    highlight: false,
  },
  {
    name: "Pro",
    price: "$19",
    interval: "/mo or $149/yr",
    description: "Unlimited exports and priority support for active makers.",
    features: [
      "Everything in Free",
      "Unlimited exports",
      "All surface types",
      "Priority support",
    ],
    cta: "Start Pro",
    ctaHref: "/app/billing",
    highlight: true,
  },
];

export default function PricingPage() {
  return (
    <main className="flex min-h-screen flex-col bg-gray-50">
      {/* Header */}
      <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
        <Link
          href="/"
          className="text-sm font-semibold text-gray-900 hover:text-brand-600"
        >
          CarvAcoustic
        </Link>
        <div className="flex items-center gap-3">
          <Link
            href="/login"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Sign in
          </Link>
          <Link
            href="/login"
            className="rounded-md bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700"
          >
            Get started
          </Link>
        </div>
      </header>

      {/* Pricing */}
      <section className="flex flex-1 flex-col items-center px-6 py-16">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900 sm:text-4xl">
          Simple, transparent pricing
        </h1>
        <p className="mt-3 max-w-md text-center text-base text-gray-600">
          Start free. Upgrade when you need unlimited exports.
        </p>

        <div className="mt-12 grid max-w-3xl gap-8 sm:grid-cols-2">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`flex flex-col rounded-lg border bg-white p-6 shadow-sm ${
                plan.highlight
                  ? "border-brand-600 ring-1 ring-brand-600"
                  : "border-gray-200"
              }`}
            >
              <h2 className="text-lg font-semibold text-gray-900">
                {plan.name}
              </h2>
              <p className="mt-1 text-sm text-gray-500">{plan.description}</p>
              <div className="mt-4">
                <span className="text-3xl font-bold text-gray-900">
                  {plan.price}
                </span>
                {plan.interval && (
                  <span className="text-sm text-gray-500">{plan.interval}</span>
                )}
              </div>
              <ul className="mt-6 flex flex-1 flex-col gap-2">
                {plan.features.map((f) => (
                  <li key={f} className="flex items-start gap-2 text-sm text-gray-700">
                    <span className="mt-0.5 text-brand-600">&#10003;</span>
                    {f}
                  </li>
                ))}
              </ul>
              <Link
                href={plan.ctaHref}
                className={`mt-6 block rounded-md px-4 py-2.5 text-center text-sm font-medium ${
                  plan.highlight
                    ? "bg-brand-600 text-white hover:bg-brand-700"
                    : "border border-gray-300 bg-white text-gray-700 hover:bg-gray-50"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        <p className="mt-10 max-w-md text-center text-sm text-gray-500">
          No long-term commitment. Cancel anytime from your billing
          dashboard&nbsp;&mdash; your Pro access continues until the end of the
          current billing period. No cancellation fees.
        </p>
      </section>

      <footer className="border-t border-gray-100 bg-white px-6 py-6 text-center text-xs text-gray-400">
        <span>&copy; {new Date().getFullYear()} CarvAcoustic</span>
        <span className="mx-2">&middot;</span>
        <Link href="/terms" className="hover:text-gray-600">Terms</Link>
        <span className="mx-2">&middot;</span>
        <Link href="/privacy" className="hover:text-gray-600">Privacy</Link>
      </footer>
    </main>
  );
}
