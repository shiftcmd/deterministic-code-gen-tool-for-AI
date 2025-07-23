// Utility helper functions for the Python Debug Tool frontend

// Format file size in human readable format
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Format duration in human readable format
export const formatDuration = (startTime, endTime = null) => {
  const end = endTime || Date.now();
  const duration = Math.floor((end - startTime) / 1000);
  
  if (duration < 60) {
    return `${duration}s`;
  } else if (duration < 3600) {
    const minutes = Math.floor(duration / 60);
    const seconds = duration % 60;
    return `${minutes}m ${seconds}s`;
  } else {
    const hours = Math.floor(duration / 3600);
    const minutes = Math.floor((duration % 3600) / 60);
    return `${hours}h ${minutes}m`;
  }
};

// Format timestamp to readable date
export const formatTimestamp = (timestamp, format = 'datetime') => {
  const date = new Date(timestamp);
  
  switch (format) {
    case 'date':
      return date.toLocaleDateString();
    case 'time':
      return date.toLocaleTimeString();
    case 'datetime':
    default:
      return date.toLocaleString();
  }
};

// Get risk level color for UI components
export const getRiskColor = (risk) => {
  const riskColors = {
    minimal: '#52c41a',   // green
    low: '#faad14',       // yellow
    medium: '#fa8c16',    // orange
    high: '#f5222d',      // red
    critical: '#722ed1'   // purple
  };
  
  return riskColors[risk?.toLowerCase()] || '#d9d9d9';
};

// Get status color for UI components
export const getStatusColor = (status) => {
  const statusColors = {
    pending: '#faad14',     // yellow
    running: '#1890ff',     // blue
    completed: '#52c41a',   // green
    failed: '#f5222d',      // red
    cancelled: '#d9d9d9'    // gray
  };
  
  return statusColors[status?.toLowerCase()] || '#d9d9d9';
};

// Debounce function for search inputs
export const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Deep clone object
export const deepClone = (obj) => {
  if (obj === null || typeof obj !== 'object') return obj;
  if (obj instanceof Date) return new Date(obj.getTime());
  if (obj instanceof Array) return obj.map(item => deepClone(item));
  if (typeof obj === 'object') {
    const copy = {};
    Object.keys(obj).forEach(key => {
      copy[key] = deepClone(obj[key]);
    });
    return copy;
  }
};

// Generate unique ID
export const generateId = () => {
  return Math.random().toString(36).substr(2, 9);
};

// Check if file is Python file
export const isPythonFile = (filename) => {
  return filename.toLowerCase().endsWith('.py');
};

// Extract file extension
export const getFileExtension = (filename) => {
  return filename.split('.').pop().toLowerCase();
};

// Get file type icon (for UI)
export const getFileTypeIcon = (filename) => {
  const extension = getFileExtension(filename);
  
  const iconMap = {
    py: 'file-python',
    js: 'file-javascript', 
    jsx: 'file-javascript',
    ts: 'file-typescript',
    tsx: 'file-typescript',
    json: 'file-json',
    md: 'file-markdown',
    txt: 'file-text',
    csv: 'file-excel',
    html: 'file-html',
    css: 'file-css',
    scss: 'file-css',
    yaml: 'file-yaml',
    yml: 'file-yaml'
  };
  
  return iconMap[extension] || 'file';
};

// Validate file path
export const isValidPath = (path) => {
  if (!path || typeof path !== 'string') return false;
  
  // Basic path validation
  const invalidChars = /[<>:"|?*]/;
  return !invalidChars.test(path) && path.trim().length > 0;
};

// Parse error message for user-friendly display
export const parseErrorMessage = (error) => {
  if (typeof error === 'string') return error;
  if (error.message) return error.message;
  if (error.detail) return error.detail;
  return 'An unknown error occurred';
};

// Convert camelCase to Title Case
export const camelToTitle = (camelCase) => {
  return camelCase
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
};

// Capitalize first letter
export const capitalize = (str) => {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
};

// Truncate string with ellipsis
export const truncate = (str, maxLength = 50) => {
  if (!str || str.length <= maxLength) return str;
  return str.substring(0, maxLength) + '...';
};

// Sort array of objects by property
export const sortByProperty = (array, property, direction = 'asc') => {
  return [...array].sort((a, b) => {
    const aVal = a[property];
    const bVal = b[property];
    
    if (direction === 'desc') {
      return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
    }
    return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
  });
};

// Group array by property
export const groupBy = (array, property) => {
  return array.reduce((groups, item) => {
    const key = item[property];
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
    return groups;
  }, {});
};

// Calculate percentage
export const calculatePercentage = (value, total) => {
  if (total === 0) return 0;
  return Math.round((value / total) * 100);
};

// Sleep/delay function for async operations
export const sleep = (ms) => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

export default {
  formatFileSize,
  formatDuration,
  formatTimestamp,
  getRiskColor,
  getStatusColor,
  debounce,
  deepClone,
  generateId,
  isPythonFile,
  getFileExtension,
  getFileTypeIcon,
  isValidPath,
  parseErrorMessage,
  camelToTitle,
  capitalize,
  truncate,
  sortByProperty,
  groupBy,
  calculatePercentage,
  sleep
}; 