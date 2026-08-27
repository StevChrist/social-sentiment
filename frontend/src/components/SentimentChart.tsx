// src/components/SentimentChart.tsx
"use client";

import React, { useState } from 'react';
import Image from 'next/image';

interface Comment {
  id: string;
  author: string;
  text: string;
  sentiment: 'positive' | 'neutral' | 'negative';
}

interface SentimentData {
  counts: { positive: number; negative: number; neutral: number };
  ratios: { positive: number; negative: number; neutral: number };
}

interface SentimentChartProps {
  data: SentimentData;
  wordCloudImage?: string;
  pieChartImage?: string;
  examples: Comment[];
}

export default function SentimentChart({
  data,
  wordCloudImage,
  examples,
}: SentimentChartProps): React.ReactElement {
  const [hovered, setHovered] = useState<'positive' | 'neutral' | 'negative' | null>(null);

  const groupedComments = {
    positive: examples.filter((c) => c.sentiment === 'positive').slice(0, 5),
    neutral: examples.filter((c) => c.sentiment === 'neutral').slice(0, 5),
    negative: examples.filter((c) => c.sentiment === 'negative').slice(0, 5),
  };

  const total = (data.counts.positive || 0) + (data.counts.neutral || 0) + (data.counts.negative || 0);

  const posRatio = total > 0 ? (data.counts.positive / total) : 0;
  const neuRatio = total > 0 ? (data.counts.neutral / total) : 0;
  const negRatio = total > 0 ? (data.counts.negative / total) : 0;

  const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

  // SVG Donut Path calculations
  const size = 260;
  const center = size / 2;
  const radius = 95;
  const strokeWidth = 38;
  const circumference = 2 * Math.PI * radius;

  // Offsets for strokeDasharray
  const posStroke = posRatio * circumference;
  const neuStroke = neuRatio * circumference;
  const negStroke = negRatio * circumference;

  const posOffset = 0;
  const neuOffset = -posStroke;
  const negOffset = -(posStroke + neuStroke);

  const sentiments = [
    { key: 'positive' as const, label: 'Positive', count: data.counts.positive, ratio: posRatio, color: '#22C55E', icon: '😊' },
    { key: 'neutral' as const, label: 'Neutral', count: data.counts.neutral, ratio: neuRatio, color: '#F59E0B', icon: '😐' },
    { key: 'negative' as const, label: 'Negative', count: data.counts.negative, ratio: negRatio, color: '#EF4444', icon: '😡' },
  ];

  const activeItem = hovered ? sentiments.find(s => s.key === hovered) : null;

  return (
    <div style={{ marginTop: "24px" }}>
      <h3 style={{ color: "#F5F5F5", fontSize: "20px", marginBottom: "18px", fontWeight: 600 }}>
        📊 Visualizations &amp; Sentiment Insights
      </h3>

      {/* Upper: Equal-sized Word Cloud & Interactive Pie Chart */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))",
        gap: "24px",
        maxWidth: "960px",
        margin: "0 auto 28px auto",
      }}>
        {/* Left: Word Cloud Card */}
        <div style={{
          height: "400px",
          padding: "20px",
          borderRadius: "16px",
          background: "rgba(31, 41, 55, 0.85)",
          border: "1px solid rgba(255,255,255,0.12)",
          backdropFilter: "blur(12px)",
          color: "#F5F5F5",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.25)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <h4 style={{ color: "#F5F5F5", fontSize: "16px", fontWeight: 600, margin: 0 }}>
              🌟 Word Cloud
            </h4>
            <span style={{ fontSize: "12px", color: "rgba(245,245,245,0.5)" }}>Most Frequent Words</span>
          </div>

          <div style={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            overflow: "hidden",
            borderRadius: "10px",
            background: "rgba(0,0,0,0.25)",
            padding: "8px"
          }}>
            {wordCloudImage ? (
              <Image
                src={wordCloudImage}
                alt="Word Cloud - Most common words"
                width={420}
                height={280}
                style={{
                  width: "100%",
                  height: "100%",
                  maxHeight: "300px",
                  objectFit: "contain",
                  borderRadius: "8px",
                  transition: "transform 0.3s ease"
                }}
                priority={false}
              />
            ) : (
              <div style={{ color: "rgba(245,245,245,0.4)", fontSize: "13px" }}>No Word Cloud generated</div>
            )}
          </div>
        </div>

        {/* Right: Interactive Donut / Pie Chart Card */}
        <div style={{
          height: "400px",
          padding: "20px",
          borderRadius: "16px",
          background: "rgba(31, 41, 55, 0.85)",
          border: "1px solid rgba(255,255,255,0.12)",
          backdropFilter: "blur(12px)",
          color: "#F5F5F5",
          display: "flex",
          flexDirection: "column",
          boxShadow: "0 8px 32px rgba(0, 0, 0, 0.25)"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
            <h4 style={{ color: "#F5F5F5", fontSize: "16px", fontWeight: 600, margin: 0 }}>
              🥧 Sentiment Distribution
            </h4>
            <span style={{ fontSize: "12px", color: "#4895EF" }}>Interactive Hover</span>
          </div>

          <div style={{
            flex: 1,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            position: "relative"
          }}>
            {/* SVG Interactive Donut */}
            <div style={{ position: "relative", width: `${size}px`, height: `${size}px` }}>
              <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: "rotate(-90deg)" }}>
                {/* Background Ring */}
                <circle
                  cx={center}
                  cy={center}
                  r={radius}
                  fill="transparent"
                  stroke="rgba(255,255,255,0.06)"
                  strokeWidth={strokeWidth}
                />

                {/* Positive Slice */}
                {posStroke > 0 && (
                  <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="transparent"
                    stroke="#22C55E"
                    strokeWidth={hovered === 'positive' ? strokeWidth + 6 : strokeWidth}
                    strokeDasharray={`${posStroke} ${circumference}`}
                    strokeDashoffset={posOffset}
                    style={{
                      cursor: "pointer",
                      transition: "all 0.25s ease",
                      filter: hovered === 'positive' ? "drop-shadow(0 0 8px rgba(34, 197, 94, 0.8))" : "none",
                      opacity: hovered && hovered !== 'positive' ? 0.45 : 1
                    }}
                    onMouseEnter={() => setHovered('positive')}
                    onMouseLeave={() => setHovered(null)}
                  />
                )}

                {/* Neutral Slice */}
                {neuStroke > 0 && (
                  <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="transparent"
                    stroke="#F59E0B"
                    strokeWidth={hovered === 'neutral' ? strokeWidth + 6 : strokeWidth}
                    strokeDasharray={`${neuStroke} ${circumference}`}
                    strokeDashoffset={neuOffset}
                    style={{
                      cursor: "pointer",
                      transition: "all 0.25s ease",
                      filter: hovered === 'neutral' ? "drop-shadow(0 0 8px rgba(245, 158, 11, 0.8))" : "none",
                      opacity: hovered && hovered !== 'neutral' ? 0.45 : 1
                    }}
                    onMouseEnter={() => setHovered('neutral')}
                    onMouseLeave={() => setHovered(null)}
                  />
                )}

                {/* Negative Slice */}
                {negStroke > 0 && (
                  <circle
                    cx={center}
                    cy={center}
                    r={radius}
                    fill="transparent"
                    stroke="#EF4444"
                    strokeWidth={hovered === 'negative' ? strokeWidth + 6 : strokeWidth}
                    strokeDasharray={`${negStroke} ${circumference}`}
                    strokeDashoffset={negOffset}
                    style={{
                      cursor: "pointer",
                      transition: "all 0.25s ease",
                      filter: hovered === 'negative' ? "drop-shadow(0 0 8px rgba(239, 68, 68, 0.8))" : "none",
                      opacity: hovered && hovered !== 'negative' ? 0.45 : 1
                    }}
                    onMouseEnter={() => setHovered('negative')}
                    onMouseLeave={() => setHovered(null)}
                  />
                )}
              </svg>

              {/* Center Details on Hover */}
              <div style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                pointerEvents: "none",
                textAlign: "center"
              }}>
                {activeItem ? (
                  <>
                    <span style={{ fontSize: "20px" }}>{activeItem.icon}</span>
                    <span style={{ fontSize: "14px", fontWeight: 700, color: activeItem.color, marginTop: "2px" }}>
                      {activeItem.label}
                    </span>
                    <span style={{ fontSize: "16px", fontWeight: 800, color: "#FFFFFF" }}>
                      {pct(activeItem.ratio)}
                    </span>
                    <span style={{ fontSize: "11px", color: "rgba(245,245,245,0.7)" }}>
                      {activeItem.count.toLocaleString()} comments
                    </span>
                  </>
                ) : (
                  <>
                    <span style={{ fontSize: "12px", color: "rgba(245,245,245,0.6)", textTransform: "uppercase", letterSpacing: "1px" }}>
                      Total Analyzed
                    </span>
                    <span style={{ fontSize: "20px", fontWeight: 800, color: "#FFFFFF", marginTop: "2px" }}>
                      {total.toLocaleString()}
                    </span>
                    <span style={{ fontSize: "11px", color: "#4895EF" }}>
                      Hover for details
                    </span>
                  </>
                )}
              </div>
            </div>

            {/* Interactive Legend Badges */}
            <div style={{
              display: "flex",
              justifyContent: "center",
              gap: "10px",
              marginTop: "10px",
              width: "100%"
            }}>
              {sentiments.map((s) => (
                <div
                  key={s.key}
                  onMouseEnter={() => setHovered(s.key)}
                  onMouseLeave={() => setHovered(null)}
                  style={{
                    padding: "4px 10px",
                    borderRadius: "20px",
                    background: hovered === s.key ? `${s.color}33` : "rgba(255,255,255,0.05)",
                    border: `1px solid ${hovered === s.key ? s.color : "rgba(255,255,255,0.1)"}`,
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                    fontSize: "11px"
                  }}
                >
                  <div style={{ width: "8px", height: "8px", borderRadius: "50%", background: s.color }} />
                  <span style={{ color: "#F5F5F5", fontWeight: 500 }}>{s.label}</span>
                  <span style={{ color: s.color, fontWeight: 700 }}>{pct(s.ratio)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Lower: Sample Comments */}
      <div style={{ marginTop: "28px" }}>
        <h3 style={{ color: "#F5F5F5", fontSize: "17px", marginBottom: "16px", fontWeight: 600 }}>
          💬 Sample Categorized Comments
        </h3>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: "20px", maxWidth: "960px", margin: "0 auto" }}>
          {/* Positive */}
          <div style={{
            padding: "16px", borderRadius: "14px",
            background: "rgba(16, 185, 129, 0.12)", border: "1px solid rgba(16, 185, 129, 0.3)",
            maxHeight: "220px", overflowY: "auto"
          }}>
            <h4 style={{
              color: "#10B981", fontSize: "14px", marginBottom: "12px", fontWeight: 600,
              background: "rgba(16, 185, 129, 0.2)", padding: "6px 12px", borderRadius: "20px", textAlign: "center"
            }}>
              😊 Positive Comments ({data.counts.positive.toLocaleString()})
            </h4>
            <div style={{ paddingRight: "4px" }}>
              {groupedComments.positive.length > 0 ? (
                groupedComments.positive.map((comment, index) => (
                  <div key={`pos-${index}`} style={{
                    marginBottom: "10px", padding: "8px 10px",
                    background: "rgba(255,255,255,0.05)", borderRadius: "8px", borderLeft: "3px solid #10B981"
                  }}>
                    <p style={{ color: "#F5F5F5", fontSize: "12px", lineHeight: "1.4", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 100)}{comment.text.length > 100 ? '...' : ''}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px" }}>
                      — {comment.author}
                    </small>
                  </div>
                ))
              ) : (
                <p style={{ color: "rgba(245,245,245,0.5)", fontSize: "12px", fontStyle: "italic", textAlign: "center" }}>
                  No positive comments found
                </p>
              )}
            </div>
          </div>

          {/* Neutral */}
          <div style={{
            padding: "16px", borderRadius: "14px",
            background: "rgba(245, 158, 11, 0.12)", border: "1px solid rgba(245, 158, 11, 0.3)",
            maxHeight: "220px", overflowY: "auto"
          }}>
            <h4 style={{
              color: "#F59E0B", fontSize: "14px", marginBottom: "12px", fontWeight: 600,
              background: "rgba(245, 158, 11, 0.2)", padding: "6px 12px", borderRadius: "20px", textAlign: "center"
            }}>
              😐 Neutral Comments ({data.counts.neutral.toLocaleString()})
            </h4>
            <div style={{ paddingRight: "4px" }}>
              {groupedComments.neutral.length > 0 ? (
                groupedComments.neutral.map((comment, index) => (
                  <div key={`neu-${index}`} style={{
                    marginBottom: "10px", padding: "8px 10px",
                    background: "rgba(255,255,255,0.05)", borderRadius: "8px", borderLeft: "3px solid #F59E0B"
                  }}>
                    <p style={{ color: "#F5F5F5", fontSize: "12px", lineHeight: "1.4", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 100)}{comment.text.length > 100 ? '...' : ''}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px" }}>
                      — {comment.author}
                    </small>
                  </div>
                ))
              ) : (
                <p style={{ color: "rgba(245,245,245,0.5)", fontSize: "12px", fontStyle: "italic", textAlign: "center" }}>
                  No neutral comments found
                </p>
              )}
            </div>
          </div>

          {/* Negative */}
          <div style={{
            padding: "16px", borderRadius: "14px",
            background: "rgba(239, 68, 68, 0.12)", border: "1px solid rgba(239, 68, 68, 0.3)",
            maxHeight: "220px", overflowY: "auto"
          }}>
            <h4 style={{
              color: "#EF4444", fontSize: "14px", marginBottom: "12px", fontWeight: 600,
              background: "rgba(239, 68, 68, 0.2)", padding: "6px 12px", borderRadius: "20px", textAlign: "center"
            }}>
              😡 Negative Comments ({data.counts.negative.toLocaleString()})
            </h4>
            <div style={{ paddingRight: "4px" }}>
              {groupedComments.negative.length > 0 ? (
                groupedComments.negative.map((comment, index) => (
                  <div key={`neg-${index}`} style={{
                    marginBottom: "10px", padding: "8px 10px",
                    background: "rgba(255,255,255,0.05)", borderRadius: "8px", borderLeft: "3px solid #EF4444"
                  }}>
                    <p style={{ color: "#F5F5F5", fontSize: "12px", lineHeight: "1.4", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 100)}{comment.text.length > 100 ? '...' : ''}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px" }}>
                      — {comment.author}
                    </small>
                  </div>
                ))
              ) : (
                <p style={{ color: "rgba(245,245,245,0.5)", fontSize: "12px", fontStyle: "italic", textAlign: "center" }}>
                  No negative comments found
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
