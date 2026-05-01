import { useState, useRef, useCallback } from "react";
import { useRecognition } from "../hooks/useRecognition";
import useStore from "../store/useStore";
import clsx from "clsx";

const BUDGET_OPTIONS  = ["budget", "mid", "luxury"];
const STYLE_OPTIONS   = ["solo", "couple", "family", "group"];
const DIET_OPTIONS    = ["any", "vegetarian", "vegan"];

function ChipGroup({ options, value, onChange, labelFn }) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((o) => (
        <button
          key={o}
          type="button"
          onClick={() => onChange(o)}
          className={clsx(
            "px-4 py-1.5 rounded-full border text-sm transition-all duration-150",
            value === o
              ? "border-brand-500 bg-brand-50 text-brand-600 font-semibold"
              : "border-gray-200 bg-white text-gray-500 hover:border-brand-400"
          )}
        >
          {labelFn ? labelFn(o) : o.charAt(0).toUpperCase() + o.slice(1)}
        </button>
      ))}
    </div>
  );
}

function PrefLabel({ children }) {
  return (
    <label className="block text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2 font-mono">
      {children}
    </label>
  );
}

export default function Home() {
  const [dragOver, setDragOver]     = useState(false);
  const [preview, setPreview]       = useState(null);
  const [selectedFile, setFile]     = useState(null);
  const [uploading, setUploading]   = useState(false);
  const [error, setError]           = useState(null);
  const fileRef = useRef();

  const { upload }                    = useRecognition();
  const { preferences, setPreferences } = useStore();

  const handleFile = (file) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Please upload a JPG, PNG, or WebP image.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("File too large — max 10 MB.");
      return;
    }
    setError(null);
    setFile(file);
    setPreview(URL.createObjectURL(file));
  };

  const onDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  }, []);

  const onSubmit = async () => {
    if (!selectedFile || uploading) return;
    setUploading(true);
    try {
      await upload(selectedFile);
    } catch (err) {
      setError(err?.response?.data?.detail || "Upload failed. Please try again.");
      setUploading(false);
    }
  };

  return (
    <main className="max-w-3xl mx-auto px-6 py-12 pb-20">

      {/* Hero */}
      <section className="text-center mb-10">
        <span className="badge-green mb-4">AI-Powered Travel Discovery</span>
        <h1 className="text-5xl font-extrabold tracking-tight text-gray-900 mt-3 mb-3">
          Where is this place?
        </h1>
        <p className="text-gray-500 text-lg max-w-md mx-auto leading-relaxed">
          Upload a photo of any tourist destination — we'll identify it and plan your entire trip.
        </p>
      </section>

      {/* Drop Zone */}
      <section className="mb-8">
        <div
          onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
          onDragLeave={() => setDragOver(false)}
          onDrop={onDrop}
          onClick={() => !preview && fileRef.current?.click()}
          className={clsx(
            "relative rounded-2xl border-2 border-dashed transition-all duration-200 overflow-hidden cursor-pointer",
            preview
              ? "border-brand-500 border-solid h-72 p-0"
              : "h-52 flex flex-col items-center justify-center gap-3 p-8",
            dragOver ? "border-brand-500 bg-brand-50" : !preview && "border-gray-300 bg-gray-50 hover:border-brand-400 hover:bg-gray-100"
          )}
        >
          {preview ? (
            <>
              <img
                src={preview}
                alt="Preview"
                className="w-full h-full object-cover"
              />
              <button
                type="button"
                onClick={(e) => { e.stopPropagation(); fileRef.current?.click(); }}
                className="absolute bottom-3 right-3 bg-black/60 hover:bg-black/80 text-white text-xs font-semibold px-3 py-1.5 rounded-lg backdrop-blur-sm transition-colors"
              >
                Change photo
              </button>
            </>
          ) : (
            <>
              <div className="text-5xl">📸</div>
              <div className="text-center">
                <p className="text-gray-700 font-semibold text-base">Drag & drop a photo here</p>
                <p className="text-gray-400 text-sm mt-1">or click to browse — JPG, PNG, WebP · max 10 MB</p>
              </div>
            </>
          )}
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => handleFile(e.target.files[0])}
          />
        </div>

        {error && (
          <p className="text-red-500 text-sm mt-2 text-center">{error}</p>
        )}
      </section>

      {/* Preferences */}
      <section className="card p-7 mb-8">
        <h2 className="text-lg font-bold text-gray-900 mb-6">Your preferences</h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">

          <div>
            <PrefLabel>Budget</PrefLabel>
            <ChipGroup
              options={BUDGET_OPTIONS}
              value={preferences.budget}
              onChange={(v) => setPreferences({ budget: v })}
            />
          </div>

          <div>
            <PrefLabel>Travel style</PrefLabel>
            <ChipGroup
              options={STYLE_OPTIONS}
              value={preferences.travel_style}
              onChange={(v) => setPreferences({ travel_style: v })}
            />
          </div>

          <div>
            <PrefLabel>
              Duration — {preferences.duration_days} day{preferences.duration_days > 1 ? "s" : ""}
            </PrefLabel>
            <input
              type="range"
              min={1}
              max={14}
              value={preferences.duration_days}
              onChange={(e) => setPreferences({ duration_days: Number(e.target.value) })}
              className="w-full accent-brand-500 mt-1"
            />
            <div className="flex justify-between text-xs text-gray-400 mt-1">
              <span>1 day</span><span>14 days</span>
            </div>
          </div>

          <div>
            <PrefLabel>Diet</PrefLabel>
            <ChipGroup
              options={DIET_OPTIONS}
              value={preferences.diet}
              onChange={(v) => setPreferences({ diet: v })}
            />
          </div>

          <div className="sm:col-span-2">
            <label className="flex items-center gap-3 cursor-pointer group">
              <input
                type="checkbox"
                checked={preferences.accessibility}
                onChange={(e) => setPreferences({ accessibility: e.target.checked })}
                className="w-4 h-4 accent-brand-500 rounded"
              />
              <span className="text-sm text-gray-700 group-hover:text-gray-900 transition-colors">
                I have accessibility needs
              </span>
            </label>
          </div>

        </div>
      </section>

      {/* Submit */}
      <button
        type="button"
        disabled={!selectedFile || uploading}
        onClick={onSubmit}
        className={clsx(
          "w-full py-5 rounded-2xl text-lg font-bold tracking-tight transition-all duration-150",
          selectedFile && !uploading
            ? "bg-brand-500 text-white hover:bg-brand-600 active:scale-[0.99] shadow-lg shadow-brand-500/20"
            : "bg-gray-200 text-gray-400 cursor-not-allowed"
        )}
      >
        {uploading ? (
          <span className="flex items-center justify-center gap-3">
            <span className="w-5 h-5 rounded-full border-2 border-white/30 border-t-white animate-spin" />
            Analysing your photo…
          </span>
        ) : (
          "Identify & Plan My Trip →"
        )}
      </button>

    </main>
  );
}
