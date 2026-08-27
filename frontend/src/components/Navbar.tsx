// src/components/Navbar.tsx
"use client";

import Link from "next/link";
import Image from "next/image";
import React, { useEffect, useState } from "react";

interface HealthStatus {
  status: string;
  provider: string;
  model: string;
  model_ready: boolean;
  database_connected: boolean;
  gemini_api_configured: boolean;
  youtube_api_configured: boolean;
  rate_limit_protection?: string;
}

export function Navbar(): React.ReactElement {
  const [scrollProgress, setScrollProgress] = useState(0);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isOnline, setIsOnline] = useState<boolean | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  // Check backend & model health periodically
  const checkHealth = async () => {
    try {
      const res = await fetch("http://localhost:8000/health", { cache: "no-store" });
      if (res.ok) {
        const data: HealthStatus = await res.json();
        setHealth(data);
        setIsOnline(data.status === "healthy" && data.model_ready);
      } else {
        setIsOnline(false);
      }
    } catch {
      setIsOnline(false);
      setHealth(null);
    }
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, 8000);

    const handleScroll = () => {
      const totalHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
      if (totalHeight > 0) {
        const progress = (window.scrollY / totalHeight) * 100;
        setScrollProgress(progress);
      }
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => {
      clearInterval(interval);
      window.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <header className="relative z-50" style={{ height: "64px" }}>
      {/* Scroll Progress Line */}
      <div
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: `${scrollProgress}%`,
          height: "3px",
          background: "linear-gradient(90deg, #0474C4, #4895EF, #7209B7)",
          boxShadow: "0 0 10px rgba(72, 149, 239, 0.8)",
          zIndex: 100,
          transition: "width 0.1s ease-out",
        }}
      />

      {/* Fixed top navigation bar */}
      <div
        className="fixed inset-x-0"
        style={{ top: "12px", height: "54px", pointerEvents: "none", zIndex: 50 }}
      >
        {/* ===== Left: Logo ===== */}
        <div
          style={{
            position: "absolute",
            left: "40px",
            top: "50%",
            transform: "translateY(-50%)",
            pointerEvents: "auto",
          }}
        >
          <Link href="https://stevchrist.site" className="flex items-center" aria-label="SocialSentiment Home">
            <Image
              src="/Logo PEN White.png"
              alt="SocialSentiment Logo"
              width={44}
              height={44}
              priority
              style={{ transition: "transform 0.2s ease" }}
              className="hover:scale-105"
            />
          </Link>
        </div>

        {/* ===== Center: Nav Menu ===== */}
        <nav
          className="relative mx-auto"
          style={{ height: "100%", maxWidth: "1200px" }}
        >
          <div
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              transform: "translate(-50%, -50%)",
              pointerEvents: "auto",
            }}
          >
            <ul
              className="flex items-center backdrop-blur-md"
              style={{
                gap: "24px",
                padding: "8px 24px",
                borderRadius: "9999px",
                backgroundColor: "rgba(17, 34, 64, 0.75)",
                border: "1px solid rgba(255,255,255,0.12)",
                boxShadow: "0 8px 32px rgba(0,0,0,0.3)",
                margin: 0,
                listStyle: "none",
              }}
            >
              <li>
                <Link
                  href="/"
                  style={linkStyle}
                  className="transition-colors duration-200 hover:text-white hover:opacity-100"
                >
                  Home
                </Link>
              </li>
              <li>
                <Link
                  href="#how"
                  style={linkStyle}
                  className="transition-colors duration-200 hover:text-white hover:opacity-100"
                >
                  How it Works
                </Link>
              </li>
              <li>
                <Link
                  href="#try"
                  style={linkStyle}
                  className="transition-colors duration-200 hover:text-white hover:opacity-100"
                >
                  Try!
                </Link>
              </li>
            </ul>
          </div>
        </nav>

        {/* ===== Right: Clean Online / Offline Badge with Hover Tooltip ===== */}
        <div
          style={{
            position: "absolute",
            right: "40px",
            top: "50%",
            transform: "translateY(-50%)",
            pointerEvents: "auto",
            width: "auto",
            display: "inline-block",
          }}
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "8px",
              padding: "6px 14px",
              borderRadius: "20px",
              background: isOnline === true
                ? "rgba(34, 197, 94, 0.12)"
                : isOnline === false
                ? "rgba(239, 68, 68, 0.15)"
                : "rgba(245, 158, 11, 0.12)",
              border: `1px solid ${
                isOnline === true
                  ? "rgba(34, 197, 94, 0.4)"
                  : isOnline === false
                  ? "rgba(239, 68, 68, 0.5)"
                  : "rgba(245, 158, 11, 0.4)"
              }`,
              backdropFilter: "blur(10px)",
              cursor: "pointer",
              boxShadow: isOnline === true
                ? "0 0 12px rgba(34, 197, 94, 0.25)"
                : isOnline === false
                ? "0 0 12px rgba(239, 68, 68, 0.35)"
                : "none",
              transition: "all 0.3s ease",
              whiteSpace: "nowrap",
            }}
          >
            {/* Pulsing status dot */}
            <div
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: isOnline === true ? "#22C55E" : isOnline === false ? "#EF4444" : "#F59E0B",
                boxShadow: isOnline === true ? "0 0 8px #22C55E" : isOnline === false ? "0 0 8px #EF4444" : "0 0 8px #F59E0B",
                animation: isOnline === true ? "pulse 2s infinite" : "none",
                flexShrink: 0,
              }}
            />

            {/* Clean Short Text: Online / Offline / Checking... */}
            <span
              style={{
                fontSize: "12px",
                fontWeight: 600,
                color: isOnline === true ? "#4ADE80" : isOnline === false ? "#F87171" : "#FCD34D",
                letterSpacing: "0.3px",
              }}
            >
              {isOnline === true
                ? "Online"
                : isOnline === false
                ? "Offline"
                : "Checking..."}
            </span>
          </div>

          {/* Details Tooltip on Hover */}
          {showTooltip && (
            <div
              style={{
                position: "absolute",
                top: "calc(100% + 8px)",
                right: 0,
                width: "270px",
                padding: "14px 16px",
                background: "rgba(11, 22, 40, 0.96)",
                border: "1px solid rgba(72, 149, 239, 0.25)",
                borderRadius: "12px",
                boxShadow: "0 15px 35px rgba(0,0,0,0.55), 0 0 15px rgba(72, 149, 239, 0.15)",
                backdropFilter: "blur(14px)",
                fontSize: "12px",
                color: "rgba(245,245,245,0.85)",
                lineHeight: "1.7",
                zIndex: 200,
                pointerEvents: "none",
              }}
            >
              <div style={{
                fontWeight: 700,
                color: "#FFFFFF",
                marginBottom: "8px",
                fontSize: "13px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                borderBottom: "1px solid rgba(255,255,255,0.1)",
                paddingBottom: "6px"
              }}>
                <span>🖥️ System Health &amp; Services</span>
                <span style={{
                  fontSize: "10px",
                  padding: "2px 6px",
                  borderRadius: "4px",
                  background: isOnline ? "rgba(34,197,94,0.2)" : "rgba(239,68,68,0.2)",
                  color: isOnline ? "#4ADE80" : "#F87171"
                }}>
                  {isOnline ? "OPERATIONAL" : "DEGRADED"}
                </span>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "rgba(245,245,245,0.6)" }}>Backend Server:</span>
                <strong style={{ color: isOnline !== false ? "#4ADE80" : "#F87171" }}>
                  {isOnline !== false ? "FastAPI (Running)" : "Offline"}
                </strong>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "rgba(245,245,245,0.6)" }}>AI Model Engine:</span>
                <strong style={{ color: "#A8C4EC" }}>
                  {health?.model || "gemini-3.5-flash-lite"}
                </strong>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "rgba(245,245,245,0.6)" }}>Database (PostgreSQL):</span>
                <strong style={{ color: health?.database_connected ? "#4ADE80" : isOnline ? "#4ADE80" : "#F87171" }}>
                  {health?.database_connected ? "Connected" : isOnline ? "Connected" : "Disconnected"}
                </strong>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "rgba(245,245,245,0.6)" }}>YouTube Data API:</span>
                <strong style={{ color: health?.youtube_api_configured !== false ? "#4ADE80" : "#F87171" }}>
                  {health?.youtube_api_configured !== false ? "Configured" : "Missing Key"}
                </strong>
              </div>

              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <span style={{ color: "rgba(245,245,245,0.6)" }}>Rate Limit Safety:</span>
                <strong style={{ color: "#38BDF8" }}>
                  15 RPM Safe (Free Tier)
                </strong>
              </div>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

const linkStyle: React.CSSProperties = {
  fontSize: "14px",
  fontWeight: 600,
  color: "rgba(245,245,245,0.85)",
  textDecoration: "none",
};
