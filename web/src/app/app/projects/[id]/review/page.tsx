import { notFound } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { SheetReview } from "./sheet-review";

export default async function ReviewPage({
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

  return <SheetReview project={project} />;
}
