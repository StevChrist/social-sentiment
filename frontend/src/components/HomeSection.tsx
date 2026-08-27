// src/components/HomeSection.tsx
"use client";

import React from 'react';

export default function HomeSection(): React.ReactElement {
  return (
    <section
      style={{
        minHeight: "calc(100vh - 74px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        boxSizing: "border-box",
        position: "relative",
        padding: "0 20px"
      }}
    >
      <div style={{ maxWidth: "800px", margin: "0 auto", animation: "fadeInUp 0.8s ease-out forwards" }}>
        {/* Floating Badge */}
        <div style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "8px",
          padding: "6px 16px",
          borderRadius: "30px",
          background: "rgba(72, 149, 239, 0.12)",
          border: "1px solid rgba(72, 149, 239, 0.3)",
          color: "#A8C4EC",
          fontSize: "13px",
          fontWeight: 500,
          marginBottom: "20px",
          boxShadow: "0 0 20px rgba(72, 149, 239, 0.15)",
          backdropFilter: "blur(8px)"
        }}>
          <span style={{ fontSize: "14px" }}>✨</span>
          <span>Powered by Gemini 3.5 Flash-Lite &amp; YouTube Data API</span>
        </div>

        {/* Hero Title */}
        <h1
          style={{
            fontSize: "clamp(36px, 6vw, 64px)",
            fontWeight: 700,
            color: "#F5F5F5",
            margin: "0 0 16px 0",
            lineHeight: 1.15,
            letterSpacing: "-0.5px"
          }}
        >
          <span style={{ color: "rgba(245,245,245,0.75)" }}>Welcome To</span>{" "}
          <span style={{
            background: "linear-gradient(135deg, #FFFFFF 0%, #A8C4EC 60%, #4895EF 100%)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
          }}>
            SocialSentiment
          </span>
        </h1>

        {/* Subtitle */}
        <p
          style={{
            fontSize: "clamp(16px, 2.5vw, 20px)",
            color: "rgba(245,245,245,0.8)",
            maxWidth: "600px",
            margin: "0 auto 32px auto",
            lineHeight: 1.5
          }}
        >
          AI-powered YouTube comment sentiment analysis engine with real-time multilingual insights and interactive visual analytics.
        </p>

        {/* Call to Action Button */}
        <div>
          <a
            href="#try"
            className="btn-gradient"
            style={{
              textDecoration: "none",
              fontSize: "16px",
              display: "inline-flex",
              alignItems: "center",
              gap: "8px"
            }}
          >
            <span>Let&apos;s Analyze</span>
            <span style={{ transition: "transform 0.2s ease" }}>🚀</span>
          </a>
        </div>
      </div>
    </section>
  );
}
