import Link from "next/link";

export default function LandingPage() {
  return (
    <main className="flex min-h-screen flex-col">
      {/* Header */}
      <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
        <span className="text-sm font-semibold text-gray-900">CarvAcoustic</span>
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

      {/* Hero */}
      <section className="flex flex-1 flex-col items-center justify-center px-6 py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900 sm:text-5xl">
          Decorative panels,
          <br />
          Vectric-ready.
        </h1>
        <p className="mt-5 max-w-xl text-lg text-gray-600">
          Design wave fields, contour bands, and slat-rib patterns for wall art,
          cabinet fronts, and architectural face panels. Export clean DXF/SVG
          ready for Vectric.
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
              title: "Three panel modes",
              body: "Wall art, cabinet front panels, architectural face panels.",
            },
            {
              title: "Three pattern families",
              body: "wave_field, contour_bands, slat_rib — all deterministic.",
            },
            {
              title: "Vectric handoff",
              body: "DXF, SVG, reference PDF, and JSON manifest — no G-code.",
            },
          ].map((f) => (
            <div key={f.title}>
              <h3 className="font-semibold text-gray-900">{f.title}</h3>
              <p className="mt-1 text-sm text-gray-500">{f.body}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-gray-100 px-6 py-6 text-center text-xs text-gray-400">
        © {new Date().getFullYear()} CarvAcoustic
      </footer>
    </main>
  );
}
