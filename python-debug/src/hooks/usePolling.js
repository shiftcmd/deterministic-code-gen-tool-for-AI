import { useState, useEffect, useRef, useCallback } from 'react';

/**
 * Custom hook for polling data at regular intervals
 * Provides automatic cleanup and error handling
 * 
 * @param {Function} apiCall - Async function to call for data
 * @param {number} interval - Polling interval in milliseconds (default: 5000)
 * @param {Array} dependencies - Dependencies that should restart polling
 * @param {boolean} enabled - Whether polling should be active (default: true)
 * @returns {Object} { data, loading, error, start, stop, restart }
 */
export const usePolling = (apiCall, interval = 5000, dependencies = [], enabled = true) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(false);
  
  const intervalRef = useRef(null);
  const mountedRef = useRef(true);

  // Memoize the API call to prevent unnecessary re-renders
  const memoizedApiCall = useCallback(apiCall, [apiCall, ...dependencies]);

  const poll = useCallback(async () => {
    if (!mountedRef.current) return;
    
    try {
      setError(null);
      const result = await memoizedApiCall();
      
      if (mountedRef.current) {
        setData(result);
        setLoading(false);
      }
    } catch (err) {
      if (mountedRef.current) {
        setError(err.message || 'Polling failed');
        setLoading(false);
      }
    }
  }, [memoizedApiCall]);

  const start = useCallback(() => {
    if (!enabled || isPolling) return;
    
    setIsPolling(true);
    setLoading(true);
    
    // Initial poll
    poll();
    
    // Set up interval
    intervalRef.current = setInterval(poll, interval);
  }, [enabled, isPolling, poll, interval]);

  const stop = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const restart = useCallback(() => {
    stop();
    setTimeout(start, 100); // Brief delay to ensure cleanup
  }, [stop, start]);

  // Start/stop polling based on enabled state
  useEffect(() => {
    if (enabled) {
      start();
    } else {
      stop();
    }

    return stop;
  }, [enabled, start, stop]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    isPolling,
    start,
    stop,
    restart
  };
};
