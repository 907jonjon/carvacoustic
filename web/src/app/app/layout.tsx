import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { AppNav } from "@/components/layout/nav";

/** Layout for all /app/* routes. Verifies session server-side. */
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <div className="flex min-h-screen flex-col">
      <AppNav userEmail={user.email ?? null} />
      <div className="flex flex-1 flex-col">{children}</div>
    </div>
  );
}
