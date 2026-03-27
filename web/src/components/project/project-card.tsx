import Link from "next/link";
import type { Database } from "@/types/database";

type Project = Database["public"]["Tables"]["projects"]["Row"];

const modeLabels: Record<string, string> = {
  wall_art: "Wall Art",
  cabinet_front_panel: "Cabinet Front Panel",
  architectural_face_panel: "Architectural Face Panel",
};

export function ProjectCard({ project }: { project: Project }) {
  const updatedAt = new Date(project.updated_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });

  return (
    <Link
      href={`/app/projects/${project.id}`}
      className="block rounded-lg border border-gray-200 bg-white p-5 transition-shadow hover:shadow-md"
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-medium text-gray-900 truncate">{project.name}</h3>
        <span className="shrink-0 rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
          {project.units}
        </span>
      </div>
      <p className="mt-1 text-sm text-gray-500">
        {modeLabels[project.mode] ?? project.mode}
      </p>
      <p className="mt-3 text-xs text-gray-400">Updated {updatedAt}</p>
    </Link>
  );
}
