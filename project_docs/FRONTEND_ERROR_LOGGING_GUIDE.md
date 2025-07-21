# React Frontend Error Logging & Monitoring System

## Overview

This comprehensive error logging system provides robust error tracking, reporting, and analysis for your React frontend. It includes Supabase integration, vector search for React documentation, and a detailed error dashboard.

## Features Implemented

### 1. Comprehensive Error Logging
- **Automatic Error Capture**: JavaScript errors, unhandled promise rejections, console errors
- **API Error Tracking**: Detailed logging of all API requests/responses with failures
- **User Action Tracking**: User interactions and their success/failure status
- **Performance Issue Detection**: Automatic detection and reporting of performance problems

### 2. Supabase Integration
- **Cloud Storage**: All errors stored in Supabase for persistence and analysis
- **Offline Support**: Local storage fallback when offline, sync when back online
- **Vector Search**: AI-powered search through React documentation for error solutions

### 3. Error Dashboard
- **Real-time Monitoring**: Live view of all application errors
- **Detailed Analysis**: Error categorization, severity levels, and trends
- **Solution Suggestions**: AI-generated solutions and debug steps
- **Export Capabilities**: Export error reports for external analysis

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the frontend directory:

```bash
# Copy the example file
cp .env.example .env

# Edit with your values
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your_anon_key_here
REACT_APP_API_BASE_URL=http://localhost:8080/api
REACT_APP_ENABLE_ERROR_REPORTING=true
REACT_APP_ERROR_REPORTING_LEVEL=debug
REACT_APP_DEBUG_MODE=true
```

### 2. Supabase Database Setup

Run the SQL schema in your Supabase project:

```sql
-- Execute the contents of supabase_error_logging_schema.sql
-- This creates:
-- - error_logs table for storing errors
-- - react_docs table for documentation search
-- - Functions for error statistics and vector search
-- - RLS policies for security
```

### 3. Install Dependencies

```bash
cd frontend
npm install
# Installs @supabase/supabase-js and other required packages
```

## Usage Guide

### Automatic Error Logging

The system automatically captures:

1. **JavaScript Errors**
   - Syntax errors, runtime errors, component crashes
   - Includes full stack traces and browser context

2. **API Errors**
   - Failed HTTP requests with status codes, endpoints, and payloads
   - Network errors and timeouts
   - Automatic retry suggestions

3. **User Actions**
   - Button clicks, form submissions, navigation
   - Success/failure tracking for user workflows

### Manual Error Logging

Use the error logger in your components:

```javascript
import { useErrorLogger } from '../services/errorLogger';

const MyComponent = () => {
  const { logError, logUserAction, logApiError } = useErrorLogger();

  const handleAction = async () => {
    try {
      await logUserAction('BUTTON_CLICK', { buttonId: 'submit' });
      // Your action code here
      await logUserAction('ACTION_SUCCESS', { result: 'completed' });
    } catch (error) {
      await logError(error, {
        component: 'MyComponent',
        action: 'handleAction',
        additionalContext: 'user was trying to submit form'
      });
    }
  };

  return <button onClick={handleAction}>Submit</button>;
};
```

### Error Dashboard Access

Navigate to `/errors` in your application to access the error dashboard, which provides:

- **Error Statistics**: Total errors, API errors, JavaScript errors, unique sessions
- **Error List**: Searchable, filterable table of all errors
- **Error Details**: Detailed view with stack traces, solutions, and debug steps
- **Export Functionality**: Download error reports as JSON

## Error Analysis Features

### 1. Automatic Error Classification

Errors are automatically classified by:
- **Type**: API error, JavaScript error, user action, performance issue
- **Severity**: Critical (5xx), High (4xx), Medium (JS errors), Low (warnings)
- **Source**: Component, API endpoint, browser environment

### 2. Solution Generation

The system provides:
- **Contextual Solutions**: Based on error type and message
- **Debug Steps**: Step-by-step troubleshooting guide
- **Related Documentation**: AI-powered search through React docs

### 3. Performance Monitoring

Automatic detection of:
- Slow API responses (>5 seconds)
- Large component render times
- Memory usage issues
- Network connectivity problems

## Integration with Existing Issues

### Fixed Issues

1. **React Router Deprecation Warnings** ✅
   - Added future flags: `v7_startTransition` and `v7_relativeSplatPath`
   - Router now compatible with v7 migration path

2. **Antd Card bodyStyle Deprecation** ✅
   - Replaced `bodyStyle` with `styles.body` in all components:
     - FileExplorer.js
     - ProjectSelector.js
     - ProcessingView.js

