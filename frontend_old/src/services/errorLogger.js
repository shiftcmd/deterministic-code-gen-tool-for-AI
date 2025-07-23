import { createClient } from '@supabase/supabase-js';

class ErrorLogger {
  constructor() {
    // Initialize Supabase client only if valid URLs are provided
    this.supabaseUrl = process.env.REACT_APP_SUPABASE_URL;
    this.supabaseKey = process.env.REACT_APP_SUPABASE_ANON_KEY;
    
    if (this.supabaseUrl && this.supabaseKey && 
        this.supabaseUrl !== 'YOUR_SUPABASE_URL' && 
        this.supabaseKey !== 'YOUR_SUPABASE_ANON_KEY' &&
        this.supabaseUrl.startsWith('http')) {
      try {
        this.supabase = createClient(this.supabaseUrl, this.supabaseKey);
      } catch (error) {
        console.warn('Failed to initialize Supabase client for error logging:', error);
        this.supabase = null;
      }
    } else {
      console.info('Supabase credentials not configured, using local error logging only');
      this.supabase = null;
    }

    // Local error queue for when Supabase is unavailable
    this.errorQueue = [];
    this.isOnline = navigator.onLine;
    
    // Listen for online/offline events
    window.addEventListener('online', this.handleOnline.bind(this));
    window.addEventListener('offline', this.handleOffline.bind(this));
    
    // Setup global error handlers
    this.setupGlobalErrorHandlers();
  }

  setupGlobalErrorHandlers() {
    // Handle unhandled promise rejections
    window.addEventListener('unhandledrejection', (event) => {
      this.logError({
        type: 'unhandled_promise_rejection',
        error: event.reason,
        stack: event.reason?.stack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent
      });
    });

    // Handle JavaScript errors
    window.addEventListener('error', (event) => {
      this.logError({
        type: 'javascript_error',
        error: event.error,
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        userAgent: navigator.userAgent
      });
    });

    // Override console.error to capture additional errors
    const originalConsoleError = console.error;
    console.error = (...args) => {
      this.logError({
        type: 'console_error',
        message: args.join(' '),
        args: args,
        timestamp: new Date().toISOString(),
        url: window.location.href,
        stack: new Error().stack
      });
      originalConsoleError.apply(console, args);
    };
  }

  async logError(errorData) {
    const enrichedError = {
      ...errorData,
      id: this.generateErrorId(),
      sessionId: this.getSessionId(),
      userId: this.getUserId(),
      browserInfo: this.getBrowserInfo(),
      timestamp: errorData.timestamp || new Date().toISOString()
    };

    // Add to local queue first
    this.errorQueue.push(enrichedError);

    // Try to send to Supabase if online
    if (this.isOnline && this.supabase) {
      try {
        await this.sendToSupabase(enrichedError);
        // Remove from queue if successfully sent
        this.errorQueue = this.errorQueue.filter(err => err.id !== enrichedError.id);
      } catch (error) {
        console.warn('Failed to send error to Supabase:', error);
      }
    }

    // Keep local storage backup
    this.saveToLocalStorage(enrichedError);

    return enrichedError.id;
  }

  async sendToSupabase(errorData) {
    if (!this.supabase) return;

    const { error } = await this.supabase
      .from('error_logs')
      .insert([errorData]);

    if (error) {
      throw error;
    }
  }

  async logApiError(endpoint, method, status, response, requestData = null) {
    const errorData = {
      type: 'api_error',
      endpoint,
      method,
      status,
      response: typeof response === 'string' ? response : JSON.stringify(response),
      requestData: requestData ? JSON.stringify(requestData) : null,
      timestamp: new Date().toISOString(),
      url: window.location.href
    };

    return this.logError(errorData);
  }

  async logUserAction(action, data = null, success = true) {
    const actionData = {
      type: 'user_action',
      action,
      data: data ? JSON.stringify(data) : null,
      success,
      timestamp: new Date().toISOString(),
      url: window.location.href
    };

    return this.logError(actionData);
  }

  async logPerformanceIssue(metric, value, threshold) {
    const performanceData = {
      type: 'performance_issue',
      metric,
      value,
      threshold,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      performanceEntries: JSON.stringify(performance.getEntries().slice(-10))
    };

    return this.logError(performanceData);
  }

  handleOnline() {
    this.isOnline = true;
    this.flushErrorQueue();
  }

  handleOffline() {
    this.isOnline = false;
  }

  async flushErrorQueue() {
    if (!this.supabase || this.errorQueue.length === 0) return;

    const errorsToSend = [...this.errorQueue];
    
    for (const error of errorsToSend) {
      try {
        await this.sendToSupabase(error);
        this.errorQueue = this.errorQueue.filter(err => err.id !== error.id);
      } catch (err) {
        console.warn('Failed to flush error to Supabase:', err);
        break; // Stop trying if we hit an error
      }
    }
  }

