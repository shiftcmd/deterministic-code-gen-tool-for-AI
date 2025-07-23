import React, { createContext, useContext, useReducer, useEffect } from 'react';
import api from '../services/api.js';

// Initial state
const initialState = {
  // Application state
  loading: false,
  error: null,
  
  // Project state
  currentProject: null,
  selectedFiles: [],
  
  // Analysis state
  currentRun: null,
  runs: [],
  processingStatus: null,
  
  // UI state
  theme: 'light',
  sidebarCollapsed: false,
};

// Action types
const actionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  CLEAR_ERROR: 'CLEAR_ERROR',
  
  SET_CURRENT_PROJECT: 'SET_CURRENT_PROJECT',
  SET_SELECTED_FILES: 'SET_SELECTED_FILES',
  
  SET_CURRENT_RUN: 'SET_CURRENT_RUN',
  SET_RUNS: 'SET_RUNS',
  ADD_RUN: 'ADD_RUN',
  UPDATE_RUN: 'UPDATE_RUN',
  REMOVE_RUN: 'REMOVE_RUN',
  SET_PROCESSING_STATUS: 'SET_PROCESSING_STATUS',
  
  SET_THEME: 'SET_THEME',
  TOGGLE_SIDEBAR: 'TOGGLE_SIDEBAR',
};

// Reducer function
const appReducer = (state, action) => {
  switch (action.type) {
    case actionTypes.SET_LOADING:
      return { ...state, loading: action.payload };
    
    case actionTypes.SET_ERROR:
      return { ...state, error: action.payload, loading: false };
    
    case actionTypes.CLEAR_ERROR:
      return { ...state, error: null };
    
    case actionTypes.SET_CURRENT_PROJECT:
      return { ...state, currentProject: action.payload };
    
    case actionTypes.SET_SELECTED_FILES:
      return { ...state, selectedFiles: action.payload };
    
    case actionTypes.SET_CURRENT_RUN:
      return { ...state, currentRun: action.payload };
    
    case actionTypes.SET_RUNS:
      return { ...state, runs: action.payload };
    
    case actionTypes.ADD_RUN:
      return { ...state, runs: [action.payload, ...state.runs] };
    
    case actionTypes.UPDATE_RUN:
      return {
        ...state,
        runs: state.runs.map(run => 
          run.id === action.payload.id ? { ...run, ...action.payload } : run
        )
      };
    
    case actionTypes.REMOVE_RUN:
      return {
        ...state,
        runs: state.runs.filter(run => run.id !== action.payload)
      };
    
    case actionTypes.SET_PROCESSING_STATUS:
      return { ...state, processingStatus: action.payload };
    
    case actionTypes.SET_THEME:
      return { ...state, theme: action.payload };
    
    case actionTypes.TOGGLE_SIDEBAR:
      return { ...state, sidebarCollapsed: !state.sidebarCollapsed };
    
    default:
      return state;
  }
};

// Create context
const AppContext = createContext();

// Provider component
export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Load initial data only if backend is available
  useEffect(() => {
    // Don't auto-load runs on startup to prevent errors when backend isn't ready
    // loadRuns();
  }, []);

  // Actions
  const setLoading = (loading) => {
    dispatch({ type: actionTypes.SET_LOADING, payload: loading });
  };

  const setError = (error) => {
    dispatch({ type: actionTypes.SET_ERROR, payload: error });
  };

  const clearError = () => {
    dispatch({ type: actionTypes.CLEAR_ERROR });
  };

  const selectProject = async (projectPath, isGitRepo = false) => {
    try {
      setLoading(true);
      clearError();
      
      // Real backend API call to analyze project
      const analysisResult = await api.analyzeProject(projectPath, isGitRepo);
      
      dispatch({ 
        type: actionTypes.SET_CURRENT_PROJECT, 
        payload: { 
          path: projectPath, 
          isGitRepo, 
          ...analysisResult 
        } 
      });
      
      return analysisResult;
    } catch (error) {
      setError(`Failed to select project: ${error.message}`);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const updateSelectedFiles = (files) => {
    dispatch({ type: actionTypes.SET_SELECTED_FILES, payload: files });
  };

  const startProcessing = async (config) => {
    try {
      setLoading(true);
      clearError();
      
      // PSEUDOCODE: Start analysis processing
      const runData = await api.startProcessing({
        project: state.currentProject,
        files: state.selectedFiles,
        ...config
      });
      
      dispatch({ type: actionTypes.ADD_RUN, payload: runData });
      dispatch({ type: actionTypes.SET_CURRENT_RUN, payload: runData });
      
      return runData;
    } catch (error) {
      setError(`Failed to start processing: ${error.message}`);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const loadRuns = async () => {
    try {
      setLoading(true);
      const response = await api.getRuns();
      // Handle new mock API response structure
      const runs = response.runs || response || [];
      dispatch({ type: actionTypes.SET_RUNS, payload: runs });
    } catch (error) {
      setError(`Failed to load runs: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const getRun = async (runId) => {
    try {
      setLoading(true);
      const run = await api.getRun(runId);
      dispatch({ type: actionTypes.SET_CURRENT_RUN, payload: run });
      return run;
    } catch (error) {
      setError(`Failed to load run: ${error.message}`);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const deleteRun = async (runId) => {
    try {
      setLoading(true);
      await api.deleteRun(runId);
      dispatch({ type: actionTypes.REMOVE_RUN, payload: runId });
    } catch (error) {
      setError(`Failed to delete run: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const updateProcessingStatus = (status) => {
    dispatch({ type: actionTypes.SET_PROCESSING_STATUS, payload: status });
  };

  const toggleTheme = () => {
    const newTheme = state.theme === 'light' ? 'dark' : 'light';
    dispatch({ type: actionTypes.SET_THEME, payload: newTheme });
    localStorage.setItem('theme', newTheme);
  };

  const toggleSidebar = () => {
    dispatch({ type: actionTypes.TOGGLE_SIDEBAR });
  };

  // Context value
  const value = {
    // State
    ...state,
    
    // Actions
    setLoading,
    setError,
    clearError,
    selectProject,
    updateSelectedFiles,
    startProcessing,
    loadRuns,
    getRun,
    deleteRun,
    updateProcessingStatus,
    toggleTheme,
    toggleSidebar,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

// Custom hook to use the context
export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export default AppContext; 