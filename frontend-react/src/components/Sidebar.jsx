import { NavLink } from "react-router-dom";
import { useConnection } from "../lib/ConnectionContext.jsx";
import { UploadIcon, AskIcon, InsightsIcon, DriftIcon, HealthIcon, SettingsIcon } from "./icons.jsx";

const links = [
  { to: "/documents", label: "Documents", icon: UploadIcon },
  { to: "/ask", label: "Ask", icon: AskIcon },
  { to: "/insights", label: "Insights", icon: InsightsIcon },
  { to: "/drift", label: "Drift", icon: DriftIcon },
  { to: "/health", label: "Health", icon: HealthIcon },
  { to: "/connection", label: "Connection", icon: SettingsIcon },
];

export default function Sidebar() {
  const { status } = useConnection();
  const dotClass = status === "connected" || status === "ready" ? "ok" : status === "unreachable" || status === "not_ready" ? "bad" : "";

  return (
    <aside className="rail">
      <div className="rail-brand">
        <div className="mark">DI</div>
        <div className="name">Document Intelligence</div>
        <div className="sub">Ops Console</div>
      </div>
      <nav>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => "nav-item" + (isActive ? " active" : "")}>
            <Icon />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div className="rail-status">
        <span className={"dot " + dotClass} />
        <span>{status}</span>
      </div>
    </aside>
  );
}
