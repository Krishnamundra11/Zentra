import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "../services/api";

function TripCard({ trip }) {
  return (
    <div className="card p-6 flex flex-col gap-2 hover:shadow-md transition-shadow duration-200">
      <span className="text-[10px] font-mono font-bold uppercase tracking-[2px] text-brand-500">
        {trip.place_name || "Unknown place"}
      </span>
      <h3 className="text-lg font-bold text-gray-900 leading-snug">
        {trip.title || "Travel Plan"}
      </h3>
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span>📅 {trip.duration_days} day{trip.duration_days !== 1 ? "s" : ""}</span>
        <span>·</span>
        <span>{new Date(trip.created_at).toLocaleDateString("en-US", {
          year: "numeric", month: "short", day: "numeric"
        })}</span>
      </div>
      <Link
        to={`/itinerary/${trip.id}`}
        className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-brand-500 hover:text-brand-700 hover:underline transition-colors"
      >
        View itinerary →
      </Link>
    </div>
  );
}

export default function Profile() {
  const [trips, setTrips]     = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);

  useEffect(() => {
    api.get("/itinerary/saved")
      .then((r) => setTrips(Array.isArray(r.data) ? r.data : []))
      .catch(() => setError("Could not load saved trips."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="max-w-4xl mx-auto px-6 py-12 pb-20">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <span className="section-label">Account</span>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 mt-1">My Trips</h1>
        </div>
        <Link to="/" className="btn-primary text-sm px-5 py-2.5">
          + Discover new place
        </Link>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-24">
          <div className="spinner" />
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div className="card p-6 text-center text-red-500 text-sm">{error}</div>
      )}

      {/* Empty state */}
      {!loading && !error && trips.length === 0 && (
        <div className="card p-16 flex flex-col items-center gap-4 text-center">
          <div className="text-6xl">🗺</div>
          <h2 className="text-xl font-bold text-gray-800">No saved trips yet</h2>
          <p className="text-gray-500 text-sm max-w-xs">
            Upload a tourist place photo and we'll plan your whole trip — then save it here.
          </p>
          <Link to="/" className="btn-primary mt-2">
            Discover a destination
          </Link>
        </div>
      )}

      {/* Trip grid */}
      {!loading && trips.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {trips.map((trip) => (
            <TripCard key={trip.id} trip={trip} />
          ))}
        </div>
      )}

    </main>
  );
}
