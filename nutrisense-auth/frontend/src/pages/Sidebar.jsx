import {
  Link,
  useLocation, useNavigate
} from "react-router-dom";

import {
  Leaf,
  LayoutDashboard,
  UtensilsCrossed,
  FlaskConical,
  ClipboardList,
  CalendarDays,
  TrendingUp,
  UserRound,
  LogOut,
} from "lucide-react";

import { useAuth } from "../AuthContext";

const navItems = [
  {
    icon: LayoutDashboard,
    label: "Dashboard",
    path: "/dashboard",
  },
  {
    icon: UtensilsCrossed,
    label: "Food diary",
    path: "/food-diary",
  },
  {
    icon: FlaskConical,
    label: "Lab results",
    path: "/lab-results",
  },
  {
    icon: ClipboardList,
    label: "Assessment",
    path: "/assessment",
  },
  {
    icon: UserRound,
    label: "Profile",
    path: "/profile",
  },
  {
    icon: CalendarDays,
    label: "Meal plan",
    path: "/meal-plan",
  },
  {
    icon: TrendingUp,
    label: "Progress",
    path: "/progress",
  },
];

export default function Sidebar() {
  const { user, logOut } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  function handleLogout() {
  logOut();
  navigate("/");
}

  return (
    <aside className="dash-sidebar">
      <div>
        <div className="brand-mark small on-sidebar">
          <Leaf size={19} strokeWidth={2.2} />
          nutri<span>sense</span>
        </div>

        <p className="sidebar-username">
          {user?.first_name} {user?.last_name}
        </p>

        <nav className="sidebar-nav">
          {navItems.map(
            ({ icon: Icon, label, path }) => {
              if (!path) {
                return (
                  <div
                    key={label}
                    className="sidebar-link disabled"
                  >
                    <Icon size={17} />
                    {label}
                    <span className="soon-tag">
                      soon
                    </span>
                  </div>
                );
              }

              const isActive =
                location.pathname === path;

              return (
                <Link
                  key={label}
                  to={path}
                  className={
                    isActive
                      ? "sidebar-link active"
                      : "sidebar-link"
                  }
                >
                  <Icon size={17} />
                  {label}
                </Link>
              );
            }
          )}
        </nav>
      </div>

      <button
        className="btn-logout"
        onClick={handleLogout}
      >
        <LogOut size={15} />
        Sign out
      </button>
    </aside>
  );
}