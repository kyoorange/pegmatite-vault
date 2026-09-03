import { NavLink } from "react-router-dom";

const resources = [
  ["/admin/minerals", "鉱物種"],
  ["/admin/mineral-classes", "鉱物分類"],
  ["/admin", "採集地"],
  ["/admin/acquisition-methods", "入手経路"],
];

export default function AdminResourceNav() {
  return (
    <nav className="admin-resources" aria-label="管理対象">
      {resources.map(([path, name]) => (
        <NavLink
          className={({ isActive }) =>
            isActive ? "admin-resource is-active" : "admin-resource"
          }
          end
          key={path}
          to={path}
        >
          <span>{name}</span>
          <small>管理画面を開く →</small>
        </NavLink>
      ))}
    </nav>
  );
}
