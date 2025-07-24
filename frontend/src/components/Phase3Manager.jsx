import React, { useState, useEffect } from 'react';
import {
  Card,
  Button,
  Space,
  Typography,
  Alert,
  Descriptions,
  Tag,
  Progress,
  Statistic,
  Row,
  Col,
  notification
} from 'antd';
import {
  DatabaseOutlined,
  CloudUploadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import api from '../services/api.js';

const { Title, Text } = Typography;

const Phase3Manager = ({ jobId, onStatusChange }) => {
  const [backupStatus, setBackupStatus] = useState(null);
  const [uploadStatus, setUploadStatus] = useState(null);
  const [neo4jStats, setNeo4jStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load Phase 3 status
  const loadPhase3Status = async () => {
    if (!jobId) return;
    
    try {
      setLoading(true);
      setError(null);

      // Get backup status
      try {
        const backup = await api.getBackupStatus(jobId);
        setBackupStatus(backup);
      } catch (err) {
        if (err.message.includes('404')) {
          setBackupStatus({ status: 'not_created', message: 'No backup found' });
        } else {
          throw err;
        }
      }

      // Get upload status
      try {
        const upload = await api.getUploadStatus(jobId);
        setUploadStatus(upload);
      } catch (err) {
        if (err.message.includes('404')) {
          setUploadStatus({ status: 'not_started', message: 'Upload not started' });
        } else {
          throw err;
        }
      }

      // Get Neo4j stats if upload is complete
      try {
        const stats = await api.getNeo4jStats(jobId);
        setNeo4jStats(stats);
      } catch (err) {
        // Neo4j stats might not be available yet
        setNeo4jStats(null);
      }

    } catch (err) {
      setError(`Failed to load Phase 3 status: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPhase3Status();
    
    // Refresh status every 5 seconds if upload is in progress
    const interval = setInterval(() => {
      if (uploadStatus?.status === 'in_progress' || backupStatus?.status === 'in_progress') {
        loadPhase3Status();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobId]);

  // Create backup
  const handleCreateBackup = async () => {
    try {
      setLoading(true);
      await api.createBackup(jobId);
      notification.success({
        message: 'Backup Started',
        description: 'Database backup has been initiated.'
      });
      setTimeout(loadPhase3Status, 1000);
    } catch (err) {
      notification.error({
        message: 'Backup Failed',
        description: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  // Trigger manual upload
  const handleTriggerUpload = async () => {
    try {
      setLoading(true);
      await api.triggerManualUpload(jobId);
      notification.success({
        message: 'Upload Started',
        description: 'Neo4j upload has been initiated.'
      });
      setTimeout(loadPhase3Status, 1000);
    } catch (err) {
      notification.error({
        message: 'Upload Failed',
        description: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  // Restore backup
  const handleRestoreBackup = async () => {
    try {
      setLoading(true);
      await api.restoreBackup(jobId);
      notification.success({
        message: 'Restore Started',
        description: 'Database restore has been initiated.'
      });
      setTimeout(loadPhase3Status, 1000);
    } catch (err) {
      notification.error({
        message: 'Restore Failed',
        description: err.message
      });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return 'success';
      case 'in_progress':
      case 'running':
        return 'processing';
      case 'failed':
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'failed':
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return null;
    }
  };

  if (error) {
    return (
      <Alert
        message="Phase 3 Status Error"
        description={error}
        type="error"
        closable
        action={
          <Button size="small" onClick={loadPhase3Status}>
            Retry
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={4} style={{ margin: 0 }}>
          <DatabaseOutlined /> Phase 3: Neo4j Management
        </Title>
        <Button icon={<ReloadOutlined />} onClick={loadPhase3Status} loading={loading}>
          Refresh
        </Button>
      </div>

      <Row gutter={[16, 16]}>
        {/* Backup Status */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <DatabaseOutlined />
                Database Backup
                {getStatusIcon(backupStatus?.status)}
              </Space>
            }
            bordered={false}
          >
            {backupStatus ? (
              <div>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Status">
                    <Tag color={getStatusColor(backupStatus.status)}>
                      {backupStatus.status?.toUpperCase() || 'UNKNOWN'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Message">
                    {backupStatus.message || 'No message'}
                  </Descriptions.Item>
                  {backupStatus.backup_path && (
                    <Descriptions.Item label="Backup Path">
                      <Text code>{backupStatus.backup_path}</Text>
                    </Descriptions.Item>
                  )}
                  {backupStatus.size_mb && (
                    <Descriptions.Item label="Size">
                      {backupStatus.size_mb.toFixed(2)} MB
                    </Descriptions.Item>
                  )}
                </Descriptions>

                <div style={{ marginTop: 16 }}>
                  <Space>
                    {backupStatus.status === 'not_created' && (
                      <Button 
                        type="primary" 
                        icon={<DatabaseOutlined />}
                        onClick={handleCreateBackup}
                        loading={loading}
                      >
                        Create Backup
                      </Button>
                    )}
                    {backupStatus.status === 'completed' && (
                      <>
                        <Button 
                          icon={<DownloadOutlined />}
                          onClick={handleRestoreBackup}
                          loading={loading}
                        >
                          Restore
                        </Button>
                        <Button 
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => api.deleteBackup(jobId)}
                        >
                          Delete
                        </Button>
                      </>
                    )}
                  </Space>
                </div>
              </div>
            ) : (
              <Text type="secondary">Loading backup status...</Text>
            )}
          </Card>
        </Col>

        {/* Upload Status */}
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <CloudUploadOutlined />
                Neo4j Upload
                {getStatusIcon(uploadStatus?.status)}
              </Space>
            }
            bordered={false}
          >
            {uploadStatus ? (
              <div>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Status">
                    <Tag color={getStatusColor(uploadStatus.status)}>
                      {uploadStatus.status?.toUpperCase() || 'UNKNOWN'}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Phase">
                    {uploadStatus.phase || 'Not started'}
                  </Descriptions.Item>
                  {uploadStatus.upload_stats && (
                    <>
                      <Descriptions.Item label="Nodes Created">
                        {uploadStatus.upload_stats.nodes_created || 0}
                      </Descriptions.Item>
                      <Descriptions.Item label="Relationships">
                        {uploadStatus.upload_stats.relationships_created || 0}
                      </Descriptions.Item>
                    </>
                  )}
                </Descriptions>

                {uploadStatus.cypher_file_ready && (
                  <div style={{ marginTop: 16 }}>
                    <Space>
                      {uploadStatus.status === 'not_started' && (
                        <Button 
                          type="primary" 
                          icon={<CloudUploadOutlined />}
                          onClick={handleTriggerUpload}
                          loading={loading}
                        >
                          Start Upload
                        </Button>
                      )}
                    </Space>
                  </div>
                )}
              </div>
            ) : (
              <Text type="secondary">Loading upload status...</Text>
            )}
          </Card>
        </Col>

        {/* Neo4j Statistics */}
        {neo4jStats && (
          <Col xs={24}>
            <Card title="Neo4j Statistics" bordered={false}>
              <Row gutter={16}>
                <Col span={6}>
                  <Statistic
                    title="Nodes Created"
                    value={neo4jStats.upload_stats?.nodes_created || 0}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Relationships"
                    value={neo4jStats.upload_stats?.relationships_created || 0}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Upload Duration"
                    value={neo4jStats.upload_stats?.upload_duration_seconds || 0}
                    suffix="s"
                    precision={2}
                  />
                </Col>
                <Col span={6}>
                  <Statistic
                    title="Database"
                    value={neo4jStats.neo4j_connection?.database || 'neo4j'}
                  />
                </Col>
              </Row>
            </Card>
          </Col>
        )}
      </Row>
    </div>
  );
};

export default Phase3Manager;