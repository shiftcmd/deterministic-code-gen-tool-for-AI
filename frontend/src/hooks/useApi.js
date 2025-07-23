import { useState, useEffect, useCallback } from 'react';
import api from '../services/api.js';
import { parseErrorMessage } from '../utils/helpers.js';

// Custom hook for API calls with loading, error, and data state
export const useApi = (apiCall, dependencies = [], options = {}) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const {
    immediate = true,
    onSuccess,
    onError,
    retry = 0,
    retryDelay = 1000
  } = options;

  const execute = useCallback(async (...args) => {
    setLoading(true);
    setError(null);
    
    let attempts = 0;
    const maxAttempts = retry + 1;
    
    while (attempts < maxAttempts) {
      try {
        const result = await apiCall(...args);
        setData(result);
        setLoading(false);
        
        if (onSuccess) {
          onSuccess(result);
        }
        
        return result;
      } catch (err) {
        attempts++;
        
        if (attempts >= maxAttempts) {
          const errorMessage = parseErrorMessage(err);
          setError(errorMessage);
          setLoading(false);
          
          if (onError) {
            onError(errorMessage);
          }
          
          throw err;
        } else {
          // Wait before retrying
          await new Promise(resolve => setTimeout(resolve, retryDelay));
        }
      }
    }
  }, [apiCall, retry, retryDelay, onSuccess, onError]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, dependencies);

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return {
    data,
    loading,
    error,
    execute,
    reset
  };
};

// Hook for polling API endpoints
export const usePolling = (apiCall, interval = 5000, dependencies = [], enabled = true) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!enabled) return;

    const poll = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await apiCall();
        setData(result);
      } catch (err) {
        setError(parseErrorMessage(err));
      } finally {
        setLoading(false);
      }
    };

    // Initial call
    poll();

    // Set up polling
    const intervalId = setInterval(poll, interval);

    return () => clearInterval(intervalId);
  }, [...dependencies, enabled, interval]);

  return { data, loading, error };
};

// Hook for async data fetching with state management
export const useAsyncData = (
  apiCall, 
  dependencies = [], 
  options = {}
) => {
  const [data, setData] = useState(options.initialData || null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await apiCall(...args);
      setData(result);
      
      return result;
    } catch (err) {
      const errorMessage = parseErrorMessage(err);
      setError(errorMessage);
      throw err;
    } finally {
      setLoading(false);
    }
  }, [apiCall]);

  useEffect(() => {
    fetchData();
  }, dependencies);

  const refetch = useCallback(() => {
    return fetchData();
  }, [fetchData]);

  const reset = useCallback(() => {
    setData(options.initialData || null);
    setError(null);
    setLoading(false);
  }, [options.initialData]);

  return {
    data,
    loading,
    error,
    refetch,
    reset
  };
};

// Hook for managing processing status polling
export const useProcessingStatus = (runId, options = {}) => {
  const { interval = 2000, enabled = true } = options;
  
  const apiCall = useCallback(() => {
    if (!runId) return Promise.resolve(null);
    return api.getProcessingStatus(runId);
  }, [runId]);

  const { data: status, loading, error } = usePolling(
    apiCall, 
    interval, 
    [runId], 
    enabled && !!runId
  );

  const isComplete = status?.status === 'completed' || status?.status === 'failed';
  const isRunning = status?.status === 'running' || status?.status === 'processing';

  return {
    status,
    loading,
    error,
    isComplete,
    isRunning,
    progress: status?.progress || 0
  };
};

// Hook for file system browsing
export const useFileSystem = (initialPath = '/') => {
  const [currentPath, setCurrentPath] = useState(initialPath);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const browsePath = useCallback(async (path) => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await api.browseFileSystem(path);
      // Handle new mock API response structure
      setFiles(result.files || []);
      setCurrentPath(result.currentPath || path);
      
      return result;
    } catch (err) {
      setError(parseErrorMessage(err));
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // Only browse path if it's a valid path
    if (currentPath) {
      browsePath(currentPath).catch(err => {
        console.warn('Failed to load initial path:', err.message);
        // Set some default files if the API call fails
        setFiles([
          { name: 'example.py', type: 'file', path: '/example.py', size: 1024 },
          { name: 'src', type: 'directory', path: '/src', size: 0 }
        ]);
      });
    }
  }, []);

  const navigateUp = useCallback(() => {
    const parentPath = currentPath.split('/').slice(0, -1).join('/') || '/';
    return browsePath(parentPath);
  }, [currentPath, browsePath]);

  const navigateToPath = useCallback((path) => {
    return browsePath(path);
  }, [browsePath]);

  return {
    currentPath,
    files,
    loading,
    error,
    browsePath,
    navigateUp,
    navigateToPath
  };
};

export default {
  useApi,
  usePolling,
  useAsyncData,
  useProcessingStatus,
  useFileSystem
}; 