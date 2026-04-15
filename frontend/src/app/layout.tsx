import type { Metadata } from "next";
import "./globals.css";
import AuthGuard from "@/components/AuthGuard";
import LayoutContent from "@/components/LayoutContent";

export const metadata: Metadata = {
  title: "Lottery Lab - Sistema Predittivo",
  description: "Dashboard predittiva per Lotto Italiano e VinciCasa",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="it">
      <body className="antialiased" style={{ background: "var(--bg)", color: "var(--text)" }}>
        <AuthGuard>
          <LayoutContent>{children}</LayoutContent>
        </AuthGuard>
      </body>
    </html>
  );
}
