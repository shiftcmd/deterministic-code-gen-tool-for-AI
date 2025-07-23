import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import { Header } from './components/Layout/Header';
import { Sidebar } from './components/Layout/Sidebar';
import { ProjectSelector } from './components/ProjectSelector/ProjectSelector';
import { FileConfirmation } from './components/FileConfirmation/FileConfirmation';
import { ProcessingView } from './components/Processing/ProcessingView';
import { Dashboard } from './components/Dashboard/Dashboard';
import { HistoryView } from './components/History/HistoryView';
import { Neo4jView } from './components/Neo4j/Neo4jView';
import { FileExplorer } from './components/FileExplorer/FileExplorer';
import { ErrorDashboard } from './components/ErrorDashboard/ErrorDashboard';
import { FrameworkProvider } from './context/FrameworkContext';
import { ThemeProvider } from './context/ThemeContext';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <ThemeProvider>
      <FrameworkProvider>
        <Router
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true
          }}
        >
          <Layout style={{ minHeight: '100vh' }}>
            <Header />
            <Layout>
              <Sidebar />
              <Layout style={{ padding: '0 24px 24px', background: 'transparent' }}>
                <Content
                  style={{
                    padding: 24,
                    margin: 0,
                    minHeight: 280,
                    background: 'transparent',
                    borderRadius: 6,
                  }}
                >
                  <Routes>
                    <Route path="/" element={<ProjectSelector />} />
                    <Route path="/confirm" element={<FileConfirmation />} />
                    <Route path="/processing" element={<ProcessingView />} />
                    <Route path="/dashboard/:runId" element={<Dashboard />} />
                    <Route path="/history" element={<HistoryView />} />
                    <Route path="/neo4j/:runId" element={<Neo4jView />} />
                    <Route path="/explorer/:runId" element={<FileExplorer />} />
                    <Route path="/errors" element={<ErrorDashboard />} />
                  </Routes>
                </Content>
              </Layout>
            </Layout>
          </Layout>
        </Router>
      </FrameworkProvider>
    </ThemeProvider>
  );
}

export default App;