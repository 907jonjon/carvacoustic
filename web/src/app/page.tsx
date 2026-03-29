import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
        <span className="text-sm font-semibold text-gray-900">CarvAcoustic</span>
        <div className="flex items-center gap-3">
          <Link
            href="/pricing"
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Pricing
          </Link>
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

      {/* Hero */}
      <section className="flex flex-1 flex-col items-center justify-center px-6 py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Design to Fabrication
        </h1>
        <p className="mt-5 max-w-xl text-lg text-gray-600">
          Design profiled slat panels, preview in 3D, and export CNC-ready cut
          files.
        </p>
        <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
          <Link
            href="/login"
            className="rounded-md bg-brand-600 px-6 py-3 text-base font-medium text-white hover:bg-brand-700"
          >
            Start a project
          </Link>
          <Link
            href="/docs"
            className="rounded-md border border-gray-300 bg-white px-6 py-3 text-base font-medium text-gray-700 hover:bg-gray-50"
          >
            Read the docs
          </Link>
        </div>
      </section>

      {/* Feature strip */}
      <section className="border-t border-gray-100 bg-white px-6 py-12">
        <div className="mx-auto grid max-w-4xl gap-8 sm:grid-cols-3">
          {[
            {
              title: "3D Design Preview",
              body: "Shape your surface, see the slats in real-time 3D before committing.",
            },
            {
              title: "CNC-Ready Export",
              body: "DXF, SVG, and reference PDF — ready for your CNC workflow.",
            },
            {
              title: "Profiled Slat Panels",
              body: "Wave, terrain, ripple, and mountain surfaces with precise tab-and-slot joinery.",
            },
          ].map((f) => (
            <div key={f.title}>
              <h3 className="font-semibold text-gray-900">{f.title}</h3>
              <p className="mt-1 text-sm text-gray-500">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing CTA */}
      <section className="border-t border-gray-100 bg-gray-50 px-6 py-12 text-center">
        <h2 className="text-xl font-semibold text-gray-900">
          Ready to start making?
        </h2>
        <p className="mt-2 text-sm text-gray-600">
          Free to design. Upgrade when you need unlimited exports.
        </p>
        <Link
          href="/pricing"
          className="mt-4 inline-block rounded-md bg-brand-600 px-6 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
        >
          See pricing
        </Link>
      </section>

      <footer className="border-t border-gray-100 px-6 py-6 text-center text-xs text-gray-400">
        &copy; {new Date().getFullYear()} CarvAcoustic
      </footer>
    </main>
  );
}
