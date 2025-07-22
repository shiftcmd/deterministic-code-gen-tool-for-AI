import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Button,
  Typography,
  Progress,
  Alert,
  Space,
  Statistic,
  Timeline,
  Tag,
  Divider
} from 'antd';
import {
  StopOutlined,
  CheckCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  FileTextOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { useFramework } from '../../context/FrameworkContext';
import { api } from '../../services/api';
import { usePolling, useErrorHandling } from '../../hooks';

const { Title, Text } = Typography;

export const ProcessingView = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const runId = searchParams.get('runId');
  
  const { currentRun, getRun } = useFramework();
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const [currentPhase, setCurrentPhase] = useState('');
  const [startTime, setStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [isCompleted, setIsCompleted] = useState(false);
  
  // Use custom error handling hook
  const { error, handleError, clearError } = useErrorHandling({
    showNotification: true,
    defaultMessage: 'Processing failed'
  });

  // Load initial run data with error handling
  const loadRunData = useCallback(async () => {
    try {
      clearError(); // Clear any previous errors
      const run = await getRun(runId);
      setStatus(run.status);
      setStartTime(new Date(run.started_at));
      
      if (run.status === 'completed') {
        setIsCompleted(true);
        setProgress(100);
        // Auto-redirect to dashboard after a short delay if analysis is already complete
        setTimeout(() => {
          navigate(`/dashboard/${runId}`);
        }, 1000);
      } else if (run.status === 'failed') {
        handleError(run.error, 'Initial data load');
      }
    } catch (error) {
      handleError(error, 'Failed to load run data');
    }
  }, [runId, getRun, navigate, handleError, clearError]);

  // Polling function for status updates using custom hook
  const pollStatusData = useCallback(async () => {
    const statusData = await api.getProcessingStatus(runId);
    
    // Update all state from polling data
    setStatus(statusData.status);
    setProgress(statusData.progress || 0);
    setCurrentPhase(statusData.current_phase || '');
    
    // Add new logs if available
    if (statusData.logs && statusData.logs.length > logs.length) {
      setLogs(statusData.logs);
    }
    
    // Handle completion
    if (statusData.status === 'completed') {
      setIsCompleted(true);
      setProgress(100);
      // Auto-redirect to dashboard after delay
      setTimeout(() => {
        navigate(`/dashboard/${runId}`);
      }, 2000);
    } else if (statusData.status === 'failed') {
      handleError(statusData.error, 'Processing failed');
    }
    
    return statusData; // Return data for usePolling hook
  }, [runId, logs.length, navigate, handleError]);

  // Use custom polling hook for status updates
  usePolling(
    pollStatusData,
    1000, // Poll every 1 second
    [runId], // Restart polling when runId changes
    !isCompleted && status !== 'failed' // Only poll if not completed
  );

  // Update elapsed time
  const updateElapsedTime = useCallback(() => {
    if (startTime && !isCompleted) {
      const now = new Date();
      const elapsed = Math.floor((now - startTime) / 1000);
      setElapsedTime(elapsed);
    }
  }, [startTime, isCompleted]);

  // Initial data load and elapsed time setup
  useEffect(() => {
    if (!runId) {
      navigate('/');
      return;
    }

    // Load initial run data
    loadRunData();
    
    // Set up elapsed time counter (polling handled by usePolling hook)
    const timeInterval = setInterval(updateElapsedTime, 1000);

    return () => {
      clearInterval(timeInterval);
    };
  }, [runId, navigate, loadRunData, updateElapsedTime]);



  const handleStopProcessing = async () => {
    try {
      await api.stopProcessing(runId);
      setStatus('stopped');
    } catch (error) {
      handleError(error, 'Failed to stop processing');
    }
  };

  const handleViewResults = () => {
    navigate(`/dashboard/${runId}`);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'running':
        return <LoadingOutlined spin style={{ color: '#1890ff' }} />;
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'running': return '#1890ff';
      case 'completed': return '#52c41a';
      case 'failed': return '#ff4d4f';
      default: return '#faad14';
    }
  };

  const phases = [
    { key: 'discovery', title: 'File Discovery', description: 'Scanning project structure' },
    { key: 'parsing', title: 'AST Parsing', description: 'Parsing Python files' },
    { key: 'analysis', title: 'Code Analysis', description: 'Analyzing code patterns' },
    { key: 'validation', title: 'Validation', description: 'Running validation checks' },
    { key: 'export', title: 'Knowledge Graph Export', description: 'Exporting to Neo4j' },
    { key: 'dashboard', title: 'Dashboard Generation', description: 'Preparing results' }
  ];

  const getPhaseStatus = (phaseKey) => {
    const currentIndex = phases.findIndex(p => p.key === currentPhase);
    const phaseIndex = phases.findIndex(p => p.key === phaseKey);
    
    if (isCompleted) return 'finish';
    if (phaseIndex < currentIndex) return 'finish';
    if (phaseIndex === currentIndex) return 'process';
    return 'wait';
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Card>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Space direction="vertical" size={16}>
            <div style={{ fontSize: 48 }}>
              {getStatusIcon()}
            </div>
            <Title level={2} style={{ margin: 0 }}>
              Framework Analysis {status === 'running' ? 'In Progress' : 
                                 status === 'completed' ? 'Completed' :
                                 status === 'failed' ? 'Failed' : 'Starting...'}
            </Title>
            <Tag color={getStatusColor()} style={{ fontSize: 14, padding: '4px 12px' }}>
              {status?.toUpperCase() || 'INITIALIZING'}
            </Tag>
          </Space>
        </div>

        {error && (
          <Alert
            message="Analysis Failed"
            description={error.message || error}
            type="error"
            style={{ marginBottom: 24 }}
            showIcon
          />
        )}

        <Row gutter={24}>
          {/* Left Column - Progress and Phases */}
          <Col span={16}>
            {/* Overall Progress */}
            <Card title="Overall Progress" style={{ marginBottom: 24 }}>
              <Progress
                percent={progress}
                status={status === 'failed' ? 'exception' : 
                       status === 'completed' ? 'success' : 'active'}
                strokeWidth={12}
                style={{ marginBottom: 16 }}
              />
              <Text type="secondary">
                {currentPhase && `Current Phase: ${phases.find(p => p.key === currentPhase)?.title}`}
              </Text>
            </Card>

            {/* Phase Timeline */}
            <Card title="Analysis Phases">
              <Timeline>
                {phases.map(phase => (
                  <Timeline.Item
                    key={phase.key}
                    color={getPhaseStatus(phase.key) === 'finish' ? 'green' :
                           getPhaseStatus(phase.key) === 'process' ? 'blue' : 'gray'}
                    dot={getPhaseStatus(phase.key) === 'process' ? 
                         <LoadingOutlined spin /> : undefined}
                  >
                    <div>
                      <Text strong>{phase.title}</Text>
                      <br />
                      <Text type="secondary">{phase.description}</Text>
                      {phase.key === currentPhase && (
                        <Tag color="blue" style={{ marginLeft: 8 }}>
                          Active
                        </Tag>
                      )}
                    </div>
                  </Timeline.Item>
                ))}
              </Timeline>
            </Card>
          </Col>

          {/* Right Column - Statistics and Actions */}
          <Col span={8}>
            <Space direction="vertical" style={{ width: '100%' }} size={16}>
              
              {/* Statistics */}
              <Card title="Analysis Statistics">
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Files Processed"
                      value={Math.floor((progress / 100) * (currentRun?.file_count || 0))}
                      suffix={`/ ${currentRun?.file_count || 0}`}
                      prefix={<FileTextOutlined />}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Elapsed Time"
                      value={formatTime(elapsedTime)}
                      prefix={<ClockCircleOutlined />}
                    />
                  </Col>
                </Row>
                
                {currentRun && (
                  <>
                    <Divider />
                    <Row gutter={16}>
                      <Col span={24}>
                        <Text type="secondary">Project: </Text>
                        <Text>{currentRun.project_path}</Text>
                      </Col>
                    </Row>
                  </>
                )}
              </Card>

              {/* Actions */}
              <Card title="Actions">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {status === 'running' && (
                    <Button
                      danger
                      block
                      icon={<StopOutlined />}
                      onClick={handleStopProcessing}
                    >
                      Stop Analysis
                    </Button>
                  )}
                  
                  {isCompleted && (
                    <Button
                      type="primary"
                      block
                      size="large"
                      icon={<CheckCircleOutlined />}
                      onClick={handleViewResults}
                    >
                      View Results Dashboard
                    </Button>
                  )}
                  
                  <Button
                    block
                    onClick={() => navigate('/')}
                  >
                    Start New Analysis
                  </Button>
                </Space>
              </Card>

              {/* Live Metrics */}
              {status === 'running' && (
                <Card title="Live Metrics">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text>Analysis Speed: </Text>
                      <Text strong>
                        {elapsedTime > 0 ? 
                          ((Math.floor((progress / 100) * (currentRun?.file_count || 0)) / elapsedTime) * 60).toFixed(1)
                          : '0'} files/min
                      </Text>
                    </div>
                    <div>
                      <Text>Est. Completion: </Text>
                      <Text strong>
                        {progress > 0 && elapsedTime > 0 ? 
                          formatTime(Math.floor((elapsedTime / progress) * (100 - progress)))
                          : '--:--'}
                      </Text>
                    </div>
                    <div>
                      <Text>Current Memory: </Text>
                      <Text strong>--</Text>
                    </div>
                  </Space>
                </Card>
              )}
            </Space>
          </Col>
        </Row>

        {/* Processing Logs */}
        {logs.length > 0 && (
          <Card 
            title="Processing Logs" 
            style={{ marginTop: 24 }}
            styles={{ 
              body: {
                maxHeight: 300, 
                overflowY: 'auto',
                backgroundColor: '#001529',
                color: '#fff',
                fontFamily: 'monospace'
              }
            }}
          >
            {logs.map((log, index) => (
              <div key={index} style={{ marginBottom: 4 }}>
                <Text style={{ color: '#fff', fontSize: 12 }}>
                  [{log.timestamp}] {log.level}: {log.message}
                </Text>
              </div>
            ))}
          </Card>
        )}
      </Card>
    </div>
  );
};