3. **API Error Handling** ✅
   - Enhanced error interceptors with detailed logging
   - Automatic retry suggestions for network errors
   - Related documentation search for API failures

### Current Error Analysis

Based on your error logs:

```
POST http://localhost:8080/api/processing/start 500 (Internal Server Error)
```

**Diagnosis**: Backend server error when starting processing
**Possible Causes**:
1. Backend server not running or crashed
2. Database connection issues
3. Invalid request payload
4. Missing environment variables

**Debug Steps**:
1. Check if backend server is running on port 8080
2. Verify database connectivity
3. Check backend logs for specific error details
4. Validate request payload structure

## Advanced Features

### 1. Vector Search for Documentation

When an error occurs, the system automatically searches through React documentation:

```javascript
// Automatic search when API errors occur
const relatedDocs = await errorLogger.searchReactDocs(
  `API error ${status} ${endpoint} ${error.message}`,
  error.stack
);
```

### 2. Error Statistics and Trends

Get error statistics for analysis:

```javascript
const stats = await errorLogger.getErrorStats('24h');
// Returns: total errors, API errors, JS errors, unique sessions, common errors
```

### 3. Offline Support

- Errors stored locally when offline
- Automatic sync when connection restored
- No data loss during network issues

## SQL Queries for Error Analysis

Use these SQL queries in Supabase to analyze errors:

```sql
-- Get most common errors in last 24 hours
SELECT message, COUNT(*) as count 
FROM error_logs 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY message 
ORDER BY count DESC 
LIMIT 10;

-- Get error trends by hour
SELECT 
  EXTRACT(HOUR FROM timestamp) as hour,
  COUNT(*) as error_count,
  COUNT(*) FILTER (WHERE type = 'api_error') as api_errors
FROM error_logs 
WHERE timestamp >= NOW() - INTERVAL '24 hours'
GROUP BY hour 
ORDER BY hour;

-- Get user sessions with most errors
SELECT 
  session_id,
  COUNT(*) as error_count,
  MIN(timestamp) as session_start,
  MAX(timestamp) as last_error
FROM error_logs 
GROUP BY session_id 
ORDER BY error_count DESC 
LIMIT 10;

-- Search for specific error patterns
SELECT * FROM error_logs 
WHERE message ILIKE '%500%' 
  AND endpoint LIKE '%processing%'
  AND timestamp >= NOW() - INTERVAL '1 hour'
ORDER BY timestamp DESC;
```

## Monitoring and Alerts

### Setting Up Alerts

Create database functions for real-time alerts:

```sql
-- Alert function for critical errors
CREATE OR REPLACE FUNCTION notify_critical_error()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.status >= 500 OR NEW.type = 'javascript_error' THEN
    -- Send notification (implement your preferred method)
    PERFORM pg_notify('critical_error', 
      json_build_object(
        'error_id', NEW.error_id,
        'message', NEW.message,
        'endpoint', NEW.endpoint,
        'timestamp', NEW.timestamp
      )::text
    );
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for new errors
CREATE TRIGGER critical_error_trigger
  AFTER INSERT ON error_logs
  FOR EACH ROW
  EXECUTE FUNCTION notify_critical_error();
```

## Troubleshooting

### Common Issues

1. **Supabase Connection Failed**
   - Check REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY
   - Verify Supabase project is active
   - Check network connectivity

2. **Vector Search Not Working**
   - Ensure pgvector extension is enabled in Supabase
   - Verify react_docs table has data
   - Check RLS policies allow access

3. **Error Dashboard Empty**
   - Trigger some errors to populate data
   - Check local storage for offline errors
   - Verify error logging is enabled

### Performance Considerations

1. **Error Queue Management**
   - Local queue limited to prevent memory issues
   - Automatic cleanup of old errors
   - Batch processing for better performance

2. **Network Optimization**
   - Errors sent in batches when possible
   - Offline support prevents blocking
   - Compression for large error payloads

## Next Steps

1. **Set up monitoring dashboards** in Supabase or external tools
2. **Configure alerts** for critical errors
3. **Implement error analytics** for trend analysis
4. **Add custom error boundaries** for better React error handling
5. **Set up automated error resolution** workflows

## Security Notes

- All error data is subject to RLS policies
- Sensitive data is automatically filtered
- User sessions are anonymized by default
- API keys and secrets are never logged

This system provides comprehensive error monitoring and will help you quickly identify and resolve issues in your React frontend. The 500 error you're experiencing should now be captured with full context, making debugging much easier.