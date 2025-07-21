import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Tree,
  Typography,
  Space,
  Button,
  Divider,
  Tag,
  List,
  Descriptions,
  Alert,
  Spin,
  Collapse,
  Badge,
  Tooltip,
  Table,
  Progress
} from 'antd';
import {
  FileOutlined,
  FolderOutlined,
  ArrowLeftOutlined,
  CodeOutlined,
  BugOutlined,
  LinkOutlined,
  FunctionOutlined,
  ApiOutlined,
  SecurityScanOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  DatabaseOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

export const FileExplorer = () => {
  const { runId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [projectFiles, setProjectFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileAnalysis, setFileAnalysis] = useState(null);
  const [analysisLoading, setAnalysisLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (runId) {
      loadProjectFiles();
    }
  }, [runId]);

  const loadProjectFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getNeo4jProjectFiles(runId);
      setProjectFiles(data.files || []);
    } catch (error) {
      console.error('Failed to load project files:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFileSelect = async (file) => {
    try {
      setSelectedFile(file);
      setAnalysisLoading(true);
      const analysis = await api.getNeo4jFileAnalysis(runId, file.path);
      setFileAnalysis(analysis);
    } catch (error) {
      console.error('Failed to load file analysis:', error);
      setError(error.message);
    } finally {
      setAnalysisLoading(false);
    }
  };

  const getRiskColor = (risk) => {
    const colors = {
      'low': '#52c41a',
      'medium': '#faad14', 
      'high': '#ff4d4f',
      'critical': '#722ed1'
    };
    return colors[risk] || '#d9d9d9';
  };

  const getRiskIcon = (risk) => {
    switch (risk) {
      case 'low': return <CheckCircleOutlined />;
      case 'medium': return <WarningOutlined />;
      case 'high': return <ExclamationCircleOutlined />;
      case 'critical': return <BugOutlined />;
      default: return <CheckCircleOutlined />;
    }
  };

  const renderFileList = () => {
    const columns = [
      {
        title: 'File',
        dataIndex: 'name',
        key: 'name',
        render: (name, record) => (
          <Space>
            <FileOutlined style={{ color: '#1890ff' }} />
            <Button 
              type="link" 
              onClick={() => handleFileSelect(record)}
              style={{ padding: 0, fontWeight: record.path === selectedFile?.path ? 'bold' : 'normal' }}
            >
              {name}
            </Button>
          </Space>
        ),
        width: '30%'
      },
      {
        title: 'Risk',
        dataIndex: 'risk_level',
        key: 'risk_level',
        render: (risk) => (
          <Tag color={getRiskColor(risk)} icon={getRiskIcon(risk)}>
            {risk?.toUpperCase()}
          </Tag>
        ),
        width: '12%'
      },
      {
        title: 'LOC',
        dataIndex: 'lines_of_code',
        key: 'lines_of_code',
        sorter: (a, b) => a.lines_of_code - b.lines_of_code,
        width: '8%'
      },
      {
        title: 'Complexity',
        dataIndex: 'complexity_score',
        key: 'complexity_score',
        render: (score) => (
          <Progress 
            percent={Math.min(score * 10, 100)} 
            size="small"
            status={score > 8 ? 'exception' : score > 6 ? 'normal' : 'success'}
            format={() => score.toFixed(1)}
          />
        ),
        width: '15%'
      },
      {
        title: 'Classes',
        dataIndex: 'class_count',
        key: 'class_count',
        width: '8%'
      },
      {
        title: 'Functions',
        dataIndex: 'function_count', 
        key: 'function_count',
        width: '10%'
      },
      {
        title: 'Issues',
        dataIndex: 'has_issues',
        key: 'has_issues',
        render: (hasIssues) => (
          hasIssues ? 
            <Tag color="red" icon={<ExclamationCircleOutlined />}>Issues</Tag> :
            <Tag color="green" icon={<CheckCircleOutlined />}>Clean</Tag>
        ),
        width: '10%'
      }
    ];

    return (
      <Table
        dataSource={projectFiles}
        columns={columns}
        rowKey="path"
        loading={loading}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        scroll={{ y: 600 }}
        onRow={(record) => ({
          onClick: () => handleFileSelect(record),
          style: { 
            cursor: 'pointer',
            backgroundColor: record.path === selectedFile?.path ? '#f0f8ff' : undefined
          }
        })}
      />
    );
  };

  const renderFileAnalysis = () => {
    if (!fileAnalysis) return null;

    const { node_data, classes, functions, imports, relationships, issues } = fileAnalysis;

    return (
      <Space direction="vertical" style={{ width: '100%' }} size={16}>
        {/* File Overview */}
        <Card title={
          <Space>
            <DatabaseOutlined />
            Neo4j Node Data
          </Space>
        } size="small">
          <Descriptions size="small" column={2}>
            <Descriptions.Item label="File Path">{node_data.properties.path}</Descriptions.Item>
            <Descriptions.Item label="Extension">{node_data.properties.extension}</Descriptions.Item>
            <Descriptions.Item label="Lines of Code">{node_data.properties.lines_of_code}</Descriptions.Item>
            <Descriptions.Item label="Risk Level">
              <Tag color={getRiskColor(node_data.properties.risk_level)} icon={getRiskIcon(node_data.properties.risk_level)}>
                {node_data.properties.risk_level?.toUpperCase()}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Complexity">{node_data.properties.complexity_score}</Descriptions.Item>
            <Descriptions.Item label="Last Modified">{new Date(node_data.properties.last_modified).toLocaleString()}</Descriptions.Item>
          </Descriptions>
        </Card>

        {/* Classes and Functions */}
        <Collapse>
          <Panel 
            header={
              <Space>
                <CodeOutlined />
                Classes ({classes.length})
              </Space>
            } 
            key="classes"
          >
            {classes.map((cls, index) => (
              <Card key={index} size="small" style={{ marginBottom: 8 }}>
                <Row gutter={16}>
                  <Col span={8}>
                    <Text strong>{cls.name}</Text>
                    <br />
                    <Text type="secondary">Lines {cls.line_start}-{cls.line_end}</Text>
                  </Col>
                  <Col span={8}>
                    <Text>Methods: </Text>
                    {cls.methods.map(method => (
                      <Tag key={method} size="small" style={{ margin: 2 }}>{method}</Tag>
                    ))}
                  </Col>
                  <Col span={8}>
                    <Tag color={getRiskColor(cls.complexity)}>{cls.complexity} complexity</Tag>
                  </Col>
                </Row>
              </Card>
            ))}
          </Panel>

          <Panel 
            header={
              <Space>
                <FunctionOutlined />
                Functions ({functions.length})
              </Space>
            } 
            key="functions"
          >
            {functions.map((func, index) => (
              <Card key={index} size="small" style={{ marginBottom: 8 }}>
                <Row gutter={16}>
                  <Col span={6}>
                    <Text strong>{func.name}</Text>
                    <br />
                    <Text type="secondary">Lines {func.line_start}-{func.line_end}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>Parameters: </Text>
                    <Text code>{func.parameters.join(', ')}</Text>
                  </Col>
                  <Col span={6}>
                    <Text>Calls: </Text>
                    {func.calls.map(call => (
                      <Tag key={call} size="small" style={{ margin: 2 }}>{call}</Tag>
                    ))}
                  </Col>
                  <Col span={6}>
                    <Tag color={getRiskColor(func.complexity)}>{func.complexity}</Tag>
                  </Col>
                </Row>
              </Card>
            ))}
          </Panel>

          <Panel 
            header={
              <Space>
                <ApiOutlined />
                Imports ({imports.length})
              </Space>
            } 
            key="imports"
          >
            <List
              size="small"
              dataSource={imports}
              renderItem={(imp) => (
                <List.Item>
                  <Space>
                    <Tag color={imp.type === 'standard' ? 'blue' : imp.type === 'third_party' ? 'orange' : 'green'}>
                      {imp.type}
                    </Tag>
                    <Text code>{imp.module}</Text>
                  </Space>
                </List.Item>
              )}
            />
          </Panel>
        </Collapse>

        {/* File Relationships */}
        <Card title={
          <Space>
            <LinkOutlined />
            File Relationships
          </Space>
        }>
          <Row gutter={16}>
            <Col span={12}>
              <Title level={5}>Dependencies ({relationships.depends_on.length})</Title>
              {relationships.depends_on.map((dep, index) => (
                <Card key={index} size="small" style={{ marginBottom: 8, borderLeft: `4px solid ${getRiskColor(dep.strength)}` }}>
                  <Space direction="vertical" size={4}>
                    <Space>
                      <Button 
                        type="link" 
                        size="small"
                        onClick={() => {
                          const file = projectFiles.find(f => f.path === dep.file);
                          if (file) handleFileSelect(file);
                        }}
                      >
                        {dep.file}
                      </Button>
                      <Tag color="blue">{dep.type}</Tag>
                      <Tag color={getRiskColor(dep.strength)}>{dep.strength}</Tag>
                    </Space>
                    <Text type="secondary" style={{ fontSize: 12 }}>{dep.details}</Text>
                  </Space>
                </Card>
              ))}
            </Col>
            <Col span={12}>
              <Title level={5}>Used By ({relationships.used_by.length})</Title>
              {relationships.used_by.map((usage, index) => (
                <Card key={index} size="small" style={{ marginBottom: 8, borderLeft: `4px solid ${getRiskColor(usage.strength)}` }}>
                  <Space direction="vertical" size={4}>
                    <Space>
                      <Button 
                        type="link" 
                        size="small"
                        onClick={() => {
                          const file = projectFiles.find(f => f.path === usage.file);
                          if (file) handleFileSelect(file);
                        }}
                      >
                        {usage.file}
                      </Button>
                      <Tag color="green">{usage.type}</Tag>
                      <Tag color={getRiskColor(usage.strength)}>{usage.strength}</Tag>
                    </Space>
                    <Text type="secondary" style={{ fontSize: 12 }}>{usage.details}</Text>
                  </Space>
                </Card>
              ))}
            </Col>
          </Row>
        </Card>

        {/* Issues */}
        {issues && issues.length > 0 && (
          <Card title={
            <Space>
              <BugOutlined />
              Issues Found ({issues.length})
            </Space>
          }>
            {issues.map((issue, index) => (
              <Alert
                key={index}
                message={issue.message}
                description={
                  <Space direction="vertical" size={4}>
                    <Text type="secondary">Line {issue.line} • {issue.type} • {issue.severity}</Text>
                    <Text>{issue.recommendation}</Text>
                  </Space>
                }
                type={issue.severity === 'high' || issue.severity === 'critical' ? 'error' : 
                      issue.severity === 'medium' ? 'warning' : 'info'}
                showIcon
                style={{ marginBottom: 8 }}
              />
            ))}
          </Card>
        )}
      </Space>
    );
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '60vh' }}>
        <Spin size="large" />
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '64px 24px' }}>
        <Alert
          message="Failed to Load File Explorer"
          description={error}
          type="error"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={loadProjectFiles}>
                Retry
              </Button>
              <Button size="small" onClick={() => navigate('/')}>
                Back to Home
              </Button>
            </Space>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1600, margin: '0 auto' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate(`/dashboard/${runId}`)}
            >
              Back to Dashboard
            </Button>
            <Divider type="vertical" />
            <CodeOutlined style={{ fontSize: 20 }} />
            <Title level={3} style={{ margin: 0 }}>
              File Explorer
            </Title>
          </Space>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            Explore project files with Neo4j graph analysis and relationships
          </Text>
        </div>

        <Row gutter={24}>
          {/* Left Panel - File List */}
          <Col span={selectedFile ? 10 : 24}>
            <Card 
              title={
                <Space>
                  <FolderOutlined />
                  Project Files ({projectFiles.length})
                  {selectedFile && (
                    <Tag color="blue">
                      {selectedFile.name} selected
                    </Tag>
                  )}
                </Space>
              }
            >
              {renderFileList()}
            </Card>
          </Col>

          {/* Right Panel - File Analysis */}
          {selectedFile && (
            <Col span={14}>
              <Card 
                title={
                  <Space>
                    <FileOutlined />
                    {selectedFile.name}
                    <Tag color={getRiskColor(selectedFile.risk_level)}>
                      {selectedFile.risk_level?.toUpperCase()}
                    </Tag>
                  </Space>
                }
                loading={analysisLoading}
                styles={{ body: { maxHeight: '80vh', overflowY: 'auto' } }}
              >
                {renderFileAnalysis()}
              </Card>
            </Col>
          )}
        </Row>
      </Card>
    </div>
  );
};