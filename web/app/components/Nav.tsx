"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const LINKS = [
  { href: "/", label: "Forecast" },
  { href: "/explore", label: "Explore" },
  { href: "/ask", label: "Ask" },
  { href: "/journal", label: "Journal" },
  { href: "/account", label: "Account" },
  { href: "/gates", label: "Gates" },
  { href: "/glossary", label: "Glossary" },
  { href: "/review-dossier/latest", label: "Dossier" },
  { href: "/decisions", label: "Decisions" },
  { href: "/moderation", label: "Moderation" },
];

export default function Nav() {
  const path = usePathname();
  return (
    <nav className="nav">
      <span className="brand">orcast</span>
      {LINKS.map((l) => (
        <Link key={l.href} href={l.href} className={path === l.href ? "active" : ""}>
          {l.label}
        </Link>
      ))}
    </nav>
  );
}
