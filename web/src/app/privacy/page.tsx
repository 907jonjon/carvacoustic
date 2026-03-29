import Link from "next/link";

export default function PrivacyPage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900">
        Privacy Policy
      </h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: March 2026</p>

      <section className="mt-10 space-y-8 text-sm leading-relaxed text-gray-700">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            1. Data We Collect
          </h2>
          <p className="mt-2">
            We collect the minimum data needed to run the service:
          </p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>
              <strong>Account info</strong> &mdash; email address and
              authentication credentials.
            </li>
            <li>
              <strong>Project configurations</strong> &mdash; the panel designs
              you create and save.
            </li>
            <li>
              <strong>Usage events</strong> &mdash; actions like generating
              previews or exporting files, used for rate limiting and analytics.
            </li>
          </ul>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            2. How We Use Your Data
          </h2>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>Providing and improving the service.</li>
            <li>Processing billing through Stripe.</li>
            <li>Aggregate, anonymized analytics to understand usage patterns.</li>
          </ul>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            3. Third-Party Services
          </h2>
          <p className="mt-2">We rely on the following third parties:</p>
          <ul className="mt-2 list-disc space-y-1 pl-5">
            <li>
              <strong>Supabase</strong> &mdash; authentication and database
              hosting.
            </li>
            <li>
              <strong>Stripe</strong> &mdash; payment processing and
              subscription management.
            </li>
            <li>
              <strong>Vercel</strong> &mdash; application hosting and edge
              delivery.
            </li>
          </ul>
          <p className="mt-2">
            Each provider has its own privacy policy. We do not sell your data to
            any third party.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">4. Cookies</h2>
          <p className="mt-2">
            We use cookies only for Supabase authentication sessions. We do not
            use advertising or tracking cookies.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            5. Data Retention
          </h2>
          <p className="mt-2">
            Your account data and project files are retained while your account
            is active. If you request account deletion, we will remove your
            personal data within 30 days.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            6. Your Rights
          </h2>
          <p className="mt-2">
            You can request access to, correction of, or deletion of your
            personal data at any time by emailing us at{" "}
            <a
              href="mailto:support@carvacoustic.com"
              className="text-brand-600 hover:underline"
            >
              support@carvacoustic.com
            </a>
            .
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">7. Contact</h2>
          <p className="mt-2">
            For any privacy-related questions, reach us at{" "}
            <a
              href="mailto:support@carvacoustic.com"
              className="text-brand-600 hover:underline"
            >
              support@carvacoustic.com
            </a>
            .
          </p>
        </div>
      </section>

      <p className="mt-12 text-sm text-gray-500">
        See also our{" "}
        <Link href="/terms" className="text-brand-600 hover:underline">
          Terms of Service
        </Link>
        .
      </p>
    </main>
  );
}
