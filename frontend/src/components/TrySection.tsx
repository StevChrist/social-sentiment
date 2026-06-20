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
import Image from "next/image";

// ── Analysis depth options ────────────────────────────────────────────────────
const PERCENTAGE_OPTIONS = [
  { value: 0.25, label: "25%", description: "Quick • Up to 250 comments" },
  { value: 0.5, label: "50%", description: "Balanced • Up to 500 comments" },
  { value: 0.75, label: "75%", description: "Deep • Up to 750 comments" },
  { value: 1.0, label: "100%", description: "Full • Capped at 1k comments" },
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

// ── Shared styles ─────────────────────────────────────────────────────────────
const cardStyle: React.CSSProperties = {
  padding: "16px",
  borderRadius: "12px",
  background: "rgba(31, 41, 55, 0.7)",
  border: "1px solid rgba(255,255,255,0.1)",
  backdropFilter: "blur(4px)",
};

const headerStyle: React.CSSProperties = {
  fontSize: "17px",
  color: "#F5F5F5",
  fontWeight: 700,
  marginBottom: "14px",
  marginTop: "0px",
  display: "flex",
  alignItems: "center",
  gap: "8px",
};

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
        padding: "14px 16px",
        borderRadius: "12px",
        border: `1px solid ${accent}44`,
        background: `${accent}18`,
        textAlign: "center",
      }}
    >
      <div style={{ fontSize: "22px", marginBottom: "4px" }}>{icon}</div>
      <div style={{ color: "#EAEAEA", fontSize: "13px", opacity: 0.85 }}>{label}</div>
      <div style={{ fontWeight: 800, fontSize: "20px", color: accent, marginTop: "4px" }}>
        {count.toLocaleString()}
      </div>
      <div style={{ color: accent, fontSize: "13px", opacity: 0.8 }}>
        {(ratio * 100).toFixed(1)}%
      </div>
    </div>
  );
}

