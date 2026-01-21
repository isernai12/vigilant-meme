import type { ReactNode } from "react";
import { redirect } from "next/navigation";
import { validateSession } from "../../../src/lib/auth";

export default async function AdminLayout({ children }: { children: ReactNode }) {
  const session = await validateSession();
  if (!session) {
    redirect("/admin/login");
  }
  return <>{children}</>;
}
