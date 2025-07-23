import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { api } from '../services/api';

const FrameworkContext = createContext();

const initialState = {
  currentProject: null,
  selectedFiles: [],
  currentRun: null,
  processingStatus: null,
  runs: [],
  loading: false,
  error: null,
};

const frameworkReducer = (state, action) => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload, loading: false };
    
    case 'SET_CURRENT_PROJECT':
      return { ...state, currentProject: action.payload };
    
    case 'SET_SELECTED_FILES':
      return { ...state, selectedFiles: action.payload };
    
    case 'SET_CURRENT_RUN':
      return { ...state, currentRun: action.payload };
    
    case 'SET_PROCESSING_STATUS':
      return { ...state, processingStatus: action.payload };
    
    case 'SET_RUNS':
      return { ...state, runs: action.payload };
    
    case 'ADD_RUN':
      return { ...state, runs: [action.payload, ...state.runs] };
    
    case 'UPDATE_RUN':
      return {
        ...state,
        runs: state.runs.map(run =>
          run.id === action.payload.id ? { ...run, ...action.payload } : run
        ),
        currentRun: state.currentRun?.id === action.payload.id 
          ? { ...state.currentRun, ...action.payload } 
          : state.currentRun
      };
    
    case 'CLEAR_ERROR':
      return { ...state, error: null };
    
    default:
      return state;
  }
};

export const FrameworkProvider = ({ children }) => {
  const [state, dispatch] = useReducer(frameworkReducer, initialState);

  // Load runs on mount
  useEffect(() => {
    loadRuns();
  }, []);

  const loadRuns = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const runs = await api.getRuns();
      dispatch({ type: 'SET_RUNS', payload: runs });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const selectProject = async (projectPath, isGitRepo = false) => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const project = await api.analyzeProject(projectPath, isGitRepo);
      dispatch({ type: 'SET_CURRENT_PROJECT', payload: project });
      dispatch({ type: 'SET_SELECTED_FILES', payload: project.files || [] });
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const updateSelectedFiles = (files) => {
    dispatch({ type: 'SET_SELECTED_FILES', payload: files });
  };

  const startProcessing = async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      
      const run = await api.startProcessing({
        projectPath: state.currentProject.path,
        selectedFiles: state.selectedFiles,
        isGitRepo: state.currentProject.isGitRepo
      });
      
      dispatch({ type: 'SET_CURRENT_RUN', payload: run });
      dispatch({ type: 'ADD_RUN', payload: run });
      
      return run;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const getRun = async (runId) => {
    try {
      const run = await api.getRun(runId);
      dispatch({ type: 'SET_CURRENT_RUN', payload: run });
      return run;
    } catch (error) {
      dispatch({ type: 'SET_ERROR', payload: error.message });
      throw error;
    }
  };

  const clearError = () => {
    dispatch({ type: 'CLEAR_ERROR' });
  };

  const value = {
    ...state,
    selectProject,
    updateSelectedFiles,
    startProcessing,
    getRun,
    loadRuns,
    clearError,
  };

  return (
    <FrameworkContext.Provider value={value}>
      {children}
    </FrameworkContext.Provider>
  );
};

export const useFramework = () => {
  const context = useContext(FrameworkContext);
  if (!context) {
    throw new Error('useFramework must be used within a FrameworkProvider');
  }
  return context;
};