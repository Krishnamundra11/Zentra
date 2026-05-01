import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import clsx from "clsx";
import { getItinerary, getAgentStatus } from "../services/api";
import RecoGrid from "../components/RecoGrid";

const TABS = [
  { key: "itinerary",   label: "📅 Itinerary"     },
  { key: "attractions", label: "🗺 Attractions"    },
  { key: "stays",       label: "🏨 Where to Stay"  },
  { key: "food",        label: "🍽 Food"            },
  { key: "info",        label: "ℹ️ Travel Info"    },
];

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        "px-4 py-2.5 text-sm font-medium whitespace-nowrap border-b-2 transition-all duration-150",
        active
          ? "border-brand-500 text-brand-600 font-semibold"
          : "border-transparent text-gray-500 hover:text-gray-800 hover:border-gray-300"
      )}
    >
      {children}
    </button>
  );
}

function InfoRow({ icon, label, value }) {
  return (
    <div className="flex gap-4 py-4 border-b border-gray-100 last:border-0">
      <span className="text-xl flex-shrink-0">{icon}</span>
      <div>
        <p className="text-xs font-mono font-semibold uppercase tracking-wider text-gray-400 mb-0.5">{label}</p>
        <p className="text-sm text-gray-800">{value}</p>
      </div>
    </div>
  );
}

