"use client";

import React, { useEffect, useState, useRef, useCallback } from 'react';

interface QuotaData {
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
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
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

  const getUsagePercentage = () => {
    if (!quota) return 0;
    return Math.round((quota.estimated_used / quota.daily_limit) * 100);
  };

  const getUsageColor = () => {
    const percentage = getUsagePercentage();
    if (percentage >= 90) return '#EF4444';
    if (percentage >= 70) return '#F59E0B';
    if (percentage >= 50) return '#10B981';
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
          fontWeight: 600 
        }}>
          🔥 API Credits
        </span>
        <span style={{ 
          color: "rgba(245,245,245,0.5)", 
          fontSize: "10px"
        }}>
          Live
        </span>
      </div>

      {/* Usage Bar */}
      <div style={{ marginBottom: "10px" }}>
        <div 
          style={{
            width: "100%",
            height: "6px",
            background: "rgba(255,255,255,0.1)",
            borderRadius: "3px",
            overflow: "hidden"
          }}
        >
          <div
            style={{
              width: `${getUsagePercentage()}%`,
              height: "100%",
              background: `linear-gradient(90deg, ${getUsageColor()}, ${getUsageColor()}AA)`,
              borderRadius: "3px",
              transition: "width 0.5s ease"
            }}
          />
        </div>
        <div style={{ 
          display: "flex", 
          justifyContent: "space-between", 
          marginTop: "4px",
          fontSize: "11px",
          color: "rgba(245,245,245,0.7)"
        }}>
          <span>Used: {quota.estimated_used.toLocaleString()}</span>
          <span>{getUsagePercentage()}%</span>
          <span>Limit: {quota.daily_limit.toLocaleString()}</span>
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
            ~{Math.floor(quota.comments_remaining / 1000)}K
          </div>
          <div style={{ opacity: 0.8 }}>Comments</div>
        </div>
      </div>

      {/* Reset Info */}
      <div style={{
        marginTop: "8px",
        fontSize: "11px",
        color: "rgba(245,245,245,0.5)",
        textAlign: "center"
      }}>
        Resets at midnight PT • ~{quota.videos_remaining} videos left
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