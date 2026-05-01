import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import clsx from "clsx";
import useStore from "../store/useStore";
import { useAgent } from "../hooks/useAgent";
import AgentProgress from "../components/AgentProgress";
import PlaceCard from "../components/PlaceCard";
import RecoGrid from "../components/RecoGrid";

const PIPELINE_STEPS = [
  { key: "cv_started",        label: "Preprocessing image",           emoji: "🖼" },
  { key: "cv_matched",        label: "Running CLIP recognition",       emoji: "🔍" },
  { key: "agent_started",     label: "AI agent initialising",          emoji: "🤖" },
  { key: "agent_tool_called", label: "Gathering travel data",          emoji: "📡" },
  { key: "itinerary_ready",   label: "Building itinerary",             emoji: "📋" },
];

export default function Results() {
  const { taskId } = useParams();
  const navigate   = useNavigate();
  const {
    recognitionStatus, recognitionResult, wsEvents,
    agentStatus, agentTaskId,
  } = useStore();
  const { launchAgent } = useAgent();
  const [agentLaunched, setAgentLaunched] = useState(false);

  const completedKeys = new Set(wsEvents.map((e) => e.event));

  // Auto-launch agent on strong match
  useEffect(() => {
    if (recognitionStatus === "matched" && recognitionResult?.place && !agentLaunched) {
      setAgentLaunched(true);
      launchAgent(recognitionResult.place);
    }
  }, [recognitionStatus, recognitionResult]);

  // Navigate to itinerary when agent done
  useEffect(() => {
    if (agentStatus === "completed" && agentTaskId) {
      navigate(`/itinerary/${agentTaskId}`);
    }
  }, [agentStatus, agentTaskId]);

  return (
    <div className="max-w-6xl mx-auto px-6 py-10 pb-20">
      <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-8 items-start">

        {/* ── Sidebar pipeline tracker ── */}
        <aside className="card p-6 lg:sticky lg:top-24">
          <p className="text-[10px] font-mono font-bold uppercase tracking-[3px] text-gray-400 mb-4">
            Analysis progress
          </p>
          <ul className="space-y-1">
            {PIPELINE_STEPS.map((step, i) => {
              const done   = completedKeys.has(step.key);
              const active = !done && wsEvents.length > 0 &&
                i === PIPELINE_STEPS.findIndex((s) => !completedKeys.has(s.key));
              return (
                <li
                  key={step.key}
                  className={clsx(
                    "flex items-center gap-3 py-2.5 px-2 rounded-lg text-sm transition-colors",
                    done   && "text-brand-600 font-semibold",
                    active && "text-gray-900 bg-brand-50",
                    !done && !active && "text-gray-400"
                  )}
                >
                  <span className="w-5 text-center text-base flex-shrink-0">
                    {done ? "✅" : active ? step.emoji : "○"}
                  </span>
                  {step.label}
                </li>
              );
            })}
          </ul>
        </aside>

        {/* ── Main content ── */}
        <section className="min-h-[400px]">

          {/* Pending */}
          {recognitionStatus === "pending" && (
            <div className="flex flex-col items-center justify-center py-24 gap-4 animate-fade-in">
              <div className="spinner" />
              <p className="text-gray-500 font-medium">Analysing your image…</p>
              <p className="text-xs text-gray-400">This usually takes 5–10 seconds</p>
            </div>
          )}

          {/* Matched or likely */}
          {(recognitionStatus === "matched" || recognitionStatus === "likely") && recognitionResult?.place && (
            <div className="animate-fade-in">
              {recognitionStatus === "likely" && (
                <div className="mb-4 px-4 py-3 bg-amber-50 border border-amber-200 rounded-xl text-amber-700 text-sm font-medium">
                  ⚠️ We're fairly confident about this — but double-check the name below.
                </div>
              )}

              <PlaceCard
                place={recognitionResult.place}
                confidence={recognitionResult.confidence}
              />

              {/* Agent in progress */}
              {agentLaunched && agentStatus === "running" && (
                <AgentProgress wsEvents={wsEvents} />
              )}

              {/* Manual trigger if auto-launch failed */}
              {!agentLaunched && (
                <button
                  type="button"
                  onClick={() => { setAgentLaunched(true); launchAgent(recognitionResult.place); }}
                  className="btn-primary mt-4"
                >
                  Plan this trip →
                </button>
              )}
            </div>
          )}

          {/* Unknown — show similar places */}
          {recognitionStatus === "unknown" && (
            <div className="animate-fade-in">
              <div className="card p-8 mb-6 text-center">
                <div className="text-5xl mb-4">🤔</div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  We couldn't identify this place exactly
                </h2>
                <p className="text-gray-500 text-sm max-w-md mx-auto">
                  Our model wasn't confident enough. Here are visually similar destinations you might enjoy — pick one to plan a trip!
                </p>
              </div>

              <h3 className="text-sm font-bold text-gray-500 uppercase tracking-wider mb-3 font-mono">
                Similar destinations
              </h3>
              <RecoGrid
                items={(recognitionResult?.similar_places || []).map((p) => ({
                  title:    p.name,
                  subtitle: [p.city, p.country].filter(Boolean).join(", "),
                  badge:    `${Math.round(p.similarity * 100)}% similar`,
                  onSelect: () => {
                    setAgentLaunched(true);
                    launchAgent(p);
                  },
                }))}
                ctaLabel="Plan this trip"
              />

              {agentLaunched && agentStatus === "running" && (
                <div className="mt-8">
                  <AgentProgress wsEvents={wsEvents} />
                </div>
              )}
            </div>
          )}

        </section>
      </div>
    </div>
  );
}
