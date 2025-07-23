// Environment variables
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

// Simple API client wrapper
const apiClient = {
  async get(endpoint) {
    try {
      console.log('🔄 API GET Request:', `${API_BASE_URL}${endpoint}`);
      const response = await fetch(`${API_BASE_URL}${endpoint}`);
      console.log('📥 API GET Response Status:', response.status);
      if (!response.ok) throw new Error(`API request failed: ${response.status}`);
      const data = await response.json();
      console.log('📥 API GET Response Data:', data);
      return data;
    } catch (error) {
      console.error('❌ API GET error:', error);
      throw error;
    }
  },

  async post(endpoint, data) {
    try {
      console.log('🔄 API POST Request:', `${API_BASE_URL}${endpoint}`);
      console.log('📤 API POST Data:', data);
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      console.log('📥 API POST Response Status:', response.status);
      if (!response.ok) {
        const errorText = await response.text();
        console.error('❌ API POST Error Response:', errorText);
        throw new Error(`API request failed: ${response.status} - ${errorText}`);
      }
      const responseData = await response.json();
      console.log('📥 API POST Response Data:', responseData);
      return responseData;
    } catch (error) {
      console.error('❌ API POST error:', error);
      throw error;
    }
  },

  async put(endpoint, data) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });
      if (!response.ok) throw new Error(`API request failed: ${response.status}`);
      return response.json();
    } catch (error) {
      console.error('API PUT error:', error);
      throw error;
    }
  },

  async delete(endpoint) {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error(`API request failed: ${response.status}`);
      return response.json();
    } catch (error) {
      console.error('API DELETE error:', error);
      throw error;
    }
  }
};

// Specific API functions for the Python Debug Tool
export const api = {
  // Health check
  async healthCheck() {
    // Real API call to backend health endpoint
    return apiClient.get('/api/health');
  },

  // Project analysis endpoints
  async analyzeProject(projectPath, isGitRepo = false) {
    // Real API call to validate and analyze project structure
    try {
      // First validate the path
      const validation = await this.validatePath(projectPath);
      if (!validation.valid) {
        throw new Error(validation.error || 'Invalid project path');
      }

      // Then get project files to analyze structure
      const filesResponse = await this.getProjectFiles(projectPath, true);
      
      return {
        path: projectPath,
        isGitRepo,
        totalFiles: filesResponse.total_count,
        pythonFiles: filesResponse.files.filter(f => f.is_python).length,
        directories: filesResponse.files.filter(f => f.type === 'directory').length,
        totalSize: filesResponse.files.reduce((sum, f) => sum + (f.size || 0), 0),
        valid: true,
        files: filesResponse.files
      };
    } catch (error) {
      console.error('Failed to analyze project:', error);
      throw error;
    }
  },

  async getProcessingStatus(runId) {
    // Real API call to get processing status
    return apiClient.get(`/api/processing/status/${runId}`);
  },

  async stopProcessing(runId) {
    // Real API call to stop processing
    return apiClient.post(`/api/processing/stop/${runId}`);
  },

  // File system operations - REAL implementations using backend endpoints
  async browseFileSystem(path = '.') {
    // Real API call to backend /api/filesystem/browse endpoint
    try {
      const params = new URLSearchParams({
        path: path,
        show_hidden: 'false'
      });
      
      const response = await apiClient.get(`/api/filesystem/browse?${params}`);
      
      // Transform backend response to frontend expected format
      return {
        currentPath: response.current_path,
        files: [
          ...response.directories.map(dir => ({
            name: dir.name,
            path: dir.path,
            type: 'directory',
            size: dir.size,
            lastModified: dir.last_modified
          })),
          ...response.files.map(file => ({
            name: file.name,
            path: file.path,
            type: file.type,
            size: file.size,
            lastModified: file.last_modified,
            is_python: file.is_python || false
          }))
        ],
        parentPath: response.parent_path
      };
    } catch (error) {
      console.error('Failed to browse filesystem:', error);
      throw error;
    }
  },

  async getProjectFiles(path, pythonOnly = true) {
    // Real API call to backend /api/files endpoint
    try {
      const params = new URLSearchParams({
        path: path,
        python_only: pythonOnly.toString(),
        limit: '100'
      });
      
      const response = await apiClient.get(`/api/files?${params}`);
      
      // Transform backend response to frontend expected format
      return {
        path: response.base_path,
        files: response.files.map(file => ({
          name: file.name,
          path: file.path,
          relativePath: file.relative_path,
          type: file.type,
          size: file.size,
          is_python: file.is_python,
          lastModified: file.last_modified
        })),
        pythonOnly,
        total: response.total_count,
        showing: response.showing,
        truncated: response.truncated
      };
    } catch (error) {
      console.error('Failed to get project files:', error);
      throw error;
    }
  },

  async validatePath(path) {
    // Real API call to backend /api/filesystem/validate endpoint
    try {
      const response = await apiClient.post('/api/filesystem/validate', {
        path: path,
        include_hidden: false,
        python_only: false
      });
      
      return {
        path: response.path,
        valid: response.valid,
        exists: response.exists,
        type: response.type,
        readable: response.readable,
        pythonFilesCount: response.python_files_count,
        size: response.size,
        error: response.error
      };
    } catch (error) {
      console.error('Failed to validate path:', error);
      throw error;
    }
  },

  // Analysis runs management
  async getRuns() {
    // Real API call to get analysis runs
    return apiClient.get('/api/runs');
  },

  async getRun(runId) {
    // Real API call to get specific run
    return apiClient.get(`/api/runs/${runId}`);
  },

  async deleteRun(runId) {
    // Real API call to delete run
    return apiClient.delete(`/api/runs/${runId}`);
  },

  // Processing endpoints
  async startProcessing(config) {
    // Real API call to start processing
    return apiClient.post('/api/projects/analyze', {
      path: config.project?.path || '.',
      config_preset: 'standard',
      include_relationships: true,
      export_to_neo4j: false,
      cache_results: true
    });
  },

  // Dashboard data
  async getDashboardData(runId) {
    // Real API call to get dashboard data
    return apiClient.get(`/api/runs/${runId}/dashboard`);
  }
};

export default api; 