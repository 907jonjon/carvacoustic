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
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppNav userEmail={user.email ?? null} />
      <div style={{ display: 'flex', flex: 1, flexDirection: 'column' }}>{children}</div>
    </div>
  );
}
