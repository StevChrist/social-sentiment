"use client";

import React, { useState } from "react";
import { startScrape, AnalyzeOut } from "@/lib/api";
import { toast } from "react-toastify";
import QuotaDisplay from "@/components/QuotaDisplay";
import StorageMonitor from "@/components/StorageMonitor";
import Image from "next/image";

// Perbaikan interface untuk response yang mengandung properti result opsional
interface StartScrapeResponse {
  job_id: string;
  eta_seconds_initial: number;
  message: string;
  result?: AnalyzeOut; // result sebagai properti opsional
}

// Opsi persentase kedalaman analisis
const PERCENTAGE_OPTIONS = [
  { value: 0.25, label: "25%", description: "Quick analysis" },
  { value: 0.5, label: "50%", description: "Balanced analysis" },
  { value: 0.75, label: "75%", description: "Comprehensive analysis" },
  { value: 1.0, label: "100%", description: "Full analysis" }
];

// Konsisten style header
const headerStyle: React.CSSProperties = {
  fontSize: "18px",
  color: "#F5F5F5",
  fontWeight: 700,
  marginBottom: "16px",
  marginTop: "0px",
  display: "flex",
  alignItems: "center",
  gap: "8px"
};

export default function TrySection(): React.ReactElement {
  const [url, setUrl] = useState("");
  const [percentage, setPercentage] = useState(0.5);
  const [result, setResult] = useState<AnalyzeOut | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const realPercentageAnalyzed = result ? result.actual_analyzed / result.total_comments : 0;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    setUrl(e.target.value);
  };

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (submitting) return;

    if (!url.trim()) {
      toast.error("Please enter a YouTube video URL or ID");
      return;
    }

    const estimatedUnits = 3;
    if (window.updateQuotaImmediately) {
      window.updateQuotaImmediately(estimatedUnits);
    }

    setResult(null);
    setSubmitting(true);

    try {
      toast.info(`Analysis started for ${percentage * 100}% of comments...`);

      // Cast response to type that includes result
      const response: StartScrapeResponse = await startScrape(url, percentage);

      if (response.result) {
        setResult(response.result);
        toast.success("Analysis completed successfully!");
      } else {
        throw new Error("No result returned from analysis");
      }

    } catch (err: unknown) {
      if (window.updateQuotaImmediately) {
        window.updateQuotaImmediately(-estimatedUnits);
      }

      let msg = err instanceof Error ? err.message : "Failed to start job.";

      if (msg.includes("exceeded the quota") || msg.includes("QuotaExceededError")) {
        msg = "Browser storage is full. Click here for instructions to clear storage.";
        toast.error(msg, {
          autoClose: 10000,
          onClick: () => {
            alert(`To fix storage quota issue:

1. Press F12 to open Developer Tools
2. Go to Application tab
3. Find Local Storage in sidebar
4. Select your domain (${window.location.origin})
5. Right-click and select "Clear"
6. Refresh the page and try again

Alternatively, try clearing your browser cache.`);
          }
        });
      } else {
        toast.error(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

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

      <h2 className="section-title" style={{ fontSize: "60px", margin: 0 }}>
        Try the Social Sentiment
      </h2>

      <p style={{ marginTop: "10px", fontSize: "18px", lineHeight: "1.6", color: "rgba(245,245,245,0.85)" }}>
        To start analyze, put your YouTube video link down below.
      </p>

      <form onSubmit={onSubmit} style={{ marginTop: "26px", width: "100%", maxWidth: "720px" }}>
        <div style={{
          position: "relative", width: "100%", height: "52px", borderRadius: "14px",
          background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.18)",
          boxShadow: "inset 0 1px 0 rgba(255,255,255,0.05), 0 10px 30px rgba(0,0,0,0.25)",
          backdropFilter: "blur(6px)", marginBottom: "20px"
        }}>
          <input
            type="url"
            required
            value={url}
            onChange={handleInputChange}
            placeholder="Paste your YouTube video URL here…"
            aria-label="YouTube Video URL"
            disabled={submitting}
            style={{
              position: "absolute", inset: 0, width: "100%", height: "100%", border: "none",
              outline: "none", background: "transparent", color: "#F5F5F5",
              paddingLeft: "26px", paddingRight: "16px", fontSize: "16px", opacity: submitting ? 0.7 : 1,
            }}
          />
        </div>

        <div style={{ marginBottom: "20px" }}>
          <p style={{ color: "rgba(245,245,245,0.85)", fontSize: "14px", marginBottom: "10px" }}>
            Select analysis depth:
          </p>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "10px" }}>
            {PERCENTAGE_OPTIONS.map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() => setPercentage(option.value)}
                disabled={submitting}
                style={{
                  padding: "10px 8px", borderRadius: "10px",
                  border: `2px solid ${percentage === option.value ? "#0474C4" : "rgba(255,255,255,0.2)"}`,
                  background: percentage === option.value ? "rgba(4,116,196,0.2)" : "rgba(255,255,255,0.05)",
                  color: percentage === option.value ? "#A8C4EC" : "rgba(245,245,245,0.8)",
                  fontSize: "14px", fontWeight: percentage === option.value ? 700 : 500,
                  cursor: submitting ? "not-allowed" : "pointer", transition: "all 0.2s ease",
                  opacity: submitting ? 0.5 : 1,
                }}
              >
                <div style={{ fontSize: "16px", marginBottom: "2px" }}>{option.label}</div>
                <div style={{ fontSize: "10px", opacity: 0.8 }}>{option.description}</div>
              </button>
            ))}
          </div>
          <p style={{ color: "rgba(245,245,245,0.6)", fontSize: "12px", marginTop: "8px" }}>
            {percentage * 100}% of total comments will be analyzed
          </p>
        </div>

        <div style={{ marginTop: "30px" }}>
          <button
            type="submit"
            className="btn-gradient"
            style={{
              display: "inline-flex", alignItems: "center", justifyContent: "center",
              height: "48px", padding: "0 26px", borderRadius: "12px", fontWeight: 700,
              color: "#F5F5F5", background: "linear-gradient(90deg, #0474C4 0%, #A8C4EC 100%)",
              boxShadow: "0 12px 30px rgba(0,0,0,0.25)",
              cursor: submitting ? "not-allowed" : "pointer", opacity: submitting ? 0.7 : 1,
              transition: "opacity 160ms ease", border: "none",
            }}
            disabled={submitting}
          >
            {submitting ? "Analyzing..." : `Start Analyze (${percentage * 100}%)`}
          </button>
        </div>

        <p style={{ marginTop: "20px", fontSize: "14px", color: "rgba(245,245,245,0.65)" }}>
          Example Link: https://www.youtube.com/watch?v=dQw4w9WgXcQ
        </p>

        <div style={{ maxWidth: "720px", width: "100%" }}>
          <QuotaDisplay />
        </div>
      </form>

      {/* ✅ RESULTS SECTION */}
      {result && (
        <div style={{
          marginTop: "24px",
          width: "100%",
          maxWidth: "1200px",
          background: "rgba(255,255,255,0.04)",
          border: "1px solid rgba(255,255,255,0.15)",
          borderRadius: "14px",
          padding: "20px",
          textAlign: "left",
        }}>
          {/* Header */}
          <div style={headerStyle}>
            📹 {result.video_title}
          </div>

          {/* Video Info */}
          <div style={{ marginBottom: "20px", color: "rgba(245,245,245,0.85)" }}>
            <div style={{ fontSize: "14px", marginBottom: "6px" }}>Channel: {result.channel_title}</div>
            <div style={{ fontSize: "14px" }}>
              Analyzed: {result.actual_analyzed} comments ({(realPercentageAnalyzed * 100).toFixed(1)}% of {result.total_comments} total)
            </div>
          </div>

          {/* Stats Grid */}
          <div style={{
            display: "grid",
            gridTemplateColumns: "1fr 1fr 1fr",
            gap: "10px",
            marginBottom: "30px",
          }}>
            <div style={{
              padding: "10px 12px", borderRadius: "10px", border: "1px solid rgba(16, 185, 129, 0.3)",
              background: "rgba(16, 185, 129, 0.1)", color: "#EAEAEA", fontSize: "14px", textAlign: "center",
            }}>
              <div style={{ opacity: 0.9 }}>Positive</div>
              <div style={{ fontWeight: 700, color: "#10B981" }}>{result.counts.positive} ({(result.ratios.positive * 100).toFixed(1)}%)</div>
            </div>
            <div style={{
              padding: "10px 12px", borderRadius: "10px", border: "1px solid rgba(245, 158, 11, 0.3)",
              background: "rgba(245, 158, 11, 0.1)", color: "#EAEAEA", fontSize: "14px", textAlign: "center",
            }}>
              <div style={{ opacity: 0.9 }}>Neutral</div>
              <div style={{ fontWeight: 700, color: "#F59E0B" }}>{result.counts.neutral} ({(result.ratios.neutral * 100).toFixed(1)}%)</div>
            </div>
            <div style={{
              padding: "10px 12px", borderRadius: "10px", border: "1px solid rgba(239, 68, 68, 0.3)",
              background: "rgba(239, 68, 68, 0.1)", color: "#EAEAEA", fontSize: "14px", textAlign: "center",
            }}>
              <div style={{ opacity: 0.9 }}>Negative</div>
              <div style={{ fontWeight: 700, color: "#EF4444" }}>{result.counts.negative} ({(result.ratios.negative * 100).toFixed(1)}%)</div>
            </div>
          </div>

          {/* Visualizations */}
          <div style={{ ...headerStyle, marginTop: "30px" }}>📊 Visualizations</div>
          <div style={{ display: "flex", gap: "24px", marginBottom: "30px" }}>
            {result.visualizations?.wordcloud_base64 && (
              <div style={{
                flex: 1, padding: "16px", borderRadius: "12px",
                background: "rgba(31, 41, 55, 0.7)", border: "1px solid rgba(255,255,255,0.1)",
              }}>
                <h4 style={{ color: "#F5F5F5", fontSize: "16px", marginBottom: "12px", fontWeight: 600 }}>🌟 Word Cloud</h4>
                <Image src={result.visualizations.wordcloud_base64} alt="Word Cloud" width={400} height={200} style={{ width: "100%", height: "auto", borderRadius: "8px", objectFit: "contain" }} />
              </div>
            )}
            {result.visualizations?.pie_chart_base64 && (
            <div style={{
              flex: 1,
              minWidth: "300px",
              padding: "16px",
              borderRadius: "12px",
              background: "rgba(31, 41, 55, 0.7)",
              border: "1px solid rgba(255,255,255,0.1)",

              // Flexbox untuk center
              display: "flex",
              flexDirection: "column",
              justifyContent: "center",
              alignItems: "center"
            }}>
              {/* Judul align left */}
              <p style={{
                fontSize: "16px",
                fontWeight: "600",
                marginBottom: "8px",
                color: "white",
                alignSelf: "flex-start"   // ini yang bikin text ke kiri
              }}>
                📊 Real Sentiment Distribution from YouTube Comments
              </p>

              {/* Gambar tetap center */}
              <Image
                src={result.visualizations.pie_chart_base64}
                alt="Pie Chart"
                width={300}
                height={150}
                style={{
                  maxWidth: "100%",
                  height: "auto",
                  borderRadius: "8px",
                  objectFit: "contain"
                }}
              />
            </div>
            )}
          </div>

          {/* Sample Comments */}
          <div style={{ ...headerStyle, marginTop: "30px" }}>💬 Sample Comments</div>
          <div style={{ display: "flex", gap: "16px" }}>
            {/* Positive Comments */}
            <div style={{
              flex: 1, padding: "16px", borderRadius: "12px", background: "rgba(16, 185, 129, 0.15)",
              border: "1px solid rgba(16, 185, 129, 0.3)", maxHeight: "200px", overflowY: "auto",
            }}>
              <h4 style={{ color: "#10B981", fontSize: "14px", marginBottom: "12px", fontWeight: 600, textAlign: "center" }}>Positive Comments</h4>
              <div>
                {result.examples.filter(c => c.prediction.label === 'positive').slice(0, 3).map((comment, index) => (
                  <div key={`pos-${index}`} style={{ marginBottom: "12px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "6px", borderLeft: "3px solid #10B981" }} >
                    <p style={{ color: "#F5F5F5", fontSize: "13px", lineHeight: "1.3", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 80)}{comment.text.length > 80 ? "..." : ""}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px", fontStyle: "italic" }}>— {comment.author}</small>
                  </div>
                ))}
              </div>
            </div>

            {/* Neutral Comments */}
            <div style={{
              flex: 1, padding: "16px", borderRadius: "12px", background: "rgba(245, 158, 11, 0.15)",
              border: "1px solid rgba(245, 158, 11, 0.3)", maxHeight: "200px", overflowY: "auto",
            }}>
              <h4 style={{ color: "#F59E0B", fontSize: "14px", marginBottom: "12px", fontWeight: 600, textAlign: "center" }}>Neutral Comments</h4>
              <div>
                {result.examples.filter(c => c.prediction.label === 'neutral').slice(0, 3).map((comment, index) => (
                  <div key={`neu-${index}`} style={{ marginBottom: "12px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "6px", borderLeft: "3px solid #F59E0B" }}>
                    <p style={{ color: "#F5F5F5", fontSize: "13px", lineHeight: "1.3", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 80)}{comment.text.length > 80 ? "..." : ""}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px", fontStyle: "italic" }}>— {comment.author}</small>
                  </div>
                ))}
              </div>
            </div>

            {/* Negative Comments */}
            <div style={{
              flex: 1, padding: "16px", borderRadius: "12px", background: "rgba(239, 68, 68, 0.15)",
              border: "1px solid rgba(239, 68, 68, 0.3)", maxHeight: "200px", overflowY: "auto",
            }}>
              <h4 style={{ color: "#EF4444", fontSize: "14px", marginBottom: "12px", fontWeight: 600, textAlign: "center" }}>Negative Comments</h4>
              <div>
                {result.examples.filter(c => c.prediction.label === 'negative').slice(0, 3).map((comment, index) => (
                  <div key={`neg-${index}`} style={{ marginBottom: "12px", padding: "8px", background: "rgba(255,255,255,0.05)", borderRadius: "6px", borderLeft: "3px solid #EF4444" }}>
                    <p style={{ color: "#F5F5F5", fontSize: "13px", lineHeight: "1.3", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 80)}{comment.text.length > 80 ? "..." : ""}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px", fontStyle: "italic" }}>— {comment.author}</small>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Processing time info */}
          {result.processing_time !== undefined && (
            <div style={{ marginTop: "20px", padding: "12px", background: "rgba(255,255,255,0.05)", borderRadius: "8px", fontSize: "12px", color: "rgba(245,245,245,0.7)", textAlign: "center" }}>
              Analysis completed in {result.processing_time.toFixed(2)} seconds
            </div>
          )}
        </div>
      )}
    </section>
  );
}