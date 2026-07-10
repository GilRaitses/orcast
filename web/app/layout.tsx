import type { Metadata } from "next";
import { headers } from "next/headers";
import { AuthKitProvider } from "@workos-inc/authkit-nextjs/components";
import "./globals.css";
import Nav from "./components/Nav";
import AuthStatus from "./components/AuthStatus";

function isOrcaStrikeStandalone(): boolean {
  return headers().get("x-orcast-standalone") === "1";
}

export const metadata: Metadata = {
  title: "orcast",
  description: "Orca encounter forecasting with provenance, gates, and community moderation.",
  openGraph: {
    title: "orcast",
    description: "Orca encounter forecasting with provenance, gates, and community moderation.",
    url: "https://orcast.aimez.ai",
    siteName: "orcast",
    images: [
      {
        url: "https://orcast.aimez.ai/social/og-preview.png",
        width: 1200,
        height: 630,
      },
    ],
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "orcast",
    description: "Orca encounter forecasting with provenance, gates, and community moderation.",
    images: ["https://orcast.aimez.ai/social/og-preview.png"],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  if (isOrcaStrikeStandalone()) {
    return (
      <html lang="en">
        <body>{children}</body>
      </html>
    );
  }

  return (
    <html lang="en">
      <body>
        <AuthKitProvider>
          <div className="topbar">
            <Nav />
            <AuthStatus />
          </div>
          {children}
        </AuthKitProvider>
      </body>
    </html>
  );
}
