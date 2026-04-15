"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";

export default function LayoutContent({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const isLogin = pathname === "/login";

  if (isLogin) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="flex-1 min-w-0 md:pl-60">
        <div className="max-w-5xl mx-auto px-5 py-8 md:px-8 pb-24 md:pb-8">
          {children}
        </div>
      </main>
    </div>
  );
}
