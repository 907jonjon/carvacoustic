import Link from "next/link";
import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

export default async function ExportsPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: project, error } = await supabase
    .from("projects")
    .select("id, name")
    .eq("id", id)
    .single();

  if (error || !project) notFound();

  const { data: bundles } = await supabase
    .from("export_bundles")
    .select("*")
    .eq("project_id", id)
    .order("created_at", { ascending: false });

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <Link
        href={`/app/projects/${id}`}
        className="text-sm text-gray-500 hover:text-gray-700"
      >
        ← {project.name}
      </Link>

      <h1 className="mt-4 text-2xl font-bold text-gray-900">Exports</h1>
      <p className="mt-1 text-sm text-gray-500">
        DXF, SVG, PDF, and JSON manifest bundles for this project.
      </p>

      {bundles && bundles.length > 0 ? (
        <ul className="mt-6 divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white">
          {bundles.map((b) => (
            <li
              key={b.id}
              className="flex items-center justify-between px-5 py-4"
            >
              <div>
                <span className="text-sm font-medium text-gray-900 font-mono">
                  {b.storage_path.split("/").pop()}
                </span>
                <span className="ml-3 text-xs text-gray-400">
                  {new Date(b.created_at).toLocaleString()}
                </span>
              </div>
              <span className="text-xs text-gray-400">
                {b.version_id ? `version ${b.version_id.slice(0, 8)}` : "draft"}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="mt-8 rounded-lg border border-dashed border-gray-300 bg-white px-8 py-12 text-center">
          <p className="text-sm text-gray-500">No exports yet.</p>
          <p className="mt-1 text-xs text-gray-400">
            Exports will appear here after geometry is generated (Milestone B).
          </p>
          <Link
            href={`/app/projects/${id}/edit`}
            className="mt-4 inline-block text-sm text-brand-600 hover:underline"
          >
            Open editor
          </Link>
        </div>
      )}
    </main>
  );
}
