import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "localhost:3000";
  const protocol = requestHeaders.get("x-forwarded-proto") || (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;
  return {
    title: { default: "Ultra Brain v0.9", template: "%s · Ultra Brain" },
    description: "Ultra Brain v0.9 Official UI Studio and OS Ecosystem world interface",
    icons: { icon: "/favicon.png", shortcut: "/favicon.png" },
    openGraph: { title: "Ultra Brain v0.9", description: "Official UI Studio · OS Ecosystem", images: [`${origin}/og.png`] },
    twitter: { card: "summary_large_image", title: "Ultra Brain v0.9", description: "Official UI Studio · OS Ecosystem", images: [`${origin}/og.png`] },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
