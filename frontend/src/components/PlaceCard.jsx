import clsx from "clsx";

export default function PlaceCard({ place, confidence }) {
  const pct = Math.round((confidence || place.similarity || 0) * 100);
  const tier =
    pct >= 80 ? { bg: "bg-green-50", text: "text-green-700", border: "border-green-300" } :
    pct >= 50 ? { bg: "bg-amber-50",  text: "text-amber-700",  border: "border-amber-300" } :
                { bg: "bg-red-50",    text: "text-red-600",    border: "border-red-300" };

  return (
    <div className="card p-7 mb-6 animate-fade-in">
      <div className="flex justify-between items-start gap-4 mb-4">
        <div className="flex-1 min-w-0">
          <span className="section-label">Identified destination</span>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900 mt-1 truncate">
            {place.name}
          </h1>
          <p className="text-gray-500 mt-1 text-sm">
            {[place.city, place.country].filter(Boolean).join(", ")}
          </p>
        </div>

        {/* Confidence badge */}
        <div className={clsx(
          "flex-shrink-0 border-2 rounded-xl p-3 text-center min-w-[72px]",
          tier.bg, tier.border
        )}>
          <span className={clsx("block text-2xl font-extrabold", tier.text)}>{pct}%</span>
          <span className={clsx("block text-[10px] uppercase tracking-widest font-mono", tier.text)}>
            confidence
          </span>
        </div>
      </div>

      {place.description && (
        <p className="text-gray-600 text-sm leading-relaxed mb-4">{place.description}</p>
      )}

      <div className="flex flex-wrap gap-2">
        {place.lat && place.lng && (
          <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-500 text-xs px-3 py-1 rounded-full">
            📍 {place.lat.toFixed(4)}, {place.lng.toFixed(4)}
          </span>
        )}
        {place.category && (
          <span className="inline-flex items-center gap-1 bg-gray-100 text-gray-500 text-xs px-3 py-1 rounded-full">
            🏛 {place.category}
          </span>
        )}
      </div>
    </div>
  );
}