export default function Itinerary() {
  const { taskId }               = useParams();
  const [data, setData]          = useState(null);
  const [loading, setLoading]    = useState(true);
  const [activeTab, setActiveTab]= useState("itinerary");

  useEffect(() => {
    let interval;

    const poll = async () => {
      try {
        // First try to fetch directly (task might already be done)
        const res = await getItinerary(taskId);
        setData(res.data);
        setLoading(false);
        clearInterval(interval);
      } catch {
        // Not ready yet — poll agent status
        try {
          const { data: status } = await getAgentStatus(taskId);
          if (status.status === "completed") {
            const res = await getItinerary(taskId);
            setData(res.data);
            setLoading(false);
            clearInterval(interval);
          }
        } catch {}
      }
    };

    poll();
    interval = setInterval(poll, 3000);
    return () => clearInterval(interval);
  }, [taskId]);

  if (loading) {
    return (
      <div className="min-h-[60vh] flex flex-col items-center justify-center gap-4 px-6">
        <div className="spinner" />
        <p className="text-gray-700 font-semibold text-lg">Building your personalised itinerary…</p>
        <p className="text-gray-400 text-sm">The AI agent is gathering attractions, hotels, and restaurants</p>
      </div>
    );
  }

  const {
    place_name, itinerary = {},
    attractions = [], hotels = [], homestays = [],
    restaurants = [], travel_info = {}, booking_links = {},
  } = data;

  const days = itinerary?.itinerary || {};
  const tips = itinerary?.tips || [];
  const summary = itinerary?.summary || "";

  return (
    <main className="max-w-4xl mx-auto px-6 py-10 pb-20 animate-fade-in">

      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-8">
        <div>
          <span className="section-label">Your Travel Plan</span>
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 mt-1">
            {place_name}
          </h1>
          {summary && (
            <p className="text-gray-500 mt-2 max-w-xl text-sm leading-relaxed">{summary}</p>
          )}
        </div>

        <div className="flex flex-col gap-2">
          {booking_links?.hotels_link && (
            <a
              href={booking_links.hotels_link}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 bg-brand-500 text-white text-sm font-bold rounded-xl hover:bg-brand-600 transition-colors text-center"
            >
              Book Hotels ↗
            </a>
          )}
          {booking_links?.tours_link && (
            <a
              href={booking_links.tours_link}
              target="_blank"
              rel="noopener noreferrer"
              className="px-5 py-2.5 border border-brand-500 text-brand-600 text-sm font-bold rounded-xl hover:bg-brand-50 transition-colors text-center"
            >
              Book Tours ↗
            </a>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-8 flex gap-0 overflow-x-auto">
        {TABS.map((t) => (
          <TabButton key={t.key} active={activeTab === t.key} onClick={() => setActiveTab(t.key)}>
            {t.label}
          </TabButton>
        ))}
      </div>

      {/* ── Itinerary Tab ── */}
      {activeTab === "itinerary" && (
        <div className="space-y-8">
          {Object.entries(days).length === 0 ? (
            <p className="text-gray-400 text-sm">No itinerary data available.</p>
          ) : (
            Object.entries(days).map(([dayKey, activities]) => {
              const dayLabel = dayKey.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
              const acts = Array.isArray(activities) ? activities : [];
              return (
                <div key={dayKey} className="card overflow-hidden">
                  <div className="bg-brand-500 px-6 py-3">
                    <h2 className="text-white font-bold text-base">{dayLabel}</h2>
                  </div>
                  <ul className="divide-y divide-gray-100">
                    {acts.map((act, i) => (
                      <li key={i} className="flex items-start gap-4 px-6 py-4">
                        <span className="text-xs font-mono font-bold text-brand-500 min-w-[52px] mt-0.5 flex-shrink-0 bg-brand-50 px-2 py-1 rounded">
                          {act.time || "—"}
                        </span>
                        <div className="flex-1">
                          <p className="text-sm font-semibold text-gray-900">{act.activity}</p>
                          {act.duration_hrs && (
                            <p className="text-xs text-gray-400 mt-0.5">⏱ {act.duration_hrs}h</p>
                          )}
                          {act.notes && (
                            <p className="text-xs text-gray-500 mt-1 italic">{act.notes}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })
          )}

          {tips.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-2xl p-6">
              <h3 className="text-amber-800 font-bold text-base mb-3">💡 Local Tips</h3>
              <ul className="space-y-2">
                {tips.map((t, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-amber-900">
                    <span className="text-amber-400 flex-shrink-0 mt-0.5">•</span>
                    {t}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ── Attractions Tab ── */}
      {activeTab === "attractions" && (
        <RecoGrid
          items={attractions.map((a) => ({
            title:    a.name,
            subtitle: a.vicinity || a.address || "",
            badge:    a.rating ? `★ ${a.rating}` : undefined,
          }))}
        />
      )}

      {/* ── Stays Tab ── */}
      {activeTab === "stays" && (
        <div className="space-y-8">
          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-[2px] text-gray-400 mb-4">
              Hotels &amp; Resorts
            </h3>
            <RecoGrid
              ctaLabel="Book"
              items={hotels.map((h) => ({
                title:   h.name,
                subtitle: h.rating ? `★ ${h.rating}` : undefined,
                detail:  h.price_per_night ? `From $${h.price_per_night} / night` : undefined,
                url:     h.booking_url,
              }))}
            />
          </div>

          <div>
            <h3 className="text-xs font-mono font-bold uppercase tracking-[2px] text-gray-400 mb-4">
              Homestays &amp; Rentals
            </h3>
            <RecoGrid
              ctaLabel="View"
              items={homestays.map((h) => ({
                title:   h.name,
                badge:   h.host_rating ? `Host ★ ${h.host_rating}` : undefined,
                detail:  h.price_per_night ? `$${h.price_per_night} / night` : undefined,
                url:     h.url,
              }))}
            />
          </div>
        </div>
      )}

      {/* ── Food Tab ── */}
      {activeTab === "food" && (
        <RecoGrid
          items={restaurants.map((r) => ({
            title:    r.name,
            subtitle: r.vicinity || r.address || "",
            badge:    r.rating ? `★ ${r.rating}` : undefined,
            detail:   r.cuisine || undefined,
          }))}
        />
      )}

      {/* ── Info Tab ── */}
      {activeTab === "info" && (
        <div className="max-w-lg space-y-2">
          <div className="card p-6">
            {travel_info.best_season && (
              <InfoRow icon="🗓" label="Best Season"  value={travel_info.best_season} />
            )}
            {travel_info.how_to_reach && (
              <InfoRow icon="✈️" label="How to Reach" value={travel_info.how_to_reach} />
            )}
            {travel_info.safety && (
              <InfoRow icon="🛡" label="Safety"        value={travel_info.safety} />
            )}
          </div>

          {travel_info.local_tips?.length > 0 && (
            <div className="card p-6">
              <p className="text-xs font-mono font-bold uppercase tracking-wider text-gray-400 mb-3">
                Local Tips
              </p>
              <ul className="space-y-2">
                {travel_info.local_tips.map((t, i) => (
                  <li key={i} className="flex gap-2 text-sm text-gray-700">
                    <span className="text-brand-500 flex-shrink-0">•</span> {t}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {(booking_links?.hotels_link || booking_links?.tours_link) && (
            <div className="card p-6">
              <p className="text-xs font-mono font-bold uppercase tracking-wider text-gray-400 mb-4">
                Book Now
              </p>
              <div className="flex flex-wrap gap-3">
                {booking_links.hotels_link && (
                  <a
                    href={booking_links.hotels_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-brand-50 text-brand-600 text-sm font-semibold rounded-lg hover:bg-brand-100 transition-colors"
                  >
                    Hotels on Booking.com ↗
                  </a>
                )}
                {booking_links.tours_link && (
                  <a
                    href={booking_links.tours_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-4 py-2 bg-brand-50 text-brand-600 text-sm font-semibold rounded-lg hover:bg-brand-100 transition-colors"
                  >
                    Tours on Viator ↗
                  </a>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Back link */}
      <div className="mt-12 pt-6 border-t border-gray-100">
        <Link to="/" className="text-sm text-gray-400 hover:text-brand-500 transition-colors">
          ← Discover another destination
        </Link>
      </div>

    </main>
  );
}
