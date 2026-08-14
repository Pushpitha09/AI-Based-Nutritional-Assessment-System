import { Link, useLocation } from "react-router-dom";
import { Leaf, LayoutDashboard, UtensilsCrossed, Activity, FlaskConical, ClipboardList, CalendarDays, TrendingUp, LogOut } from "lucide-react";
import { useAuth } from "../AuthContext";

const navItems = [
  { icon: LayoutDashboard, label: "Dashboard", path: null },
  { icon: UtensilsCrossed, label: "Food diary", path: "/dashboard" },
  { icon: Activity, label: "Symptoms", path: null },
  { icon: FlaskConical, label: "Lab results", path: "/lab-results" },
  { icon: ClipboardList, label: "Assessment", path: null },
  { icon: CalendarDays, label: "Meal plan", path: null },
  { icon: TrendingUp, label: "Progress", path: null },
];

export default function Sidebar() {
  const { user, logOut } = useAuth();
  const location = useLocation();

  return (
    <aside className="dash-sidebar">
      <div>
        <div className="brand-mark small on-sidebar">
          <Leaf size={19} strokeWidth={2.2} />
          nutri<span>sense</span>
        </div>
        <p className="sidebar-username">{user?.first_name} {user?.last_name}</p>

        <nav className="sidebar-nav">
          {navItems.map(({ icon: Icon, label, path }) => {
            const isActive = path === location.pathname;
            if (!path) {
              return (
                <div key={label} className="sidebar-link disabled">
                  <Icon size={17} />
                  {label}
                  <span className="soon-tag">soon</span>
                </div>
              );
            }
            return (
              <Link key={label} to={path} className={isActive ? "sidebar-link active" : "sidebar-link"}>
                <Icon size={17} />
                {label}
              </Link>
            );
          })}
        </nav>
      </div>

      <button className="btn-logout" onClick={logOut}>
        <LogOut size={15} /> Sign out
      </button>
    </aside>
  );
}
