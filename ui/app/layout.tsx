import type { Metadata } from "next";
import { headers } from "next/headers";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const requestHeaders = await headers();
  const host = requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "localhost:3000";
  const protocol = requestHeaders.get("x-forwarded-proto") || (host.startsWith("localhost") ? "http" : "https");
  const origin = `${protocol}://${host}`;
  return {
    title: { default: "Ultra Brain v0.95", template: "%s · Ultra Brain" },
    description: "Ultra Brain v0.95 Advanced Theme and Visual World Engine",
    icons: { icon: "/favicon.png", shortcut: "/favicon.png" },
    openGraph: { title: "Ultra Brain v0.95", description: "Advanced Theme · Visual World Engine", images: [`${origin}/og.png`] },
    twitter: { card: "summary_large_image", title: "Ultra Brain v0.95", description: "Advanced Theme · Visual World Engine", images: [`${origin}/og.png`] },
  };
}

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}
