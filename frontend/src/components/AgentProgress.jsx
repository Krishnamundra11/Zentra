import clsx from "clsx";

const TOOL_LABELS = {
  search_nearby_attractions: { emoji: "🗺", label: "Searching nearby attractions" },
  search_hotels:             { emoji: "🏨", label: "Finding hotels & resorts" },
  search_homestays:          { emoji: "🏡", label: "Searching homestays" },
  search_restaurants:        { emoji: "🍽", label: "Finding restaurants" },
  get_travel_info:           { emoji: "ℹ️", label: "Gathering travel info" },
  get_booking_links:         { emoji: "🔗", label: "Fetching booking options" },
};

export default function AgentProgress({ wsEvents }) {
  const toolEvents = wsEvents.filter((e) => e.event === "agent_tool_called");
  const agentStarted = wsEvents.some((e) => e.event === "agent_started");

  return (
    <div className="card p-6 mb-6 animate-fade-in border-l-4 border-brand-500">
      {/* Header */}
      <div className="flex items-center gap-4 mb-5">
        <div className="flex-shrink-0 w-10 h-10 rounded-full border-4 border-brand-200 border-t-brand-500 animate-spin" />
        <div>
          <h3 className="font-bold text-gray-900 text-base">AI Agent Planning Your Trip</h3>
          <p className="text-sm text-gray-400">Autonomously researching the best options…</p>
        </div>
      </div>

      {/* Tool stream */}
      {agentStarted && (
        <ul className="space-y-1">
          {toolEvents.map((ev, i) => {
            const meta = TOOL_LABELS[ev.data?.tool] || { emoji: "⚙️", label: ev.data?.tool };
            return (
              <li key={i} className="flex items-center gap-3 py-2 border-b border-gray-100 text-sm text-gray-600">
                <span className="w-5 h-5 flex items-center justify-center rounded-full bg-brand-100 text-brand-600 text-xs font-bold flex-shrink-0">
                  ✓
                </span>
                <span>{meta.emoji}</span>
                <span>{meta.label}</span>
              </li>
            );
          })}
          <li className="flex items-center gap-3 py-2 text-sm text-brand-600 font-semibold">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse flex-shrink-0 ml-1.5" />
            <span>Thinking…</span>
          </li>
        </ul>
      )}
    </div>
  );
}
