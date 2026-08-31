import { useState } from "react";
import {
  Link,
  useLocation,
  useNavigate,
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
  Menu,
  X,
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

  const [menuOpen, setMenuOpen] = useState(false);

  function handleLogout() {
    setMenuOpen(false);
    logOut();
    navigate("/");
  }

  function closeMenu() {
    setMenuOpen(false);
  }

  return (
    <>
      {/* Mobile menu button */}
      <button
        className="mobile-menu-btn"
        onClick={() => setMenuOpen(true)}
        aria-label="Open menu"
      >
        <Menu size={24} />
      </button>

      {/* Dark overlay on mobile */}
      {menuOpen && (
        <div
          className="sidebar-overlay"
          onClick={closeMenu}
        />
      )}

      <aside
        className={
          menuOpen
            ? "dash-sidebar mobile-open"
            : "dash-sidebar"
        }
      >
        <div>
          {/* Mobile close button */}
          <div className="sidebar-top-row">
            <div className="brand-mark small on-sidebar">
              <Leaf size={19} strokeWidth={2.2} />
              nutri<span>sense</span>
            </div>

            <button
              className="sidebar-close-btn"
              onClick={closeMenu}
              aria-label="Close menu"
            >
              <X size={22} />
            </button>
          </div>

          <p className="sidebar-username">
            {user?.first_name} {user?.last_name}
          </p>

          <nav className="sidebar-nav">
            {navItems.map(
              ({ icon: Icon, label, path }) => {
                const isActive =
                  location.pathname === path;

                return (
                  <Link
                    key={label}
                    to={path}
                    onClick={closeMenu}
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
    </>
  );
}