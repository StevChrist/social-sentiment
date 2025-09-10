// src/components/StorageMonitor.tsx - Storage Usage Monitor
"use client";

import React, { useEffect, useState } from 'react';
import { getStorageInfo, clearAllJobData } from '@/utils/storage';

export default function StorageMonitor(): React.ReactElement {
  const [storageInfo, setStorageInfo] = useState({ used: 0, available: 0, percentage: 0 });
  const [showMonitor, setShowMonitor] = useState(false);

  useEffect(() => {
    const updateStorageInfo = () => {
      const info = getStorageInfo();
      setStorageInfo(info);
      setShowMonitor(info.percentage >= 80); // Show when 80% full
    };

    updateStorageInfo();
    const interval = setInterval(updateStorageInfo, 10000); // Check every 10 seconds

    return () => clearInterval(interval);
  }, []);

  const handleClearStorage = () => {
    if (confirm('Clear all stored job data? This action cannot be undone.')) {
      clearAllJobData();
      setStorageInfo(getStorageInfo());
    }
  };

  if (!showMonitor) {
    return <></>; // Don't render if storage usage is low
  }

  return (
    <div style={{
      position: 'fixed',
      top: '20px',
      right: '20px',
      background: storageInfo.percentage >= 95 ? 'rgba(239, 68, 68, 0.9)' : 'rgba(245, 158, 11, 0.9)',
      color: 'white',
      padding: '12px 16px',
      borderRadius: '8px',
      fontSize: '14px',
      zIndex: 1000,
      boxShadow: '0 4px 12px rgba(0,0,0,0.3)'
    }}>
      <div style={{ marginBottom: '8px' }}>
        ⚠️ Storage: {storageInfo.percentage}% full ({Math.round(storageInfo.used / 1024)}KB used)
      </div>
      <button 
        onClick={handleClearStorage}
        style={{
          padding: '4px 8px',
          background: 'rgba(255,255,255,0.2)',
          border: 'none',
          borderRadius: '4px',
          color: 'white',
          cursor: 'pointer',
          fontSize: '12px'
        }}
      >
        Clear Job Data
      </button>
    </div>
  );
}
