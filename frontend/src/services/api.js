import axios from 'axios';
import { errorLogger } from './errorLogger';

const API_BASE_URL = 'http://localhost:8080/api';

class ApiService {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
    });

    this.client.interceptors.request.use(
      (config) => {
        // Log API request start
        errorLogger.logUserAction(`API_REQUEST_${config.method?.toUpperCase()}`, {
          url: config.url,
          endpoint: config.url?.split('?')[0]
        });
        return config;
      },
      (error) => {
        errorLogger.logError({
          type: 'api_request_error',
          error: error.toString(),
          message: error.message,
          stack: error.stack
        });
        return Promise.reject(error);
      }
    );

    this.client.interceptors.response.use(
      (response) => {
        // Log successful API response
        errorLogger.logUserAction(`API_SUCCESS_${response.config.method?.toUpperCase()}`, {
          url: response.config.url,
          status: response.status,
          endpoint: response.config.url?.split('?')[0]
        });
        return response.data;
      },
      async (error) => {
        const endpoint = error.config?.url || 'unknown';
        const method = error.config?.method?.toUpperCase() || 'unknown';
        const status = error.response?.status || 0;
        const responseData = error.response?.data;
        const requestData = error.config?.data;

        // Log detailed API error
        await errorLogger.logApiError(endpoint, method, status, responseData, requestData);

        // Enhanced error logging with context
        await errorLogger.logError({
          type: 'api_response_error',
          error: error.toString(),
          message: error.message,
          stack: error.stack,
          endpoint,
          method,
          status,
          responseData,
          requestData,
          timeout: error.code === 'ECONNABORTED',
          networkError: !error.response
        });

        // Search for related React documentation
        if (status >= 400) {
          const relatedDocs = await errorLogger.searchReactDocs(
            `API error ${status} ${endpoint} ${error.message}`,
            error.stack
          );
          
          if (relatedDocs?.length > 0) {
            console.group('📚 Related React Documentation Found:');
            relatedDocs.forEach(doc => {
              console.log(`- ${doc.title}: ${doc.content?.slice(0, 200)}...`);
            });
            console.groupEnd();
          }
        }

        console.error('API Error:', error);
        throw new Error(error.response?.data?.message || error.message);
      }
    );
  }

  // Project Analysis
  async analyzeProject(projectPath, isGitRepo = false) {
    return this.client.post('/projects/analyze', {
      path: projectPath,
      isGitRepo
    });
  }

  async cloneGitRepo(repoUrl, targetPath) {
    return this.client.post('/projects/clone', {
      repoUrl,
      targetPath
    });
  }

  // Processing
  async startProcessing(config) {
    return this.client.post('/processing/start', config);
  }

  async getProcessingStatus(runId) {
    return this.client.get(`/processing/status/${runId}`);
  }

  async stopProcessing(runId) {
    return this.client.post(`/processing/stop/${runId}`);
  }

  // Runs Management
  async getRuns() {
    return this.client.get('/runs');
  }

  async getRun(runId) {
    return this.client.get(`/runs/${runId}`);
  }

  async deleteRun(runId) {
    return this.client.delete(`/runs/${runId}`);
  }

  // Dashboard Data
  async getRunDashboard(runId) {
    return this.client.get(`/runs/${runId}/dashboard`);
  }

  async getRunFiles(runId) {
    return this.client.get(`/runs/${runId}/files`);
  }

  async getRunMetrics(runId) {
    return this.client.get(`/runs/${runId}/metrics`);
  }

  // Neo4j Integration
  async getNeo4jSchema(runId) {
    return this.client.get(`/neo4j/${runId}/schema`);
  }

  async getNeo4jQuery(runId, query) {
    return this.client.post(`/neo4j/${runId}/query`, { query });
  }

  async getNeo4jVisualization(runId, nodeLimit = 100) {
    return this.client.get(`/neo4j/${runId}/visualization`, {
      params: { nodeLimit }
    });
  }

  async getNeo4jProjectFiles(runId) {
    return this.client.get(`/neo4j/${runId}/files`);
  }

  async getNeo4jFileAnalysis(runId, filePath) {
    return this.client.get(`/neo4j/${runId}/file/${encodeURIComponent(filePath)}`);
  }

  // File System
  async browseFileSystem(path = '/') {
    return this.client.get('/filesystem/browse', {
      params: { path }
    });
  }

  async validatePath(path) {
    return this.client.post('/filesystem/validate', { path });
  }

  // Code Generation
  async generateCode(prompt, options = {}) {
    return this.client.post('/generation/generate', {
      prompt,
      ...options
    });
  }

  async validateCode(code, language = 'python') {
    return this.client.post('/generation/validate', {
      code,
      language
    });
  }

  // Export
  async exportResults(runId, format = 'json') {
    return this.client.get(`/export/${runId}/${format}`, {
      responseType: format === 'pdf' ? 'blob' : 'json'
    });
  }
}

export const api = new ApiService();