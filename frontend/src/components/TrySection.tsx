// src/components/TrySection.tsx
"use client";

import React, { useState, useRef } from "react";
import {
  streamAnalysis,
  downloadCSV,
  extractVideoId,
  AnalyzeOut,
  ProgressEvent,
} from "@/lib/api";
import { toast } from "react-toastify";
import QuotaDisplay from "@/components/QuotaDisplay";
import StorageMonitor from "@/components/StorageMonitor";
import ScrollReveal from "@/components/ScrollReveal";
import SentimentChart from "@/components/SentimentChart";

// ── Analysis depth options ────────────────────────────────────────────────────
const PERCENTAGE_OPTIONS = [
  { value: 0.25, label: "25%", description: "Quick • 25% of all comments" },
  { value: 0.5, label: "50%", description: "Balanced • 50% of all comments" },
  { value: 0.75, label: "75%", description: "Deep • 75% of all comments" },
  { value: 1.0, label: "100%", description: "Full • Up to 10k comments" },
];

// ── Analysis steps shown in the loading indicator ─────────────────────────────
const ANALYSIS_STEPS = [
  { key: "collecting", label: "Collecting comments", icon: "📥", minPct: 5, maxPct: 39 },
  { key: "model", label: "Running AI model", icon: "🤖", minPct: 40, maxPct: 79 },
  { key: "visuals", label: "Generating visuals", icon: "🎨", minPct: 80, maxPct: 94 },
  { key: "complete", label: "Completing results", icon: "✅", minPct: 95, maxPct: 100 },
];

function getStepFromProgress(pct: number): number {
  for (let i = ANALYSIS_STEPS.length - 1; i >= 0; i--) {
    if (pct >= ANALYSIS_STEPS[i].minPct) return i;
  }
  return 0;
}

// ── Stat card ─────────────────────────────────────────────────────────────────
interface StatCardProps {
  label: string;
  count: number;
  ratio: number;
  accent: string;
  icon: string;
}
function StatCard({ label, count, ratio, accent, icon }: StatCardProps) {
  return (
    <div
      style={{
        padding: "16px",
        borderRadius: "14px",
        border: `1px solid ${accent}44`,
        background: `${accent}14`,
        textAlign: "center",
        boxShadow: "0 4px 20px rgba(0,0,0,0.15)",
        backdropFilter: "blur(8px)",
      }}
    >
      <div style={{ fontSize: "24px", marginBottom: "4px" }}>{icon}</div>
      <div style={{ color: "rgba(245,245,245,0.85)", fontSize: "13px", fontWeight: 600 }}>{label}</div>
      <div style={{ fontWeight: 800, fontSize: "24px", color: accent, marginTop: "4px" }}>
        {count.toLocaleString()}
      </div>
      <div style={{ color: accent, fontSize: "13px", fontWeight: 700, marginTop: "2px" }}>
        {(ratio * 100).toFixed(1)}%
      </div>
    </div>
  );
}

