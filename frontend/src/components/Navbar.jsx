import { Link, useLocation } from "react-router-dom";
import clsx from "clsx";

const NAV_LINKS = [
  { to: "/",        label: "Discover" },
  { to: "/profile", label: "My Trips" },
];

export default function Navbar() {
  const { pathname } = useLocation();

  return (
    <nav className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 group">
          <span className="text-2xl">🌍</span>
          <span className="text-xl font-extrabold tracking-tight text-gray-900 group-hover:text-brand-500 transition-colors">
            TravelLens
          </span>
        </Link>
        <div className="flex items-center gap-1">
          {NAV_LINKS.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={clsx(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150",
                pathname === to
                  ? "bg-brand-50 text-brand-600 font-semibold"
                  : "text-gray-500 hover:text-gray-900 hover:bg-gray-100"
              )}
            >
              {label}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
