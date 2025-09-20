// src/components/SentimentChart.tsx
"use client";

import React from 'react';
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
  pieChartImage,
  examples,
}: SentimentChartProps): React.ReactElement {
  const groupedComments = {
    positive: examples.filter((c) => c.sentiment === 'positive').slice(0, 5),
    neutral: examples.filter((c) => c.sentiment === 'neutral').slice(0, 5),
    negative: examples.filter((c) => c.sentiment === 'negative').slice(0, 5),
  };

  const pct = (v: number) => `${(v * 100).toFixed(1)}%`;

  return (
    <div style={{ marginTop: "20px" }}>
      <h3 style={{ color: "#F5F5F5", fontSize: "18px", marginBottom: "16px" }}>
        📊 Visualizations
      </h3>

      {/* Upper: Word Cloud & Pie */}
      <div style={{
        display: "flex",
        gap: "24px",
        maxWidth: "800px",
        margin: "0 auto",
        marginBottom: "24px"
      }}>
        {/* Left: Word Cloud */}
        {wordCloudImage && (
          <div style={{
            flex: 1,
            padding: "16px",
            borderRadius: "12px",
            background: "rgba(31, 41, 55, 0.9)",
            border: "1px solid rgba(255,255,255,0.1)",
            color: "#F5F5F5"
          }}>
            <h4 style={{ color: "#F5F5F5", fontSize: "16px", marginBottom: "12px", fontWeight: 600 }}>
              🌟 Word Cloud
            </h4>
            <Image
              src={wordCloudImage}
              alt="Word Cloud - Most common words"
              width={360}
              height={300}
              style={{ width: "100%", height: "300px", objectFit: "contain", borderRadius: "8px" }}
              priority={false}
            />
          </div>
        )}

        {/* Right: Pie Chart */}
        {pieChartImage && (
          <div style={{
            flex: 1,
            padding: "16px",
            borderRadius: "12px",
            background: "rgba(31, 41, 55, 0.9)",
            border: "1px solid rgba(255,255,255,0.1)",
            color: "#F5F5F5"
          }}>
            <h4 style={{ color: "#F5F5F5", fontSize: "16px", marginBottom: "12px", fontWeight: 600 }}>
              🥧 Sentiment Distribution
            </h4>
            <Image
              src={pieChartImage}
              alt="Pie Chart - Sentiment distribution"
              width={360}
              height={300}
              style={{ width: "100%", height: "300px", objectFit: "contain", borderRadius: "8px" }}
              priority={false}
            />
            {/* gunakan 'data' agar tidak unused + memberi info */}
            <p style={{ marginTop: "8px", fontSize: "12px", color: "rgba(245,245,245,0.75)", textAlign: "center" }}>
              Positive {pct(data.ratios.positive)} • Neutral {pct(data.ratios.neutral)} • Negative {pct(data.ratios.negative)}
            </p>
          </div>
        )}
      </div>

      {/* Lower: Sample Comments */}
      <div style={{ marginTop: "24px" }}>
        <h3 style={{ color: "#F5F5F5", fontSize: "16px", marginBottom: "16px" }}>
          💬 Sample Comments
        </h3>

        <div style={{ display: "flex", gap: "24px", maxWidth: "800px", margin: "0 auto" }}>
          {/* Positive */}
          <div style={{
            flex: 1, padding: "16px", borderRadius: "12px",
            background: "rgba(16, 185, 129, 0.15)", border: "1px solid rgba(16, 185, 129, 0.3)",
            maxHeight: "200px", overflowY: "auto"
          }}>
            <h4 style={{
              color: "#10B981", fontSize: "14px", marginBottom: "12px", fontWeight: 600,
              background: "rgba(16, 185, 129, 0.2)", padding: "8px 12px", borderRadius: "20px", textAlign: "center"
            }}>
              Positive Comments
            </h4>
            <div style={{ paddingRight: "8px" }}>
              {groupedComments.positive.length > 0 ? (
                groupedComments.positive.map((comment, index) => (
                  <div key={`pos-${index}`} style={{
                    marginBottom: "12px", padding: "8px",
                    background: "rgba(255,255,255,0.05)", borderRadius: "6px", borderLeft: "3px solid #10B981"
                  }}>
                    <p style={{ color: "#F5F5F5", fontSize: "13px", lineHeight: "1.3", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 80)}{comment.text.length > 80 ? '...' : ''}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px", fontStyle: "italic" }}>
                      — {comment.author}
                    </small>
                  </div>
                ))
              ) : (
                <p style={{ color: "rgba(245,245,245,0.6)", fontSize: "13px", fontStyle: "italic" }}>
                  No positive comments found
                </p>
              )}
            </div>
          </div>

          {/* Neutral */}
          <div style={{
            flex: 1, padding: "16px", borderRadius: "12px",
            background: "rgba(245, 158, 11, 0.15)", border: "1px solid rgba(245, 158, 11, 0.3)",
            maxHeight: "200px", overflowY: "auto"
          }}>
            <h4 style={{
              color: "#F59E0B", fontSize: "14px", marginBottom: "12px", fontWeight: 600,
              background: "rgba(245, 158, 11, 0.2)", padding: "8px 12px", borderRadius: "20px", textAlign: "center"
            }}>
              Neutral
            </h4>
            <div style={{ paddingRight: "8px" }}>
              {groupedComments.neutral.length > 0 ? (
                groupedComments.neutral.map((comment, index) => (
                  <div key={`neu-${index}`} style={{
                    marginBottom: "12px", padding: "8px",
                    background: "rgba(255,255,255,0.05)", borderRadius: "6px", borderLeft: "3px solid #F59E0B"
                  }}>
                    <p style={{ color: "#F5F5F5", fontSize: "13px", lineHeight: "1.3", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 80)}{comment.text.length > 80 ? '...' : ''}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px", fontStyle: "italic" }}>
                      — {comment.author}
                    </small>
                  </div>
                ))
              ) : (
                <p style={{ color: "rgba(245,245,245,0.6)", fontSize: "13px", fontStyle: "italic" }}>
                  No neutral comments found
                </p>
              )}
            </div>
          </div>

          {/* Negative */}
          <div style={{
            flex: 1, padding: "16px", borderRadius: "12px",
            background: "rgba(239, 68, 68, 0.15)", border: "1px solid rgba(239, 68, 68, 0.3)",
            maxHeight: "200px", overflowY: "auto"
          }}>
            <h4 style={{
              color: "#EF4444", fontSize: "14px", marginBottom: "12px", fontWeight: 600,
              background: "rgba(239, 68, 68, 0.2)", padding: "8px 12px", borderRadius: "20px", textAlign: "center"
            }}>
              Negative
            </h4>
            <div style={{ paddingRight: "8px" }}>
              {groupedComments.negative.length > 0 ? (
                groupedComments.negative.map((comment, index) => (
                  <div key={`neg-${index}`} style={{
                    marginBottom: "12px", padding: "8px",
                    background: "rgba(255,255,255,0.05)", borderRadius: "6px", borderLeft: "3px solid #EF4444"
                  }}>
                    <p style={{ color: "#F5F5F5", fontSize: "13px", lineHeight: "1.3", margin: "0 0 4px 0" }}>
                      &ldquo;{comment.text.slice(0, 80)}{comment.text.length > 80 ? '...' : ''}&rdquo;
                    </p>
                    <small style={{ color: "rgba(245,245,245,0.6)", fontSize: "11px", fontStyle: "italic" }}>
                      — {comment.author}
                    </small>
                  </div>
                ))
              ) : (
                <p style={{ color: "rgba(245,245,245,0.6)", fontSize: "13px", fontStyle: "italic" }}>
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
