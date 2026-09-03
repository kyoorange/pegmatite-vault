import { NavLink, Outlet } from "react-router-dom";

import HealthStatus from "../components/HealthStatus";

const navigation = [
  ["/", "HOME"],
  ["/vault", "VAULT"],
  ["/library", "LIBRARY"],
  ["/admin", "ADMIN"],
  ["/settings", "SETTING"],
];

export default function AppLayout() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <NavLink className="brand" to="/">
          PEGMATITE VAULT
        </NavLink>
        <NavLink className="primary-action" to="/specimens/new">
          ＋ 標本を追加
        </NavLink>
      </header>
      <aside className="sidebar" aria-label="メインメニュー">
        <nav>
          {navigation.map(([path, label]) => (
            <NavLink
              key={path}
              end={path === "/"}
              className={({ isActive }) =>
                isActive ? "nav-link nav-link--active" : "nav-link"
              }
              to={path}
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-content">
        <Outlet />
      </main>
      <footer className="app-footer">
        <span>v0.1.0</span>
        <HealthStatus />
      </footer>
    </div>
  );
}
