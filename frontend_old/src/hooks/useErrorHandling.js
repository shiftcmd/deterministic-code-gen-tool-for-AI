import { useState, useCallback } from 'react';
import { message } from 'antd';

/**
 * Custom hook for consistent error handling across components
 * Provides error state management and user notifications
 * 
 * @param {Object} options - Configuration options
 * @param {boolean} options.showNotification - Whether to show Ant Design message notifications (default: true)
 * @param {string} options.defaultMessage - Default error message if none provided
 * @param {Function} options.onError - Custom error callback
 * @returns {Object} { error, setError, handleError, clearError, hasError }
 */
export const useErrorHandling = (options = {}) => {
  const {
    showNotification = true,
    defaultMessage = 'An unexpected error occurred',
    onError
  } = options;

  const [error, setError] = useState(null);

  const handleError = useCallback((err, context = '') => {
    let errorMessage = defaultMessage;
    let errorDetails = null;

    // Extract error message from different error types
    if (typeof err === 'string') {
      errorMessage = err;
    } else if (err?.message) {
      errorMessage = err.message;
      errorDetails = err;
    } else if (err?.response?.data?.message) {
      errorMessage = err.response.data.message;
      errorDetails = err;
    } else if (err?.response?.statusText) {
      errorMessage = `${err.response.status}: ${err.response.statusText}`;
      errorDetails = err;
    }

    // Add context if provided
    const fullMessage = context ? `${context}: ${errorMessage}` : errorMessage;

    // Set error state
    setError({
      message: fullMessage,
      details: errorDetails,
      timestamp: new Date().toISOString(),
      context
    });

    // Show notification if enabled
    if (showNotification) {
      message.error(fullMessage);
    }

    // Call custom error callback if provided
    if (onError) {
      onError(err, context);
    }

    // Log error for debugging
    console.error(`Error${context ? ` in ${context}` : ''}:`, err);
  }, [defaultMessage, showNotification, onError]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const hasError = error !== null;

  return {
    error,
    setError,
    handleError,
    clearError,
    hasError
  };
};
