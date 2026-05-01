import clsx from "clsx";

export default function RecoGrid({ items = [], ctaLabel = "Select" }) {
  if (!items.length) {
    return (
      <div className="text-center py-12 text-gray-400 text-sm">
        No results found.
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
      {items.map((item, i) => (
        <div
          key={i}
          className="card p-5 flex flex-col gap-2 hover:shadow-md transition-shadow duration-200 animate-slide-up"
          style={{ animationDelay: `${i * 60}ms` }}
        >
          {item.badge && (
            <span className="badge-green self-start">{item.badge}</span>
          )}

          <h4 className="text-base font-bold text-gray-900 leading-snug mt-1">
            {item.title}
          </h4>

          {item.subtitle && (
            <p className="text-sm text-gray-500">{item.subtitle}</p>
          )}

          {item.detail && (
            <p className="text-sm text-gray-700 font-medium">{item.detail}</p>
          )}

          <div className="mt-auto pt-3">
            {item.url ? (
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm font-semibold text-brand-500 hover:text-brand-700 hover:underline transition-colors"
              >
                {ctaLabel} <span>↗</span>
              </a>
            ) : item.onSelect ? (
              <button
                onClick={item.onSelect}
                className="inline-flex items-center gap-1 text-sm font-semibold text-brand-500 hover:text-brand-700 hover:underline transition-colors bg-none border-none p-0 cursor-pointer"
              >
                {ctaLabel} →
              </button>
            ) : null}
          </div>
        </div>
      ))}
    </div>
  );
}
