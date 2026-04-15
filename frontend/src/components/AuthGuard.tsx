"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";

export default function AuthGuard({
  children,
}: {
  children: React.ReactNode;
}) {
  const [checked, setChecked] = useState(false);
  const [authed, setAuthed] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const token = localStorage.getItem("lottery_token");
    if (token) {
      setAuthed(true);
    } else if (pathname !== "/login") {
      router.replace("/login");
    }
    setChecked(true);
  }, [pathname, router]);

  if (!checked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-lotto-blue border-t-transparent rounded-full spin" />
      </div>
    );
  }

  if (pathname === "/login") {
    return <>{children}</>;
  }

  if (!authed) {
    return null;
  }

  return <>{children}</>;
}
