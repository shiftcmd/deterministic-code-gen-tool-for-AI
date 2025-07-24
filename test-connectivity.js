#!/usr/bin/env node

/**
 * Comprehensive Frontend-Backend Connectivity Test
 * Tests all API endpoints and logs detailed debugging information
 */

const axios = require('axios');

const BACKEND_URL = 'http://localhost:8080';
const FRONTEND_URL = 'http://localhost:3015';

const colors = {
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

function log(color, symbol, message) {
  console.log(`${color}${symbol} ${message}${colors.reset}`);
}

async function testEndpoint(name, method, url, data = null) {
  try {
    const config = {
      method,
      url,
      timeout: 5000,
      headers: { 'Content-Type': 'application/json' }
    };
    
    if (data) config.data = data;
    
    const start = Date.now();
    const response = await axios(config);
    const duration = Date.now() - start;
    
    log(colors.green, '✅', `${name}: ${response.status} (${duration}ms)`);
    if (response.data && Object.keys(response.data).length < 10) {
      console.log('   Response:', JSON.stringify(response.data, null, 2));
    } else {
      console.log('   Response size:', JSON.stringify(response.data).length, 'bytes');
    }
    return { success: true, status: response.status, data: response.data, duration };
    
  } catch (error) {
    const status = error.response?.status || 'TIMEOUT';
    const message = error.response?.data?.detail || error.message;
    log(colors.red, '❌', `${name}: ${status} - ${message}`);
    return { success: false, status, error: message };
  }
}

async function runConnectivityTests() {
  log(colors.blue, '🧪', 'Starting Frontend-Backend Connectivity Tests...');
  console.log('');
  
  const results = {};
  
  // Test 1: Backend Health
  log(colors.yellow, '📡', 'Testing Backend Health...');
  results.health = await testEndpoint('Health Check', 'GET', `${BACKEND_URL}/health`);
  
  // Test 2: Frontend Availability  
  log(colors.yellow, '🌐', 'Testing Frontend Availability...');
  results.frontend = await testEndpoint('Frontend Check', 'GET', FRONTEND_URL);
  
  // Test 3: Path Validation
  log(colors.yellow, '📁', 'Testing Path Validation...');
  results.validate = await testEndpoint(
    'Validate Path', 
    'POST', 
    `${BACKEND_URL}/api/filesystem/validate`,
    { path: '.', include_hidden: false, python_only: false }
  );
  
  // Test 4: File Listing
  log(colors.yellow, '📄', 'Testing File Listing...');
  results.files = await testEndpoint(
    'List Files',
    'GET',
    `${BACKEND_URL}/api/files?path=.&python_only=true&limit=5`
  );
  
  // Test 5: Directory Browsing
  log(colors.yellow, '🗂️', 'Testing Directory Browsing...');
  results.browse = await testEndpoint(
    'Browse Directory',
    'GET', 
    `${BACKEND_URL}/api/filesystem/browse?path=.&show_hidden=false`
  );
  
  // Test 6: Copy for Analysis
  log(colors.yellow, '📋', 'Testing Copy for Analysis...');
  results.copyAnalysis = await testEndpoint(
    'Copy for Analysis',
    'POST',
    `${BACKEND_URL}/api/analysis/copy-for-analysis`,
    { source_path: '.', python_only: true }
  );
  
  // Summary
  console.log('');
  log(colors.blue, '📊', 'Test Summary:');
  
  const tests = Object.keys(results);
  const passed = tests.filter(test => results[test].success).length;
  const failed = tests.length - passed;
  
  log(colors.green, '✅', `Passed: ${passed}/${tests.length}`);
  if (failed > 0) {
    log(colors.red, '❌', `Failed: ${failed}/${tests.length}`);
  }
  
  console.log('');
  log(colors.blue, '🔍', 'Debugging Information:');
  
  // Check for common issues
  if (!results.health.success) {
    log(colors.red, '🚨', 'Backend is not running or not accessible');
    log(colors.yellow, '💡', 'Try: npm run start:backend');
  }
  
  if (!results.frontend.success) {
    log(colors.red, '🚨', 'Frontend is not running or not accessible');  
    log(colors.yellow, '💡', 'Try: cd frontend && npm run dev');
  }
  
  if (results.validate.success && results.validate.data) {
    const data = results.validate.data;
    log(colors.green, '📍', `Project path resolved to: ${data.resolved_path}`);
    log(colors.green, '📂', `Is directory: ${data.is_directory}`);
    log(colors.green, '🔍', `Exists: ${data.exists}`);
  }
  
  console.log('');
  log(colors.blue, '🎯', 'Next Steps:');
  console.log('1. Restart backend: npm run start:backend');
  console.log('2. Test frontend: Open http://localhost:3015 in browser');
  console.log('3. Check browser console for frontend errors');
  console.log('4. Monitor backend logs for API calls');
  
  return results;
}

// Run tests if called directly
if (require.main === module) {
  runConnectivityTests().catch(console.error);
}

module.exports = { runConnectivityTests, testEndpoint }; 