// ── Loading indicator ─────────────────────────────────────────────────────────
interface LoadingIndicatorProps {
  progress: number;
  stepLabel: string;
  activeStep: number;
  elapsed: number;
  percentage: number;
}
function LoadingIndicator({ progress, stepLabel, activeStep, elapsed, percentage }: LoadingIndicatorProps) {
  let estRemainingStr = "Estimating...";
  if (elapsed > 0) {
    if (progress >= 10) {
      const estimatedTotal = (elapsed / progress) * 100;
      const remaining = Math.max(1, Math.round(estimatedTotal - elapsed));
      estRemainingStr = `~${remaining}s`;
    } else {
      const baseEst = percentage === 0.25 ? 10 : percentage === 0.5 ? 20 : percentage === 0.75 ? 30 : 45;
      const remaining = Math.max(1, baseEst - elapsed);
      estRemainingStr = `~${remaining}s`;
    }
  }

  return (
    <div
      style={{
        marginTop: "32px",
        width: "100%",
        maxWidth: "640px",
        padding: "24px",
        borderRadius: "16px",
        background: "rgba(17, 34, 64, 0.8)",
        border: "1px solid rgba(72, 149, 239, 0.3)",
        boxShadow: "0 20px 40px rgba(0,0,0,0.4), 0 0 20px rgba(72, 149, 239, 0.15)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
        <span style={{ fontSize: "14px", fontWeight: 600, color: "#F5F5F5" }}>
          {stepLabel || "Analyzing comments…"}
        </span>
        <span style={{ fontSize: "14px", fontWeight: 700, color: "#4895EF" }}>
          {progress}%
        </span>
      </div>

      <div
        style={{
          width: "100%",
          height: "8px",
          borderRadius: "4px",
          background: "rgba(255,255,255,0.1)",
          overflow: "hidden",
          marginBottom: "16px",
        }}
      >
        <div
          style={{
            width: `${progress}%`,
            height: "100%",
            borderRadius: "4px",
            background: "linear-gradient(90deg, #0474C4, #4895EF, #7209B7)",
            transition: "width 0.4s ease",
            boxShadow: "0 0 10px rgba(72, 149, 239, 0.8)",
          }}
        />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", color: "rgba(245,245,245,0.6)" }}>
        <span>Elapsed: {elapsed}s</span>
        <span>Est. Remaining: {estRemainingStr}</span>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "8px", marginTop: "16px" }}>
        {ANALYSIS_STEPS.map((step, idx) => {
          const isDone = progress >= step.maxPct;
          const isCurrent = activeStep === idx;
          return (
            <div
              key={step.key}
              style={{
                padding: "8px 4px",
                borderRadius: "8px",
                textAlign: "center",
                fontSize: "11px",
                background: isDone
                  ? "rgba(34, 197, 94, 0.15)"
                  : isCurrent
                  ? "rgba(72, 149, 239, 0.2)"
                  : "rgba(255,255,255,0.03)",
                border: `1px solid ${
                  isDone
                    ? "rgba(34, 197, 94, 0.4)"
                    : isCurrent
                    ? "rgba(72, 149, 239, 0.5)"
                    : "rgba(255,255,255,0.08)"
                }`,
                color: isDone ? "#4ADE80" : isCurrent ? "#A8C4EC" : "rgba(245,245,245,0.4)",
              }}
            >
              <div>{step.icon}</div>
              <div style={{ marginTop: "2px", fontWeight: isCurrent ? 700 : 500 }}>{step.label}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main TrySection Component ─────────────────────────────────────────────────
export default function TrySection(): React.ReactElement {
  const [url, setUrl] = useState("");
  const [percentage, setPercentage] = useState<number>(0.5);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stepLabel, setStepLabel] = useState("");
  const [activeStep, setActiveStep] = useState(0);
  const [elapsed, setElapsed] = useState(0);
  const [result, setResult] = useState<AnalyzeOut | null>(null);

  const cleanupRef = useRef<(() => void) | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) {
      toast.error("Please enter a YouTube video URL.");
      return;
    }

    try {
      extractVideoId(url.trim());
    } catch {
      toast.error("Invalid YouTube URL format. Please check the URL.");
      return;
    }

    setSubmitting(true);
    setProgress(5);
    setStepLabel("Connecting to YouTube…");
    setActiveStep(0);
    setElapsed(0);
    setResult(null);

    const startTime = Date.now();
    timerRef.current = setInterval(() => {
      setElapsed(Math.round((Date.now() - startTime) / 1000));
    }, 1000);

    cleanupRef.current = streamAnalysis(
      url.trim(),
      percentage,
      (evt: ProgressEvent) => {
        setProgress(evt.progress);
        setStepLabel(evt.step);
        setActiveStep(getStepFromProgress(evt.progress));
      },
      (data: AnalyzeOut) => {
        if (timerRef.current) clearInterval(timerRef.current);
        setResult(data);
        setSubmitting(false);
        setProgress(100);
        setActiveStep(ANALYSIS_STEPS.length - 1);
        const unitsUsed = 1 + Math.ceil((data.actual_analyzed || 100) / 100);
        if (typeof window !== "undefined" && (window as unknown as { updateQuotaImmediately?: (u: number) => void }).updateQuotaImmediately) {
          (window as unknown as { updateQuotaImmediately: (u: number) => void }).updateQuotaImmediately(unitsUsed);
        }
        toast.success("Analysis completed successfully!");
      },
      (errMsg: string) => {
        if (timerRef.current) clearInterval(timerRef.current);
        toast.error(errMsg);
        setSubmitting(false);
        setProgress(0);
      }
    );
  };

  const handleCancel = () => {
    if (cleanupRef.current) cleanupRef.current();
    if (timerRef.current) clearInterval(timerRef.current);
    setSubmitting(false);
    setProgress(0);
    toast.info("Analysis cancelled.");
  };

  const handleDownload = () => {
    if (!result) return;
    downloadCSV(result.video_id, percentage);
    toast.success("Downloading CSV report…");
  };

  const topKeywords = result?.visualizations?.top_keywords?.slice(0, 14) ?? [];

  return (
    <section
      id="try"
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "80px 20px",
        boxSizing: "border-box",
      }}
    >
      <StorageMonitor />

      <ScrollReveal variant="fade-up" duration={700}>
        <h2 className="section-title" style={{ fontSize: "56px", margin: 0 }}>
          Try the Social Sentiment
        </h2>
      </ScrollReveal>

      <ScrollReveal variant="fade-up" delay={150} duration={700}>
        <p
          style={{
            marginTop: "12px",
            fontSize: "17px",
            lineHeight: "1.6",
            color: "rgba(245,245,245,0.8)",
            maxWidth: "560px",
          }}
        >
          Paste a YouTube video link below, choose analysis depth, and watch the AI
          analyze sentiment in real time.
        </p>
      </ScrollReveal>

      {/* ── Form ── */}
      <ScrollReveal variant="scale-up" delay={250} duration={700} style={{ width: "100%", maxWidth: "720px" }}>
        <form onSubmit={onSubmit} style={{ marginTop: "28px", width: "100%" }}>
          {/* URL Input */}
          <div
            style={{
              position: "relative",
              width: "100%",
              height: "52px",
              borderRadius: "14px",
              background: "rgba(255,255,255,0.06)",
              border: "1px solid rgba(255,255,255,0.18)",
              boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05), 0 10px 30px rgba(0,0,0,0.25)",
              backdropFilter: "blur(6px)",
              marginBottom: "18px",
            }}
          >
            <input
              type="text"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Paste your YouTube video URL here…"
              aria-label="YouTube Video URL"
              disabled={submitting}
              style={{
                position: "absolute",
                inset: 0,
                width: "100%",
                height: "100%",
                border: "none",
                outline: "none",
                background: "transparent",
                color: "#F5F5F5",
                paddingLeft: "22px",
                paddingRight: "16px",
                fontSize: "15px",
                opacity: submitting ? 0.6 : 1,
                boxSizing: "border-box",
              }}
            />
          </div>

          {/* Depth Selector */}
          <div style={{ marginBottom: "20px" }}>
            <p style={{ color: "rgba(245,245,245,0.75)", fontSize: "14px", marginBottom: "10px" }}>
              Select analysis depth:
            </p>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px" }}>
              {PERCENTAGE_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setPercentage(opt.value)}
                  disabled={submitting}
                  style={{
                    padding: "10px 6px",
                    borderRadius: "10px",
                    border: percentage === opt.value ? "2px solid #4895EF" : "1px solid rgba(255,255,255,0.15)",
                    background: percentage === opt.value ? "rgba(72, 149, 239, 0.25)" : "rgba(255,255,255,0.04)",
                    color: percentage === opt.value ? "#FFFFFF" : "rgba(245,245,245,0.7)",
                    cursor: submitting ? "not-allowed" : "pointer",
                    transition: "all 0.2s ease",
                  }}
                >
                  <div style={{ fontSize: "16px", fontWeight: 700 }}>{opt.label}</div>
                  <div style={{ fontSize: "10px", opacity: 0.7, marginTop: "2px" }}>{opt.description}</div>
                </button>
              ))}
            </div>
            {percentage === 1.0 && (
              <p
                style={{
                  marginTop: "10px",
                  fontSize: "11px",
                  color: "#38BDF8",
                  opacity: 0.9,
                  textAlign: "center",
                  letterSpacing: "0.2px",
                }}
              >
                ℹ️ &nbsp;Max 10.000 comments per analysis (100%)
              </p>
            )}
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "12px", justifyContent: "center", marginTop: "24px" }}>
            <button
              type="submit"
              className="btn-gradient"
              style={{
                height: "48px",
                padding: "0 28px",
                borderRadius: "12px",
                fontWeight: 700,
                cursor: submitting ? "not-allowed" : "pointer",
                opacity: submitting ? 0.7 : 1,
                border: "none",
              }}
              disabled={submitting}
            >
              {submitting ? "Analyzing…" : `Analyze (${percentage * 100}%)`}
            </button>

            {submitting && (
              <button
                type="button"
                onClick={handleCancel}
                style={{
                  height: "48px",
                  padding: "0 20px",
                  borderRadius: "12px",
                  fontWeight: 600,
                  background: "rgba(239,68,68,0.15)",
                  border: "1px solid rgba(239,68,68,0.4)",
                  color: "#F87171",
                  cursor: "pointer",
                  fontSize: "14px",
                }}
              >
                Cancel
              </button>
            )}
          </div>

          <p style={{ marginTop: "16px", fontSize: "13px", color: "rgba(245,245,245,0.5)" }}>
            Example: https://www.youtube.com/watch?v=dQw4w9WgXcQ
          </p>

          <div style={{ maxWidth: "720px", width: "100%", marginTop: "12px" }}>
            <QuotaDisplay />
          </div>
        </form>
      </ScrollReveal>

      {/* ── Loading Progress Indicator ── */}
      {submitting && (
        <LoadingIndicator
          progress={progress}
          stepLabel={stepLabel}
          activeStep={activeStep}
          elapsed={elapsed}
          percentage={percentage}
        />
      )}

      {/* ── Results Display ── */}
      {result && !submitting && (
        <ScrollReveal variant="blur-in" duration={600} style={{ width: "100%", maxWidth: "1080px", marginTop: "36px" }}>
          <div
            style={{
              width: "100%",
              background: "rgba(17, 34, 64, 0.7)",
              border: "1px solid rgba(255,255,255,0.12)",
              borderRadius: "20px",
              padding: "32px",
              textAlign: "left",
              boxShadow: "0 20px 50px rgba(0,0,0,0.35)",
              backdropFilter: "blur(14px)",
            }}
          >
            {/* Header + Download Action */}
            <div
              style={{
                display: "flex",
                alignItems: "flex-start",
                justifyContent: "space-between",
                flexWrap: "wrap",
                gap: "16px",
                marginBottom: "24px",
                paddingBottom: "20px",
                borderBottom: "1px solid rgba(255,255,255,0.08)",
              }}
            >
              <div>
                <h3 style={{ fontSize: "22px", fontWeight: 700, color: "#F5F5F5", margin: "0 0 6px 0" }}>
                  📹 {result.video_title}
                </h3>
                <p style={{ fontSize: "14px", color: "rgba(245,245,245,0.7)", margin: "0 0 10px 0" }}>
                  📺 {result.channel_title} &nbsp;·&nbsp; Total comments: {result.total_comments.toLocaleString()} &nbsp;·&nbsp;
                  Analyzed: <strong style={{ color: "#4895EF" }}>{result.actual_analyzed.toLocaleString()}</strong> ({((result.actual_analyzed / Math.max(1, result.total_comments)) * 100).toFixed(1)}%)
                </p>

                {/* Model Badge */}
                <div
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "10px",
                    padding: "6px 14px",
                    borderRadius: "20px",
                    background: "rgba(255,255,255,0.05)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    fontSize: "12px",
                    color: "rgba(245,245,245,0.8)",
                  }}
                >
                  <span style={{ color: "#4895EF", fontWeight: 600 }}>🤖 Engine: Google Gemini 3.5 Flash-Lite</span>
                  <span style={{ opacity: 0.3 }}>|</span>
                  <span>Accuracy: <strong style={{ color: "#22C55E" }}>83.3%</strong></span>
                  <span style={{ opacity: 0.3 }}>|</span>
                  <span>Macro F1: <strong style={{ color: "#22C55E" }}>82.3%</strong></span>
                </div>
              </div>

              <button
                type="button"
                onClick={handleDownload}
                className="btn-gradient"
                style={{
                  height: "44px",
                  padding: "0 22px",
                  fontSize: "13px",
                  borderRadius: "10px",
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "8px",
                  border: "none",
                }}
              >
                <span>📥</span>
                <span>Download CSV Report</span>
              </button>
            </div>

            {/* 3 Stat Cards */}
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: "16px",
                marginBottom: "24px",
              }}
            >
              <StatCard
                label="Positive Sentiment"
                count={result.counts.positive}
                ratio={result.ratios.positive}
                accent="#22C55E"
                icon="😊"
              />
              <StatCard
                label="Neutral Sentiment"
                count={result.counts.neutral}
                ratio={result.ratios.neutral}
                accent="#F59E0B"
                icon="😐"
              />
              <StatCard
                label="Negative Sentiment"
                count={result.counts.negative}
                ratio={result.ratios.negative}
                accent="#EF4444"
                icon="😡"
              />
            </div>

            {/* Top Keywords Pills */}
            {topKeywords.length > 0 && (
              <div style={{ marginBottom: "28px" }}>
                <div style={{ fontSize: "14px", color: "rgba(245,245,245,0.75)", marginBottom: "10px", fontWeight: 600 }}>
                  🏷️ Top Keywords
                </div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {topKeywords.map((kw, i) => (
                    <span
                      key={kw.word || `kw-${i}`}
                      style={{
                        padding: "5px 12px",
                        borderRadius: "20px",
                        background: "rgba(72, 149, 239, 0.15)",
                        border: "1px solid rgba(72, 149, 239, 0.3)",
                        color: "#A8C4EC",
                        fontSize: "12px",
                        fontWeight: i < 3 ? 700 : 500,
                      }}
                    >
                      {kw.word} <span style={{ opacity: 0.6 }}>({kw.frequency})</span>
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Visualizations Grid & Sample Comments via SentimentChart */}
            <SentimentChart
              data={{ counts: result.counts, ratios: result.ratios }}
              wordCloudImage={
                result.visualizations?.wordcloud_base64
                  ? result.visualizations.wordcloud_base64.startsWith("data:")
                    ? result.visualizations.wordcloud_base64
                    : `data:image/png;base64,${result.visualizations.wordcloud_base64}`
                  : undefined
              }
              examples={result.examples.map((ex) => ({
                id: ex.text.slice(0, 16),
                author: ex.author,
                text: ex.text,
                sentiment: ex.prediction.label as "positive" | "neutral" | "negative",
              }))}
            />

            {/* Processing Time Footer */}
            <div
              style={{
                marginTop: "24px",
                padding: "12px 16px",
                background: "rgba(255,255,255,0.03)",
                borderRadius: "10px",
                fontSize: "12px",
                color: "rgba(245,245,245,0.55)",
                textAlign: "center",
                border: "1px solid rgba(255,255,255,0.06)",
              }}
            >
              ⏱ Analysis completed in {result.processing_time.toFixed(2)} seconds &nbsp;·&nbsp;
              Gemini 3.5 Flash-Lite model &nbsp;·&nbsp; {result.actual_analyzed.toLocaleString()} comments analyzed
            </div>
          </div>
        </ScrollReveal>
      )}
    </section>
  );
}