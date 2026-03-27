import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CarvAcoustic",
  description:
    "Decorative panel design tool — wall art, cabinet fronts, architectural panels.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