// ── Comment card ─────────────────────────────────────────────────────────────
interface CommentCardProps {
  text: string;
  author: string;
  accent: string;
}
function CommentCard({ text, author, accent }: CommentCardProps) {
  return (
    <div
      style={{
        marginBottom: "10px",
        padding: "9px 10px",
        background: "rgba(255,255,255,0.05)",
        borderRadius: "8px",
        borderLeft: `3px solid ${accent}`,
      }}
    >
      <p
        style={{
          color: "#F5F5F5",
          fontSize: "13px",
          lineHeight: "1.4",
          margin: "0 0 4px 0",
          wordBreak: "break-word",
        }}
      >
        &ldquo;{text.slice(0, 100)}{text.length > 100 ? "…" : ""}&rdquo;
      </p>
      <small style={{ color: "rgba(245,245,245,0.55)", fontSize: "11px", fontStyle: "italic" }}>
        — {author}
      </small>
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
  // Estimate remaining time
  let estRemainingStr = "Estimating...";
  if (elapsed > 0) {
    if (progress >= 10) {
      const estimatedTotal = (elapsed / progress) * 100;
      const remaining = Math.max(1, Math.round(estimatedTotal - elapsed));
      estRemainingStr = `~${remaining}s`;
    } else {
      // Prior-knowledge based estimate for early stages
      const baseEst = percentage === 0.25 ? 10 : percentage === 0.5 ? 20 : percentage === 0.75 ? 30 : 45;
      const remaining = Math.max(1, baseEst - elapsed);
      estRemainingStr = `~${remaining}s`;
    }
  }

  return (
    <div
      style={{
        marginTop: "28px",
        width: "100%",
        maxWidth: "620px",
        background: "rgba(255,255,255,0.04)",
        border: "1px solid rgba(255,255,255,0.12)",
        borderRadius: "16px",
        padding: "24px 28px",
      }}
    >
      {/* Steps */}
      <div style={{ display: "flex", flexDirection: "column", gap: "14px", marginBottom: "20px" }}>
        {ANALYSIS_STEPS.map((step, idx) => {
          const isDone = idx < activeStep;
          const isActive = idx === activeStep;
          return (
            <div
              key={step.key}
              style={{ display: "flex", alignItems: "center", gap: "12px", opacity: isDone || isActive ? 1 : 0.35 }}
            >
              {/* Circle indicator */}
              <div
                style={{
                  width: "32px",
                  height: "32px",
                  borderRadius: "50%",
                  background: isDone
                    ? "#10B981"
                    : isActive
                    ? "rgba(4,116,196,0.3)"
                    : "rgba(255,255,255,0.08)",
                  border: isActive ? "2px solid #0474C4" : isDone ? "2px solid #10B981" : "2px solid rgba(255,255,255,0.15)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: "14px",
                  flexShrink: 0,
                  transition: "all 0.3s ease",
                  animation: isActive ? "pulse 1.5s ease-in-out infinite" : "none",
                }}
              >
                {isDone ? "✓" : step.icon}
              </div>
              {/* Label */}
              <div>
                <div
                  style={{
                    fontSize: "14px",
                    fontWeight: isActive ? 700 : 500,
                    color: isDone ? "#10B981" : isActive ? "#A8C4EC" : "rgba(245,245,245,0.6)",
                    transition: "color 0.3s",
                  }}
                >
                  {step.label}
                </div>
                {isActive && (
                  <div style={{ fontSize: "12px", color: "rgba(245,245,245,0.5)", marginTop: "2px" }}>
                    {stepLabel}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div
        style={{
          height: "8px",
          background: "rgba(255,255,255,0.1)",
          borderRadius: "4px",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${progress}%`,
            background: "linear-gradient(90deg, #0474C4, #A8C4EC)",
            borderRadius: "4px",
            transition: "width 0.5s ease",
          }}
        />
      </div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          marginTop: "6px",
          fontSize: "12px",
          color: "rgba(245,245,245,0.5)",
        }}
      >
        <span>{stepLabel}</span>
        <span>{progress}%</span>
      </div>

      {/* Time Estimates */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "12px",
          paddingTop: "12px",
          borderTop: "1px solid rgba(255,255,255,0.08)",
          fontSize: "13px",
          color: "rgba(245,245,245,0.7)",
        }}
      >
        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          ⏱️ Elapsed: <strong>{elapsed}s</strong>
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          ⏳ Est. Remaining: <strong style={{ color: "#A8C4EC" }}>{estRemainingStr}</strong>
        </span>
      </div>
    </div>
  );
}

// ── Main Component ────────────────────────────────────────────────────────────
export default function TrySection(): React.ReactElement {
  const [url, setUrl] = useState("");
  const [percentage, setPercentage] = useState(0.5);
  const [result, setResult] = useState<AnalyzeOut | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [stepLabel, setStepLabel] = useState("");
  const [activeStep, setActiveStep] = useState(0);

  // Time tracking states
  const [startTime, setStartTime] = useState<number | null>(null);
  const [elapsed, setElapsed] = useState(0);

  const cleanupRef = useRef<(() => void) | null>(null);

  const videoId = result ? extractVideoId(url) : "";
  const realPercentageAnalyzed = result
    ? result.actual_analyzed / Math.max(result.total_comments, 1)
    : 0;

  // Effect to tick the elapsed time every second while analyzing
  React.useEffect(() => {
    let timer: NodeJS.Timeout;
    if (submitting && startTime !== null) {
      timer = setInterval(() => {
        setElapsed(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);
    } else {
      setElapsed(0);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [submitting, startTime]);

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (submitting) return;

    if (!url.trim()) {
      toast.error("Please enter a YouTube video URL or ID");
      return;
    }

    setResult(null);
    setSubmitting(true);
    setProgress(0);
    setStepLabel("Checking quota...");
    setActiveStep(0);

    // Pre-submit check: verify if API quota is already depleted
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const quotaRes = await fetch(`${API_URL}/api/quota`);
      if (quotaRes.ok) {
        const quotaData = await quotaRes.json();
        if (quotaData.credits_remaining <= 0) {
          toast.error("Daily API quota limit exceeded. Please try again tomorrow.");
          setSubmitting(false);
          setProgress(0);
          return;
        }
      }
    } catch (e) {
      console.warn("Quota pre-check failed:", e);
    }

    setStepLabel("Starting analysis…");
    setStartTime(Date.now());
    setElapsed(0);

    toast.info(`Starting ${percentage * 100}% analysis…`, { autoClose: 3000 });

    cleanupRef.current = streamAnalysis(
      url,
      percentage,
      // onProgress
      (evt: ProgressEvent) => {
        setProgress(evt.progress);
        setStepLabel(evt.step);
        setActiveStep(getStepFromProgress(evt.progress));
      },
      // onResult
      (data: AnalyzeOut) => {
        setResult(data);
        setSubmitting(false);
        setProgress(100);
        setActiveStep(ANALYSIS_STEPS.length - 1);
        toast.success("Analysis completed!");
      },
      // onError
      (errMsg: string) => {
        toast.error(errMsg);
        setSubmitting(false);
        setProgress(0);
      }
    );
  };

  const handleCancel = () => {
    if (cleanupRef.current) cleanupRef.current();
    setSubmitting(false);
    setProgress(0);
    toast.info("Analysis cancelled.");
  };

  const handleDownload = () => {
    if (!result) return;
    downloadCSV(result.video_id, percentage);
    toast.success("Downloading CSV report…");
  };

  const topKeywords = result?.visualizations?.top_keywords?.slice(0, 12) ?? [];

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

      <h2 className="section-title" style={{ fontSize: "56px", margin: 0 }}>
        Try the Social Sentiment
      </h2>

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

      {/* ── Form ── */}
      <form onSubmit={onSubmit} style={{ marginTop: "28px", width: "100%", maxWidth: "720px" }}>
        {/* URL input */}
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

        {/* Depth selector */}
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
                  padding: "10px 8px",
                  borderRadius: "10px",
                  border: `2px solid ${percentage === opt.value ? "#0474C4" : "rgba(255,255,255,0.18)"}`,
                  background:
                    percentage === opt.value
                      ? "rgba(4,116,196,0.22)"
                      : "rgba(255,255,255,0.04)",
                  color:
                    percentage === opt.value ? "#A8C4EC" : "rgba(245,245,245,0.75)",
                  fontSize: "14px",
                  fontWeight: percentage === opt.value ? 700 : 500,
                  cursor: submitting ? "not-allowed" : "pointer",
                  transition: "all 0.2s ease",
                  opacity: submitting ? 0.5 : 1,
                }}
              >
                <div style={{ fontSize: "17px", marginBottom: "2px" }}>{opt.label}</div>
                <div style={{ fontSize: "10px", opacity: 0.7 }}>{opt.description}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Submit / Cancel */}
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
              transition: "opacity 160ms ease",
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

        <div style={{ maxWidth: "720px", width: "100%" }}>
          <QuotaDisplay />
        </div>
      </form>

      {/* ── Loading indicator ── */}
      {submitting && (
        <LoadingIndicator progress={progress} stepLabel={stepLabel} activeStep={activeStep} elapsed={elapsed} percentage={percentage} />
      )}

      {/* ── Results ── */}
      {result && !submitting && (
        <div
          style={{
            marginTop: "32px",
            width: "100%",
            maxWidth: "1200px",
            background: "rgba(255,255,255,0.03)",
            border: "1px solid rgba(255,255,255,0.12)",
            borderRadius: "18px",
            padding: "28px",
            textAlign: "left",
          }}
        >
          {/* ── Header + Download ── */}
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              flexWrap: "wrap",
              gap: "12px",
              marginBottom: "8px",
            }}
          >
            <div>
              <div style={headerStyle}>📹 {result.video_title}</div>
              <div style={{ fontSize: "13px", color: "rgba(245,245,245,0.7)", marginBottom: "4px" }}>
                📺 {result.channel_title}
              </div>
              <div style={{ fontSize: "13px", color: "rgba(245,245,245,0.6)" }}>
                Analyzed&nbsp;
                <strong style={{ color: "#A8C4EC" }}>
                  {result.actual_analyzed.toLocaleString()}
                </strong>
                &nbsp;comments&nbsp;(
                {(realPercentageAnalyzed * 100).toFixed(1)}% of{" "}
                {result.total_comments.toLocaleString()} total)
              </div>

              {/* Model Performance Badge */}
              <div style={{ 
                marginTop: "12px", 
                padding: "8px 12px", 
                background: "rgba(255,255,255,0.03)", 
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "8px",
                display: "inline-flex",
                alignItems: "center",
                gap: "12px",
                fontSize: "12px", 
                color: "rgba(245,245,245,0.7)",
                flexWrap: "wrap"
              }}>
                <span style={{ fontWeight: 600, color: "#A8C4EC", display: "flex", alignItems: "center", gap: "4px" }}>
                  🤖 Model Performance:
                </span>
                <span>Accuracy: <strong style={{ color: "#10B981" }}>83.3%</strong> (Validation)</span>
                <span style={{ opacity: 0.3 }}>|</span>
                <span>Macro F1: <strong style={{ color: "#10B981" }}>82.3%</strong></span>
                <span style={{ opacity: 0.3 }}>|</span>
                <span>Test Accuracy: <strong style={{ color: "#F59E0B" }}>71.9%</strong></span>
              </div>
            </div>

            <button
              onClick={handleDownload}
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "7px",
                padding: "10px 18px",
                borderRadius: "10px",
                background: "rgba(4,116,196,0.18)",
                border: "1px solid rgba(4,116,196,0.45)",
                color: "#A8C4EC",
                fontWeight: 600,
                fontSize: "14px",
                cursor: "pointer",
                transition: "background 0.2s",
                whiteSpace: "nowrap",
              }}
            >
              ⬇ Download CSV
            </button>
          </div>

          {/* ── Stat cards ── */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "12px",
              marginTop: "20px",
              marginBottom: "28px",
            }}
          >
            <StatCard
              label="Positive"
              count={result.counts.positive}
              ratio={result.ratios.positive}
              accent="#10B981"
              icon="😊"
            />
            <StatCard
              label="Neutral"
              count={result.counts.neutral}
              ratio={result.ratios.neutral}
              accent="#F59E0B"
              icon="😐"
            />
            <StatCard
              label="Negative"
              count={result.counts.negative}
              ratio={result.ratios.negative}
              accent="#EF4444"
              icon="😞"
            />
          </div>

          {/* ── Visualizations row ── */}
          <div style={{ ...headerStyle, marginTop: "0" }}>📊 Visualizations</div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr",
              gap: "16px",
              marginBottom: "20px",
            }}
          >
            {/* Word Cloud */}
            {result.visualizations?.wordcloud_base64 && (
              <div style={cardStyle}>
                <h4
                  style={{ color: "#F5F5F5", fontSize: "15px", marginBottom: "10px", fontWeight: 600 }}
                >
                  🌟 Word Cloud
                </h4>
                <Image
                  src={result.visualizations.wordcloud_base64}
                  alt="Word Cloud"
                  width={500}
                  height={240}
                  style={{ width: "100%", height: "auto", borderRadius: "8px", objectFit: "contain" }}
                />
              </div>
            )}

            {/* Pie Chart */}
            {result.visualizations?.pie_chart_base64 && (
              <div style={cardStyle}>
                <h4
                  style={{ color: "#F5F5F5", fontSize: "15px", marginBottom: "10px", fontWeight: 600 }}
                >
                  🥧 Sentiment Distribution
                </h4>
                <Image
                  src={result.visualizations.pie_chart_base64}
                  alt="Sentiment Pie Chart"
                  width={500}
                  height={240}
                  style={{ width: "100%", height: "auto", borderRadius: "8px", objectFit: "contain" }}
                />
              </div>
            )}

            {/* Bar Chart */}
            {result.visualizations?.bar_chart_base64 && (
              <div style={cardStyle}>
                <h4
                  style={{ color: "#F5F5F5", fontSize: "15px", marginBottom: "10px", fontWeight: 600 }}
                >
                  📊 Comment Counts
                </h4>
                <Image
                  src={result.visualizations.bar_chart_base64}
                  alt="Sentiment Bar Chart"
                  width={500}
                  height={240}
                  style={{ width: "100%", height: "auto", borderRadius: "8px", objectFit: "contain" }}
                />
              </div>
            )}

            {/* Top Keywords */}
            {topKeywords.length > 0 && (
              <div style={cardStyle}>
                <h4
                  style={{ color: "#F5F5F5", fontSize: "15px", marginBottom: "12px", fontWeight: 600 }}
                >
                  🏷️ Top Keywords
                </h4>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "8px" }}>
                  {topKeywords.map((kw, i) => {
                    const maxFreq = topKeywords[0]?.frequency ?? 1;
                    const intensity = 0.4 + 0.6 * (kw.frequency / maxFreq);
                    return (
                      <span
                        key={kw.word}
                        style={{
                          padding: "4px 10px",
                          borderRadius: "20px",
                          background: `rgba(4,116,196,${intensity * 0.3})`,
                          border: `1px solid rgba(4,116,196,${intensity * 0.5})`,
                          color: `rgba(168,196,236,${0.6 + 0.4 * intensity})`,
                          fontSize: `${11 + Math.round(intensity * 4)}px`,
                          fontWeight: i < 3 ? 700 : 500,
                          whiteSpace: "nowrap",
                        }}
                        title={`${kw.frequency} mentions`}
                      >
                        {kw.word}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* ── Sample Comments ── */}
          <div style={{ ...headerStyle, marginTop: "8px" }}>💬 Sample Comments</div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "14px" }}>
            {/* Positive */}
            <div
              style={{
                ...cardStyle,
                background: "rgba(16,185,129,0.12)",
                border: "1px solid rgba(16,185,129,0.28)",
                maxHeight: "240px",
                overflowY: "auto",
              }}
            >
              <h4
                style={{
                  color: "#10B981",
                  fontSize: "13px",
                  marginBottom: "10px",
                  fontWeight: 700,
                  textAlign: "center",
                }}
              >
                😊 Positive
              </h4>
              {result.examples
                .filter((c) => c.prediction.label === "positive")
                .slice(0, 4)
                .map((c, i) => (
                  <CommentCard key={`pos-${i}`} text={c.text} author={c.author} accent="#10B981" />
                ))}
              {result.examples.filter((c) => c.prediction.label === "positive").length === 0 && (
                <p style={{ color: "rgba(245,245,245,0.4)", fontSize: "13px", fontStyle: "italic" }}>
                  No positive comments in sample
                </p>
              )}
            </div>

            {/* Neutral */}
            <div
              style={{
                ...cardStyle,
                background: "rgba(245,158,11,0.12)",
                border: "1px solid rgba(245,158,11,0.28)",
                maxHeight: "240px",
                overflowY: "auto",
              }}
            >
              <h4
                style={{
                  color: "#F59E0B",
                  fontSize: "13px",
                  marginBottom: "10px",
                  fontWeight: 700,
                  textAlign: "center",
                }}
              >
                😐 Neutral
              </h4>
              {result.examples
                .filter((c) => c.prediction.label === "neutral")
                .slice(0, 4)
                .map((c, i) => (
                  <CommentCard key={`neu-${i}`} text={c.text} author={c.author} accent="#F59E0B" />
                ))}
              {result.examples.filter((c) => c.prediction.label === "neutral").length === 0 && (
                <p style={{ color: "rgba(245,245,245,0.4)", fontSize: "13px", fontStyle: "italic" }}>
                  No neutral comments in sample
                </p>
              )}
            </div>

            {/* Negative */}
            <div
              style={{
                ...cardStyle,
                background: "rgba(239,68,68,0.12)",
                border: "1px solid rgba(239,68,68,0.28)",
                maxHeight: "240px",
                overflowY: "auto",
              }}
            >
              <h4
                style={{
                  color: "#EF4444",
                  fontSize: "13px",
                  marginBottom: "10px",
                  fontWeight: 700,
                  textAlign: "center",
                }}
              >
                😞 Negative
              </h4>
              {result.examples
                .filter((c) => c.prediction.label === "negative")
                .slice(0, 4)
                .map((c, i) => (
                  <CommentCard key={`neg-${i}`} text={c.text} author={c.author} accent="#EF4444" />
                ))}
              {result.examples.filter((c) => c.prediction.label === "negative").length === 0 && (
                <p style={{ color: "rgba(245,245,245,0.4)", fontSize: "13px", fontStyle: "italic" }}>
                  No negative comments in sample
                </p>
              )}
            </div>
          </div>

          {/* ── Footer ── */}
          <div
            style={{
              marginTop: "20px",
              padding: "10px 16px",
              background: "rgba(255,255,255,0.04)",
              borderRadius: "8px",
              fontSize: "12px",
              color: "rgba(245,245,245,0.5)",
              textAlign: "center",
            }}
          >
            ⏱ Analysis completed in {result.processing_time.toFixed(2)} seconds &nbsp;·&nbsp;
            XLM-RoBERTa model &nbsp;·&nbsp; {result.actual_analyzed.toLocaleString()} comments processed
          </div>
        </div>
      )}
    </section>
  );
}