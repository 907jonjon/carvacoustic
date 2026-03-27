import Link from "next/link";
import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { Button } from "@/components/ui/button";

const modeLabels: Record<string, string> = {
  wall_art: "Wall Art",
  cabinet_front_panel: "Cabinet Front Panel",
  architectural_face_panel: "Architectural Face Panel",
};

export default async function ProjectPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const { data: project, error } = await supabase
    .from("projects")
    .select("*")
    .eq("id", id)
    .single();

  if (error || !project) notFound();

  const { data: versions } = await supabase
    .from("project_versions")
    .select("id, version_number, notes, created_at")
    .eq("project_id", id)
    .order("version_number", { ascending: false });

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      {/* Breadcrumb */}
      <Link href="/app" className="text-sm text-gray-500 hover:text-gray-700">
        ← Projects
      </Link>

      {/* Header */}
      <div className="mt-4 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{project.name}</h1>
          <p className="mt-1 text-sm text-gray-500">
            {modeLabels[project.mode] ?? project.mode} &bull; {project.units}
          </p>
        </div>
        <div className="flex gap-2">
          <Link href={`/app/projects/${id}/edit`}>
            <Button>Open editor</Button>
          </Link>
          <Link href={`/app/projects/${id}/exports`}>
            <Button variant="secondary">Exports</Button>
          </Link>
        </div>
      </div>

      {/* Version history */}
      <section className="mt-10">
        <h2 className="text-sm font-semibold uppercase tracking-wide text-gray-500">
          Version history
        </h2>
        {versions && versions.length > 0 ? (
          <ul className="mt-3 divide-y divide-gray-100 rounded-lg border border-gray-200 bg-white">
            {versions.map((v) => (
              <li
                key={v.id}
                className="flex items-center justify-between px-5 py-4"
              >
                <div>
                  <span className="text-sm font-medium text-gray-900">
                    v{v.version_number}
                  </span>
                  {v.notes && (
                    <span className="ml-3 text-sm text-gray-500">{v.notes}</span>
                  )}
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(v.created_at).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="mt-3 text-sm text-gray-500">
            No saved versions yet. Open the editor and save a checkpoint.
          </p>
        )}
      </section>
    </main>
  );
}
