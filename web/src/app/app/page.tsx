import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import { ProjectCard } from "@/components/project/project-card";
import { Button } from "@/components/ui/button";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { data: projects, error } = await supabase
    .from("projects")
    .select("*")
    .eq("owner_id", user!.id)
    .order("updated_at", { ascending: false });

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Projects</h1>
          <p className="mt-1 text-sm text-gray-500">
            Your decorative panel projects.
          </p>
        </div>
        <Link href="/app/projects/new">
          <Button>New project</Button>
        </Link>
      </div>

      {error && (
        <div className="mt-6 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          Failed to load projects: {error.message}
        </div>
      )}

      {!error && projects && projects.length === 0 && (
        <div className="mt-16 flex flex-col items-center gap-4 text-center">
          <div className="rounded-full bg-gray-100 p-6">
            <svg
              className="h-10 w-10 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
              />
            </svg>
          </div>
          <p className="text-gray-600">No projects yet.</p>
          <Link href="/app/projects/new">
            <Button>Create your first project</Button>
          </Link>
        </div>
      )}

      {!error && projects && projects.length > 0 && (
        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))}
        </div>
      )}
    </main>
  );
}
