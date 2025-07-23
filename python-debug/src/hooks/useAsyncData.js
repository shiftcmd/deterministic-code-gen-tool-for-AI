import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for loading async data with consistent error handling and loading states
 * Provides refetch capability and automatic cleanup
 * 
 * @param {Function} apiCall - Async function to call for data
 * @param {Array} dependencies - Dependencies that should trigger refetch
 * @param {Object} options - Configuration options
 * @param {boolean} options.immediate - Whether to fetch data immediately (default: true)
 * @param {Function} options.onSuccess - Callback for successful data load
 * @param {Function} options.onError - Callback for error handling
 * @returns {Object} { data, loading, error, refetch, reset }
 */
export const useAsyncData = (
  apiCall, 
  dependencies = [], 
  options = {}
) => {
  const {
    immediate = true,
    onSuccess,
    onError
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const [hasLoaded, setHasLoaded] = useState(false);
  
  const mountedRef = useRef(true);
  const abortControllerRef = useRef(null);

  // Memoize the API call to prevent unnecessary re-renders
  const memoizedApiCall = useCallback(apiCall, [apiCall, ...dependencies]);

  const fetchData = useCallback(async (showLoading = true) => {
    if (!mountedRef.current) return;
    
    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    
    try {
      if (showLoading) {
        setLoading(true);
      }
      setError(null);

      const result = await memoizedApiCall();
      
      if (mountedRef.current && !abortControllerRef.current.signal.aborted) {
        setData(result);
        setHasLoaded(true);
        
        // Call success callback if provided
        if (onSuccess) {
          onSuccess(result);
        }
      }
    } catch (err) {
      if (mountedRef.current && !abortControllerRef.current.signal.aborted) {
        const errorMessage = err.message || 'Failed to load data';
        setError(errorMessage);
        
        // Call error callback if provided
        if (onError) {
          onError(err);
        }
      }
    } finally {
      if (mountedRef.current && !abortControllerRef.current.signal.aborted) {
        setLoading(false);
      }
    }
  }, [memoizedApiCall, onSuccess, onError]);

  const refetch = useCallback((showLoading = true) => {
    return fetchData(showLoading);
  }, [fetchData]);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
    setHasLoaded(false);
    
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  }, []);

  // Fetch data when dependencies change
  useEffect(() => {
    if (immediate || hasLoaded) {
      fetchData();
    }
  }, [fetchData, immediate, hasLoaded]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    hasLoaded,
    refetch,
    reset
  };
};
