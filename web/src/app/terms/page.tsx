import Link from "next/link";

export default function TermsPage() {
  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-3xl font-bold tracking-tight text-gray-900">
        Terms of Service
      </h1>
      <p className="mt-2 text-sm text-gray-500">Last updated: March 2026</p>

      <section className="mt-10 space-y-8 text-sm leading-relaxed text-gray-700">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            1. Service Description
          </h2>
          <p className="mt-2">
            CarvAcoustic is a web-based design tool that helps you create
            profiled acoustic panel designs and export CNC-ready cut files (DXF,
            SVG, PDF). We provide the software; you supply the materials,
            machines, and craftsmanship.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            2. Account Responsibility
          </h2>
          <p className="mt-2">
            You are responsible for keeping your login credentials secure. Any
            activity under your account is your responsibility. If you suspect
            unauthorized access, contact us immediately.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            3. Subscription &amp; Billing
          </h2>
          <p className="mt-2">
            Paid plans are billed through Stripe on a monthly or annual basis.
            You can cancel anytime from your billing dashboard. When you cancel,
            your Pro access continues until the end of the current billing
            period. There are no cancellation fees.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            4. Acceptable Use
          </h2>
          <p className="mt-2">
            You agree not to misuse the service. This includes, but is not
            limited to: automated scraping or bot access, abusing API
            endpoints, or reselling generated files as part of a competing
            design-file service.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            5. Intellectual Property
          </h2>
          <p className="mt-2">
            You own the designs and files you create with CarvAcoustic. We own
            the platform, software, branding, and all underlying technology.
            Nothing in these terms transfers our IP rights to you, or yours to
            us.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            6. Limitation of Liability
          </h2>
          <p className="mt-2">
            CarvAcoustic generates digital cut files based on your
            configuration. We do not guarantee fitness for any particular
            material, machine, or application. You are solely responsible for
            verifying dimensions, material suitability, and machine safety
            before fabrication. To the fullest extent permitted by law,
            CarvAcoustic is not liable for any damages arising from your use of
            the generated files.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            7. Termination
          </h2>
          <p className="mt-2">
            We reserve the right to suspend or terminate accounts that violate
            these terms or engage in abusive behavior. You may delete your
            account at any time by contacting support.
          </p>
        </div>

        <div>
          <h2 className="text-base font-semibold text-gray-900">
            8. Changes to These Terms
          </h2>
          <p className="mt-2">
            We may update these terms from time to time. We will notify
            registered users of material changes via email. Continued use of the
            service after changes constitutes acceptance.
          </p>
        </div>
      </section>

      <p className="mt-12 text-sm text-gray-500">
        See also our{" "}
        <Link href="/privacy" className="text-brand-600 hover:underline">
          Privacy Policy
        </Link>
        .
      </p>
    </main>
  );
}
