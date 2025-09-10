// src/utils/storage.ts - Safe Storage Utilities
export function isQuotaExceededError(err: unknown): boolean {
  return (
    err instanceof DOMException &&
    // Everything except Firefox
    (err.code === 22 ||
     // Firefox
     err.code === 1014 ||
     // Test name field too, because code might not be present
     // Everything except Firefox
     err.name === "QuotaExceededError" ||
     // Firefox
     err.name === "NS_ERROR_DOM_QUOTA_REACHED")
  );
}

export function safeSetItem(key: string, value: string): boolean {
  try {
    localStorage.setItem(key, value);
    return true;
  } catch (error) {
    if (isQuotaExceededError(error)) {
      console.warn('LocalStorage quota exceeded. Clearing old data...');
      
      // Clear old job data
      clearOldJobData();
      
      // Try again after cleanup
      try {
        localStorage.setItem(key, value);
        return true;
      } catch (retryError) {
        console.error('Failed to store data even after cleanup:', retryError);
        return false;
      }
    } else {
      console.error('Storage error:', error);
      throw error;
    }
  }
}

export function clearOldJobData(): void {
  const keys = Object.keys(localStorage);
  const jobKeys = keys.filter(key => key.startsWith('job_'));
  
  // Sort by timestamp and remove oldest entries, keep only 5 most recent
  jobKeys.sort().slice(0, Math.max(0, jobKeys.length - 5)).forEach(key => {
    localStorage.removeItem(key);
    console.log(`Removed old job data: ${key}`);
  });
}

export function safeGetItem(key: string): string | null {
  try {
    return localStorage.getItem(key);
  } catch (error) {
    console.error('Failed to get item from localStorage:', error);
    return null;
  }
}

export function getStorageInfo(): { used: number; available: number; percentage: number } {
  let used = 0;
  
  for (const key in localStorage) {
    if (localStorage.hasOwnProperty(key)) {
      used += localStorage[key].length + key.length;
    }
  }
  
  // Estimate available space (most browsers have ~5-10MB limit)
  const estimatedLimit = 5 * 1024 * 1024; // 5MB
  const available = Math.max(0, estimatedLimit - used);
  const percentage = Math.round((used / estimatedLimit) * 100);
  
  return { used, available, percentage };
}

export function clearAllJobData(): void {
  const keys = Object.keys(localStorage);
  keys.filter(key => key.startsWith('job_')).forEach(key => {
    localStorage.removeItem(key);
  });
  console.log('All job data cleared from localStorage');
}
