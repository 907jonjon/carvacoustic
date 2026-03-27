import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { ProjectEditor } from "./project-editor";

export default async function EditPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const supabase = await createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const { data: project, error } = await supabase
    .from("projects")
    .select("*")
    .eq("id", id)
    .eq("owner_id", user!.id)
    .single();

  if (error || !project) notFound();

  const { data: latestVersion } = await supabase
    .from("project_versions")
    .select("version_number")
    .eq("project_id", id)
    .order("version_number", { ascending: false })
    .limit(1)
    .single();

  return (
    <ProjectEditor
      project={project}
      latestVersionNumber={latestVersion?.version_number ?? 0}
    />
  );
}
