import type { Metadata } from "next";
import { AuthKitProvider } from "@workos-inc/authkit-nextjs/components";
import "./globals.css";
import Nav from "./components/Nav";
import AuthStatus from "./components/AuthStatus";

export const metadata: Metadata = {
  title: "orcast",
  description: "Orca encounter forecasting with provenance, gates, and community moderation.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
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
