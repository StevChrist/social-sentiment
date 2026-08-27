"use client";

import React, { useEffect, useState, useRef, useCallback } from 'react';

interface QuotaData {
  period?: string;
  monthly_limit?: number;
  daily_limit: number;
  estimated_used: number;
  estimated_remaining: number;
  reset_time: string;
  credits_remaining: number;
  comments_remaining: number;
  videos_remaining: number;
  last_updated: string;
}

declare global {
  interface Window {
    updateQuotaImmediately?: (units: number) => void;
  }
}

// ✅ Fix: Use React.ReactElement instead of JSX.Element
export default function QuotaDisplay(): React.ReactElement {
  const [quota, setQuota] = useState<QuotaData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchQuota = async () => {
    try {
      setError(null);
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001';
      const response = await fetch(`${API_URL}/api/quota`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch quota: ${response.status}`);
      }
      
      const data: QuotaData = await response.json();
      setQuota(data);
      setLoading(false);
      
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load quota';
      setError(errorMessage);
      setLoading(false);
    }
  };

  // ✅ Fix: Use useCallback with proper dependencies
  const immediateQuotaReduce = useCallback((unitsUsed: number) => {
    setQuota(prev => {
      if (!prev) return null;
      return {
        ...prev,
        estimated_used: prev.estimated_used + unitsUsed,
        estimated_remaining: Math.max(0, prev.estimated_remaining - unitsUsed),
        credits_remaining: Math.max(0, prev.credits_remaining - unitsUsed),
        comments_remaining: Math.max(0, prev.comments_remaining - (unitsUsed * 100)),
        videos_remaining: Math.max(0, prev.videos_remaining - Math.ceil(unitsUsed / 2))
      };
    });
  }, []); // Remove quota dependency to fix the warning

  // Real-time polling every 5 seconds
  useEffect(() => {
    fetchQuota();
    intervalRef.current = setInterval(fetchQuota, 5000);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // ✅ Fix: Include immediateQuotaReduce in dependency array
  useEffect(() => {
    window.updateQuotaImmediately = immediateQuotaReduce;
    
    return () => {
      delete window.updateQuotaImmediately;
    };
  }, [immediateQuotaReduce]);

  const getEffectiveLimit = () => {
    if (!quota) return 3000;
    return quota.monthly_limit || quota.daily_limit || 3000;
  };

  const getUsagePercentage = () => {
    if (!quota) return 0;
    const pct = (quota.estimated_used / getEffectiveLimit()) * 100;
    return Math.min(100, Math.round(pct * 10) / 10);
  };

  const getBarDisplayWidth = () => {
    const pct = getUsagePercentage();
    if (pct === 0) return 0;
    return Math.max(3, pct);
  };

  const getUsageColor = () => {
    const percentage = getUsagePercentage();
    if (percentage >= 90) return '#EF4444';
    if (percentage >= 70) return '#F59E0B';
    if (percentage >= 40) return '#4895EF';
    return '#22C55E';
  };

  if (loading) {
    return (
      <div style={{ 
        color: "rgba(245,245,245,0.6)", 
        fontSize: "12px", 
        marginTop: "8px",
        display: "flex",
        alignItems: "center",
        gap: "8px"
      }}>
        <div 
          style={{
            width: "12px",
            height: "12px",
            border: "2px solid rgba(245,245,245,0.3)",
            borderTop: "2px solid rgba(245,245,245,0.8)",
            borderRadius: "50%",
            animation: "spin 1s linear infinite"
          }}
        />
        Loading quota...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ 
        color: "rgba(239, 68, 68, 0.8)", 
        fontSize: "12px", 
        marginTop: "8px",
        display: "flex",
        alignItems: "center",
        gap: "4px"
      }}>
        <span>⚠️</span>
        <span>{error}</span>
        <button
          onClick={fetchQuota}
          style={{
            marginLeft: "8px",
            background: "none",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "rgba(239, 68, 68, 0.8)",
            fontSize: "10px",
            padding: "2px 6px",
            borderRadius: "4px",
            cursor: "pointer"
          }}
        >
          Retry
        </button>
      </div>
    );
  }

  if (!quota) return <div></div>;

  return (
    <div 
      style={{
        marginTop: "12px",
        padding: "12px 16px",
        borderRadius: "12px",
        background: "rgba(255,255,255,0.05)",
        border: "1px solid rgba(255,255,255,0.1)",
        backdropFilter: "blur(10px)",
        position: "relative"
      }}
    >
      {/* Live indicator */}
      <div 
        style={{
          position: "absolute",
          top: "8px",
          right: "8px",
          width: "8px",
          height: "8px",
          background: "#22C55E",
          borderRadius: "50%",
          animation: "pulse 2s infinite"
        }}
        title="Live updates every 5 seconds"
      />

      {/* Header */}
      <div style={{ 
        display: "flex", 
        alignItems: "center", 
        justifyContent: "space-between",
        marginBottom: "8px"
      }}>
        <span style={{ 
          color: "rgba(245,245,245,0.9)", 
          fontSize: "13px", 
          fontWeight: 600,
          display: "flex",
          alignItems: "center",
          gap: "6px"
        }}>
          <span>🔥</span>
          <span>Monthly Free Tier Credits</span>
        </span>
        <span style={{ 
          color: "rgba(72, 149, 239, 0.9)", 
          fontSize: "11px",
          fontWeight: 600
        }}>
          {quota.estimated_used} / {getEffectiveLimit()} units
        </span>
      </div>

      {/* Usage Bar */}
      <div style={{ marginBottom: "10px" }}>
        <div 
          style={{
            width: "100%",
            height: "8px",
            background: "rgba(255,255,255,0.08)",
            borderRadius: "4px",
            overflow: "hidden",
            boxShadow: "inset 0 1px 3px rgba(0,0,0,0.3)"
          }}
        >
          <div
            style={{
              width: `${getBarDisplayWidth()}%`,
              height: "100%",
              background: `linear-gradient(90deg, ${getUsageColor()}, #4895EF)`,
              borderRadius: "4px",
              boxShadow: `0 0 10px ${getUsageColor()}88`,
              transition: "width 0.6s cubic-bezier(0.34, 1.56, 0.64, 1)"
            }}
          />
        </div>
        <div style={{ 
            display: "flex", 
            justifyContent: "space-between", 
            marginTop: "6px",
            fontSize: "11px",
            color: "rgba(245,245,245,0.7)"
          }}>
          <span>Used: <strong style={{ color: "#F5F5F5" }}>{quota.estimated_used.toLocaleString()}</strong> units ({getUsagePercentage()}%)</span>
          <span>Limit: <strong style={{ color: "#F5F5F5" }}>{getEffectiveLimit().toLocaleString()}</strong>/mo</span>
        </div>
      </div>

      {/* Credits Display */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "1fr 1fr",
        gap: "8px",
        fontSize: "12px"
      }}>
        <div style={{ 
          color: "rgba(245,245,245,0.8)",
          textAlign: "center",
          padding: "6px",
          background: "rgba(255,255,255,0.03)",
          borderRadius: "8px"
        }}>
          <div style={{ color: getUsageColor(), fontWeight: 700, fontSize: "14px" }}>
            {quota.credits_remaining.toLocaleString()}
          </div>
          <div style={{ opacity: 0.8 }}>Credits Left</div>
        </div>
        
        <div style={{ 
          color: "rgba(245,245,245,0.8)",
          textAlign: "center",
          padding: "6px",
          background: "rgba(255,255,255,0.03)",
          borderRadius: "8px"
        }}>
          <div style={{ color: "#4895EF", fontWeight: 700, fontSize: "14px" }}>
            {quota.comments_remaining >= 1000
              ? `~${(quota.comments_remaining / 1000).toFixed(1).replace(/\.0$/, '')}K`
              : `~${quota.comments_remaining}`}
          </div>
          <div style={{ opacity: 0.8 }}>Comments Left</div>
        </div>
      </div>

      {/* Reset Info */}
      <div style={{
        marginTop: "8px",
        fontSize: "11px",
        color: "rgba(245,245,245,0.5)",
        textAlign: "center"
      }}>
        Resets on {quota.reset_time} • 100% Free Tier Protected
      </div>
    </div>
  );
}

// Add CSS animations
if (typeof document !== 'undefined') {
  const style = document.createElement('style');
  style.textContent = `
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    @keyframes spin {
      0% { transform: rotate(0deg); }
      100% { transform: rotate(360deg); }
    }
  `;
  document.head.appendChild(style);
}