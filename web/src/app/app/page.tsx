import { createClient } from "@/lib/supabase/server";
import { DashboardBody } from "@/components/dashboard/DashboardBody";

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
    <DashboardBody
      projects={projects ?? []}
      error={error?.message}
    />
  );
}