  saveToLocalStorage(errorData) {
    try {
      const stored = JSON.parse(localStorage.getItem('errorLogs') || '[]');
      stored.push(errorData);
      
      // Keep only last 50 errors in localStorage
      if (stored.length > 50) {
        stored.splice(0, stored.length - 50);
      }
      
      localStorage.setItem('errorLogs', JSON.stringify(stored));
    } catch (error) {
      console.warn('Failed to save error to localStorage:', error);
    }
  }

  getLocalErrors() {
    try {
      return JSON.parse(localStorage.getItem('errorLogs') || '[]');
    } catch (error) {
      console.warn('Failed to retrieve local errors:', error);
      return [];
    }
  }

  clearLocalErrors() {
    localStorage.removeItem('errorLogs');
  }

  generateErrorId() {
    return Date.now().toString(36) + Math.random().toString(36).substr(2, 9);
  }

  getSessionId() {
    let sessionId = sessionStorage.getItem('sessionId');
    if (!sessionId) {
      sessionId = this.generateErrorId();
      sessionStorage.setItem('sessionId', sessionId);
    }
    return sessionId;
  }

  getUserId() {
    // This should be replaced with actual user ID from your auth system
    return localStorage.getItem('userId') || 'anonymous';
  }

  getBrowserInfo() {
    return {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
      screen: {
        width: window.screen.width,
        height: window.screen.height,
        availWidth: window.screen.availWidth,
        availHeight: window.screen.availHeight
      },
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      }
    };
  }

  // Vector search for React documentation errors
  async searchReactDocs(errorMessage, stackTrace = null) {
    if (!this.supabase) {
      console.warn('Supabase not available for React docs search');
      return null;
    }

    try {
      // Create embedding for the error message
      const searchText = `${errorMessage} ${stackTrace || ''}`.slice(0, 1000);
      
      const { data, error } = await this.supabase.rpc('search_react_docs', {
        query_text: searchText,
        match_threshold: 0.7,
        match_count: 5
      });

      if (error) {
        console.error('Error searching React docs:', error);
        return null;
      }

      return data;
    } catch (error) {
      console.error('Failed to search React docs:', error);
      return null;
    }
  }

  // Get error statistics
  async getErrorStats(timeframe = '24h') {
    if (!this.supabase) return null;

    try {
      const { data, error } = await this.supabase.rpc('get_error_stats', {
        timeframe
      });

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Failed to get error stats:', error);
      return null;
    }
  }

  // Create detailed error report
  async createErrorReport(errorId) {
    const localErrors = this.getLocalErrors();
    const error = localErrors.find(err => err.id === errorId);
    
    if (!error) return null;

    const relatedDocs = await this.searchReactDocs(error.message, error.stack);
    
    return {
      error,
      relatedDocs,
      possibleSolutions: this.generatePossibleSolutions(error),
      debugSteps: this.generateDebugSteps(error)
    };
  }

  generatePossibleSolutions(error) {
    const solutions = [];
    
    if (error.message?.includes('500')) {
      solutions.push('Check backend server status and logs');
      solutions.push('Verify API endpoint configuration');
      solutions.push('Check database connectivity');
    }
    
    if (error.message?.includes('Network Error')) {
      solutions.push('Check internet connectivity');
      solutions.push('Verify CORS configuration');
      solutions.push('Check if backend server is running');
    }
    
    if (error.message?.includes('React Router')) {
      solutions.push('Update React Router configuration for v7 compatibility');
      solutions.push('Add future flags to router configuration');
    }
    
    if (error.message?.includes('bodyStyle')) {
      solutions.push('Replace bodyStyle prop with styles.body in Antd components');
    }
    
    return solutions;
  }

  generateDebugSteps(error) {
    const steps = [
      'Reproduce the error in development environment',
      'Check browser console for additional errors',
      'Verify network requests in browser dev tools'
    ];
    
    if (error.type === 'api_error') {
      steps.push('Check backend server logs');
      steps.push('Verify API endpoint exists and is accessible');
      steps.push('Test API endpoint with curl or Postman');
    }
    
    if (error.stack) {
      steps.push('Analyze stack trace for the exact line causing the error');
      steps.push('Check if related components have recent changes');
    }
    
    return steps;
  }
}

// Create singleton instance
export const errorLogger = new ErrorLogger();

// Helper function for React components
export const useErrorLogger = () => {
  const logError = (error, context = {}) => {
    errorLogger.logError({
      type: 'react_component_error',
      error: error.toString(),
      message: error.message,
      stack: error.stack,
      context,
      timestamp: new Date().toISOString()
    });
  };

  const logApiError = (endpoint, method, status, response, requestData) => {
    return errorLogger.logApiError(endpoint, method, status, response, requestData);
  };

  const logUserAction = (action, data, success = true) => {
    return errorLogger.logUserAction(action, data, success);
  };

  return { logError, logApiError, logUserAction };
};