import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout, ConfigProvider, theme } from 'antd';
import { AppProvider, useApp } from './context/AppContext.jsx';
import Header from './components/Header.jsx';
import Sidebar from './components/Sidebar.jsx';

// Page components (will create these next)
import ProjectSelector from './pages/ProjectSelector.jsx';
import FileConfirmation from './pages/FileConfirmation.jsx';
import Processing from './pages/Processing.jsx';
import Dashboard from './pages/Dashboard.jsx';
import History from './pages/History.jsx';
import Neo4jGraph from './pages/Neo4jGraph.jsx';
import FileExplorer from './pages/FileExplorer.jsx';
import ErrorDashboard from './pages/ErrorDashboard.jsx';

import './App.css';

const { Content } = Layout;

// Inner app component that has access to context
const AppContent = () => {
  const { theme: appTheme, sidebarCollapsed } = useApp();

  return (
    <ConfigProvider
      theme={{
        algorithm: appTheme === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Header />
        <Layout>
          <Sidebar />
          <Layout 
            style={{ 
              marginLeft: sidebarCollapsed ? 80 : 200,
              transition: 'margin-left 0.2s',
              marginTop: 64 // Header height
            }}
          >
            <Content
              style={{
                margin: '24px',
                padding: '24px 32px',
                minHeight: 'calc(100vh - 112px)', // Full height minus header and margins
                background: appTheme === 'dark' ? '#141414' : '#fff',
                borderRadius: 8,
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                overflow: 'auto'
              }}
            >
              <Routes>
                <Route path="/" element={<ProjectSelector />} />
                <Route path="/confirm" element={<FileConfirmation />} />
                <Route path="/processing" element={<Processing />} />
                <Route path="/dashboard/:runId?" element={<Dashboard />} />
                <Route path="/history" element={<History />} />
                <Route path="/neo4j/:runId?" element={<Neo4jGraph />} />
                <Route path="/explorer/:runId?" element={<FileExplorer />} />
                <Route path="/errors" element={<ErrorDashboard />} />
              </Routes>
            </Content>
          </Layout>
        </Layout>
      </Layout>
    </ConfigProvider>
  );
};

// Main App component with providers
function App() {
  return (
    <AppProvider>
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true
        }}
      >
        <AppContent />
      </Router>
    </AppProvider>
  );
}

export default App;
