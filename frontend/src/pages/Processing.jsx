import React, { useEffect, useState } from 'react';
import { 
  Card, 
  Progress, 
  Button, 
  Space, 
  Typography, 
  Alert, 
  Timeline,
  Row,
  Col,
  Statistic,
  Tag,
  Spin
} from 'antd';
import { 
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  DashboardOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import { useProcessingStatus } from '../hooks/useApi.js';
import { formatDuration, formatTimestamp, getStatusColor } from '../utils/helpers.js';

const { Title, Text, Paragraph } = Typography;

const Processing = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { currentRun, processingStatus, updateProcessingStatus } = useApp();
  const [logs, setLogs] = useState([]);
  
  const runId = searchParams.get('runId') || currentRun?.id;
  
  // First call the hook without the circular dependency
  const {
    status,
    loading,
    error,
    isComplete,
    isRunning,
    progress
  } = useProcessingStatus(runId, { 
    interval: 2000,
    enabled: true  // Always enable, we'll handle stopping logic inside the hook
  });

  // Update global processing status
  useEffect(() => {
    if (status) {
      updateProcessingStatus(status);
      
      // Add new log entries if available
      if (status.logs && status.logs.length > logs.length) {
        setLogs(status.logs);
      }
    }
  }, [status, updateProcessingStatus, logs.length]);

  // Navigate to dashboard when complete
  useEffect(() => {
    if (isComplete && status?.status === 'completed') {
      // Auto-navigate after a short delay
      const timer = setTimeout(() => {
        navigate(`/dashboard/${runId}`);
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [isComplete, status?.status, runId, navigate]);

  const handleStopProcessing = async () => {
    try {
      // PSEUDOCODE: Stop the processing
      console.log('Stopping processing for run:', runId);
    } catch (err) {
      console.error('Failed to stop processing:', err);
    }
  };

  const handleViewResults = () => {
    navigate(`/dashboard/${runId}`);
  };

  const getStatusIcon = () => {
    if (loading) return <Spin size="small" />;
    
    switch (status?.status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'running':
      case 'processing':
        return <PlayCircleOutlined style={{ color: '#1890ff' }} />;
      default:
        return <PauseCircleOutlined style={{ color: '#faad14' }} />;
    }
  };

  const getPhaseStatus = (phaseName) => {
    if (!status?.phases) return 'wait';
    
    const phase = status.phases.find(p => p.name === phaseName);
    if (!phase) return 'wait';
    
    if (phase.completed) return 'finish';
    if (phase.active) return 'process';
    return 'wait';
  };

  const phases = [
    { name: 'initialization', title: 'Initialization', description: 'Setting up analysis environment' },
    { name: 'extracting', title: 'Code Extraction', description: 'Parsing Python files and extracting structure' },
    { name: 'transforming', title: 'Data Transformation', description: 'Converting to graph format and building relationships' },
    { name: 'loading', title: 'Neo4j Upload', description: 'Uploading to Neo4j database with backup' },
    { name: 'completed', title: 'Complete', description: 'Analysis finished successfully' }
  ];

  if (!runId) {
    return (
      <Alert
        message="No processing run found"
        description="Please start an analysis from the file confirmation page"
        type="warning"
        action={
          <Button type="primary" onClick={() => navigate('/confirm')}>
            Start Analysis
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <div style={{ marginBottom: 24, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>
            {getStatusIcon()} Processing Analysis
          </Title>
          <Text type="secondary">Run ID: {runId}</Text>
        </div>
        
        <Space>
          {isRunning && (
            <Button 
              type="default" 
              icon={<PauseCircleOutlined />}
              onClick={handleStopProcessing}
            >
              Stop Processing
            </Button>
          )}
          
          {isComplete && (
            <Button 
              type="primary" 
              icon={<DashboardOutlined />}
              onClick={handleViewResults}
            >
              View Results
            </Button>
          )}
          
          <Button 
            icon={<ReloadOutlined />}
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
        </Space>
      </div>

      {error && (
        <Alert
          message="Processing Error"
          description={error}
          type="error"
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={8}>
          <Card title="Status Overview" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Current Status</Text>
                <div style={{ marginTop: 8 }}>
                  <Tag 
                    color={getStatusColor(status?.status)} 
                    style={{ marginRight: 8 }}
                  >
                    {status?.status?.toUpperCase() || 'UNKNOWN'}
                  </Tag>
                  <Text>{status?.message || 'Processing...'}</Text>
                </div>
              </div>

              <div>
                <Text strong>Progress</Text>
                <Progress 
                  percent={progress} 
                  status={isComplete ? 'success' : isRunning ? 'active' : 'normal'}
                  style={{ marginTop: 8 }}
                />
              </div>

              <Row gutter={16}>
                <Col span={12}>
                  <Statistic
                    title="Started"
                    value={status?.started_at ? formatTimestamp(status.started_at, 'time') : '--'}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Duration"
                    value={status?.started_at ? formatDuration(status.started_at) : '--'}
                  />
                </Col>
              </Row>

              {status?.files_processed !== undefined && (
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Files Processed"
                      value={status.files_processed || 0}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Total Files"
                      value={status.total_files || 0}
                    />
                  </Col>
                </Row>
              )}
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={16}>
          <Card title="Processing Phases" bordered={false}>
            <Timeline>
              {phases.map((phase, index) => (
                <Timeline.Item
                  key={phase.name}
                  color={
                    getPhaseStatus(phase.name) === 'finish' ? 'green' :
                    getPhaseStatus(phase.name) === 'process' ? 'blue' : 'gray'
                  }
                  dot={
                    getPhaseStatus(phase.name) === 'process' ? <Spin size="small" /> : undefined
                  }
                >
                  <div>
                    <Text strong>{phase.title}</Text>
                    <br />
                    <Text type="secondary">{phase.description}</Text>
                    {getPhaseStatus(phase.name) === 'finish' && (
                      <Tag color="green" size="small" style={{ marginLeft: 8 }}>
                        Complete
                      </Tag>
                    )}
                    {getPhaseStatus(phase.name) === 'process' && (
                      <Tag color="blue" size="small" style={{ marginLeft: 8 }}>
                        In Progress
                      </Tag>
                    )}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        </Col>
      </Row>

      {logs.length > 0 && (
        <Card 
          title="Processing Logs" 
          style={{ marginTop: 24 }}
          bodyStyle={{ 
            maxHeight: 300, 
            overflowY: 'auto',
            fontFamily: 'monospace',
            fontSize: 12,
            background: '#001529',
            color: '#fff'
          }}
        >
          {logs.map((log, index) => (
            <div key={index} style={{ marginBottom: 4 }}>
              <Text style={{ color: '#52c41a' }}>
                [{formatTimestamp(log.timestamp, 'time')}]
              </Text>{' '}
              <Text style={{ color: '#fff' }}>{log.message}</Text>
            </div>
          ))}
        </Card>
      )}

      {isComplete && status?.status === 'completed' && (
        <Alert
          message="Analysis Complete!"
          description="The analysis has been completed successfully. You will be redirected to the dashboard shortly."
          type="success"
          showIcon
          style={{ marginTop: 24 }}
          action={
            <Button type="primary" onClick={handleViewResults}>
              View Results Now
            </Button>
          }
        />
      )}

      {isComplete && status?.status === 'failed' && (
        <Alert
          message="Analysis Failed"
          description={status?.error || "The analysis failed to complete. Please check the logs for more details."}
          type="error"
          showIcon
          style={{ marginTop: 24 }}
          action={
            <Button onClick={() => navigate('/confirm')}>
              Try Again
            </Button>
          }
        />
      )}
    </div>
  );
};

export default Processing; 