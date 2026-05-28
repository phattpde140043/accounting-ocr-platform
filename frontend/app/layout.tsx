import "./styles.css";
import type { ReactNode } from "react";

const navItems = [
  { href: "/", label: "Overview" },
  { href: "/dashboard", label: "Dashboard" },
  { href: "/accounting", label: "Accounting" },
  { href: "/accounting/review", label: "Review Queue" },
  { href: "/ai", label: "AI" },
  { href: "/admin", label: "Admin" }
];

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <aside className="sidebar">
          <div>
            <p className="eyebrow">Accounting</p>
            <h1>OCR Platform</h1>
          </div>
          <nav>
            {navItems.map((item) => (
              <a key={item.href} href={item.href}>
                {item.label}
              </a>
            ))}
          </nav>
          <div className="session-card">
            <span>Demo role</span>
            <strong>Admin</strong>
          </div>
        </aside>
        <main className="content">{children}</main>
      </body>
    </html>
  );
}
