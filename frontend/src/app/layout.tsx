import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

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
        <div className="flex min-h-screen">
          <Sidebar />
          <main className="flex-1 min-w-0 md:pl-60">
            <div className="max-w-5xl mx-auto px-5 py-8 md:px-8 pb-24 md:pb-8">
              {children}
            </div>
          </main>
        </div>
      </body>
    </html>
  );
}
