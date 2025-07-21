import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Statistic,
  Progress,
  Typography,
  Space,
  Button,
  Alert,
  Tabs,
  Table,
  Tag,
  Divider,
  Spin,
  Empty,
  Timeline,
  Descriptions,
  Badge,
  Collapse,
  List,
  Tooltip
} from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  BugOutlined,
  CodeOutlined,
  DatabaseOutlined,
  DownloadOutlined,
  ArrowLeftOutlined,
  InfoCircleOutlined,
  SecurityScanOutlined,
  ApiOutlined
} from '@ant-design/icons';
import { useFramework } from '../../context/FrameworkContext';
import { api } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;

export const Dashboard = () => {
  const { runId } = useParams();
  const navigate = useNavigate();
  const { getRun } = useFramework();
  
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [runDetails, setRunDetails] = useState(null);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (runId) {
      loadDashboardData();
    }
  }, [runId]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load run details and dashboard data in parallel
      const [runDetails, dashboardData] = await Promise.all([
        getRun(runId),
        api.getRunDashboard(runId)
      ]);

      setRunDetails(runDetails);
      setDashboardData(dashboardData);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const exportResults = async (format) => {
    try {
      await api.exportResults(runId, format);
    } catch (error) {
      console.error('Export failed:', error);
    }
  };

  const getRiskColor = (risk) => {
    const colors = {
      'minimal': '#52c41a',
      'low': '#fadb14',
      'medium': '#fa8c16',
      'high': '#f5222d',
      'critical': '#722ed1'
    };
    return colors[risk] || '#d9d9d9';
  };

  const getRiskIcon = (risk) => {
    switch (risk) {
      case 'minimal': return <CheckCircleOutlined />;
      case 'low': return <InfoCircleOutlined />;
      case 'medium': return <WarningOutlined />;
      case 'high': return <ExclamationCircleOutlined />;
      case 'critical': return <BugOutlined />;
      default: return <InfoCircleOutlined />;
    }
  };

  const renderOverviewTab = () => {
    if (!dashboardData?.main_analysis) return <Empty description="No analysis data available" />;

    const analysis = dashboardData.main_analysis;
    const stats = analysis.overall_statistics || {};
    const riskAssessment = analysis.risk_assessment || {};
    const codeMetrics = analysis.code_metrics || {};
    const qualityAnalysis = analysis.quality_analysis || {};

    return (
      <Space direction="vertical" style={{ width: '100%' }} size={24}>
        {/* Key Metrics */}
        <Row gutter={24}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Total Files Analyzed"
                value={stats.total_files || 0}
                prefix={<FileTextOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Lines of Code"
                value={stats.total_lines || 0}
                prefix={<CodeOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Syntax Valid Files"
                value={stats.syntax_valid_files || 0}
                suffix={`/${stats.total_files || 0}`}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: stats.syntax_valid_files === stats.total_files ? '#52c41a' : '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Average Confidence"
                value={stats.average_confidence ? (stats.average_confidence * 100).toFixed(1) : 0}
                suffix="%"
                prefix={<SecurityScanOutlined />}
                valueStyle={{ color: stats.average_confidence > 0.8 ? '#52c41a' : '#faad14' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Risk Distribution */}
        <Card title="Risk Assessment" extra={
          <Tooltip title="Risk levels based on framework analysis">
            <InfoCircleOutlined />
          </Tooltip>
        }>
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Total Issues"
                  value={riskAssessment.total_issues || 0}
                  prefix={<ExclamationCircleOutlined />}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Unique Issue Types"
                  value={riskAssessment.unique_issue_types || 0}
                  prefix={<BugOutlined />}
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="High Risk Files"
                  value={riskAssessment.high_risk_files || 0}
                  prefix={<WarningOutlined />}
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="Issues per File"
                  value={stats.total_files ? (riskAssessment.total_issues / stats.total_files).toFixed(1) : '0.0'}
                  prefix={<SecurityScanOutlined />}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
          </Row>
        </Card>

        {/* Analysis Timeline */}
        {analysis.analysis_phases && (
          <Card title="Analysis Timeline">
            <Timeline>
              {analysis.analysis_phases.map((phase, index) => (
                <Timeline.Item
                  key={index}
                  color={phase.status === 'completed' ? 'green' : 'blue'}
                  dot={phase.status === 'completed' ? <CheckCircleOutlined /> : undefined}
                >
                  <div>
                    <Text strong>{phase.name}</Text>
                    <br />
                    <Text type="secondary">
                      {phase.duration ? `${phase.duration}s` : 'In progress...'}
                    </Text>
                    <br />
                    {phase.files_processed && (
                      <Text type="secondary">
                        Processed {phase.files_processed} files
                      </Text>
                    )}
                  </div>
                </Timeline.Item>
              ))}
            </Timeline>
          </Card>
        )}
      </Space>
    );
  };

  const renderFilesTab = () => {
    if (!dashboardData?.main_analysis?.file_details) return <Empty description="No file analysis data" />;

    const files = dashboardData.main_analysis.file_details.map((file, index) => ({
      key: file.file_path || index,
      path: file.file_path || 'Unknown',
      risk_level: file.risk_level || 'minimal',
      lines_of_code: file.lines_of_code || 0,
      validation_passed: file.syntax_valid !== false,
      issues: file.issues || [],
      confidence_score: file.confidence || 0,
      recommendations: file.suggestions || []
    }));

    const columns = [
      {
        title: 'File Path',
        dataIndex: 'path',
        key: 'path',
        render: (path) => (
          <Text code style={{ fontSize: 12 }}>{path}</Text>
        ),
        ellipsis: true,
        width: '40%'
      },
      {
        title: 'Risk Level',
        dataIndex: 'risk_level',
        key: 'risk_level',
        render: (risk) => (
          <Tag color={getRiskColor(risk)} icon={getRiskIcon(risk)}>
            {risk?.toUpperCase() || 'UNKNOWN'}
          </Tag>
        ),
        sorter: (a, b) => {
          const order = ['minimal', 'low', 'medium', 'high', 'critical'];
          return order.indexOf(a.risk_level) - order.indexOf(b.risk_level);
        },
        width: '15%'
      },
      {
        title: 'Lines',
        dataIndex: 'lines_of_code',
        key: 'lines',
        render: (lines) => lines || 0,
        sorter: (a, b) => (a.lines_of_code || 0) - (b.lines_of_code || 0),
        width: '10%'
      },
      {
        title: 'Validation',
        dataIndex: 'validation_passed',
        key: 'validation',
        render: (passed) => (
          <Badge 
            status={passed ? 'success' : 'error'} 
            text={passed ? 'Passed' : 'Failed'} 
          />
        ),
        sorter: (a, b) => (a.validation_passed ? 1 : 0) - (b.validation_passed ? 1 : 0),
        width: '15%'
      },
      {
        title: 'Issues',
        dataIndex: 'issues',
        key: 'issues',
        render: (issues) => issues ? issues.length : 0,
        sorter: (a, b) => (a.issues?.length || 0) - (b.issues?.length || 0),
        width: '10%'
      },
      {
        title: 'Confidence',
        dataIndex: 'confidence_score',
        key: 'confidence',
        render: (score) => (
          <Progress 
            percent={score ? Math.round(score * 100) : 0} 
            size="small"
            status={score > 0.8 ? 'success' : score > 0.6 ? 'normal' : 'exception'}
          />
        ),
        sorter: (a, b) => (a.confidence_score || 0) - (b.confidence_score || 0),
        width: '10%'
      }
    ];

    return (
      <Card title={`File Analysis (${files.length} files)`}>
        <Table
          dataSource={files}
          columns={columns}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} files`
          }}
          scroll={{ x: 1000 }}
          expandable={{
            expandedRowRender: (record) => (
              <div style={{ margin: 0 }}>
                {record.issues && record.issues.length > 0 && (
                  <>
                    <Text strong>Issues Found:</Text>
                    <List
                      size="small"
                      dataSource={record.issues}
                      renderItem={(issue, index) => (
                        <List.Item key={index}>
                          <Space>
                            <Tag color="orange">{issue.type || 'Issue'}</Tag>
                            <Text>{issue.message || issue}</Text>
                          </Space>
                        </List.Item>
                      )}
                    />
                  </>
                )}
                {record.recommendations && (
                  <>
                    <Divider />
                    <Text strong>Recommendations:</Text>
                    <List
                      size="small"
                      dataSource={record.recommendations}
                      renderItem={(rec, index) => (
                        <List.Item key={index}>
                          <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                          {rec}
                        </List.Item>
                      )}
                    />
                  </>
                )}
              </div>
            ),
            rowExpandable: (record) => 
              (record.issues && record.issues.length > 0) || 
              (record.recommendations && record.recommendations.length > 0)
          }}
        />
      </Card>
    );
  };

  const renderRecommendationsTab = () => {
    if (!dashboardData?.actionable_report) return <Empty description="No recommendations available" />;

    const report = dashboardData.actionable_report;
    
    return (
      <Space direction="vertical" style={{ width: '100%' }} size={24}>
        {/* Priority Actions */}
        {report.priority_actions && (
          <Card title="Priority Actions" extra={
            <Tag color="red">High Priority</Tag>
          }>
            <List
              itemLayout="horizontal"
              dataSource={report.priority_actions}
              renderItem={(action, index) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <div style={{ 
                        width: 32, 
                        height: 32, 
                        borderRadius: '50%', 
                        backgroundColor: '#ff4d4f',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white',
                        fontWeight: 'bold'
                      }}>
                        {index + 1}
                      </div>
                    }
                    title={<Text strong>{action.title || action.action}</Text>}
                    description={action.description || action.details}
                  />
                  {action.files && (
                    <Tag color="blue">{action.files.length} files</Tag>
                  )}
                </List.Item>
              )}
            />
          </Card>
        )}

        {/* Recommendations by Category */}
        {report.recommendations_by_category && (
          <Card title="Recommendations by Category">
            <Collapse>
              {Object.entries(report.recommendations_by_category).map(([category, recommendations]) => (
                <Panel 
                  header={
                    <Space>
                      <Text strong>{category.charAt(0).toUpperCase() + category.slice(1)}</Text>
                      <Badge count={recommendations.length} />
                    </Space>
                  } 
                  key={category}
                >
                  <List
                    size="small"
                    dataSource={recommendations}
                    renderItem={(rec) => (
                      <List.Item>
                        <Space>
                          <CheckCircleOutlined style={{ color: '#52c41a' }} />
                          <div>
                            <Text>{rec.message || rec}</Text>
                            {rec.impact && (
                              <>
                                <br />
                                <Text type="secondary" style={{ fontSize: 12 }}>
                                  Impact: {rec.impact}
                                </Text>
                              </>
                            )}
                          </div>
                        </Space>
                      </List.Item>
                    )}
                  />
                </Panel>
              ))}
            </Collapse>
          </Card>
        )}

        {/* Code Quality Improvements */}
        {report.code_quality && (
          <Card title="Code Quality Improvements">
            <Descriptions bordered column={2}>
              {Object.entries(report.code_quality).map(([metric, data]) => (
                <Descriptions.Item 
                  key={metric}
                  label={metric.charAt(0).toUpperCase() + metric.slice(1)}
                >
                  <Space direction="vertical" size={4}>
                    <Text>Current: {data.current || 'N/A'}</Text>
                    <Text type="success">Target: {data.target || 'N/A'}</Text>
                    {data.improvement && (
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {data.improvement}
                      </Text>
                    )}
                  </Space>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>
        )}
      </Space>
    );
  };

  const renderNeo4jTab = () => {
    return (
      <Space direction="vertical" style={{ width: '100%' }} size={24}>
        <Card title="Knowledge Graph Overview" extra={
          <Space>
            <Button icon={<DatabaseOutlined />}>
              Connect to Neo4j
            </Button>
            <Button icon={<ApiOutlined />}>
              Execute Query
            </Button>
          </Space>
        }>
          <Row gutter={24}>
            <Col span={12}>
              <Card size="small" title="Graph Statistics">
                <Descriptions size="small" column={1}>
                  <Descriptions.Item label="Nodes">Loading...</Descriptions.Item>
                  <Descriptions.Item label="Relationships">Loading...</Descriptions.Item>
                  <Descriptions.Item label="Node Types">Loading...</Descriptions.Item>
                  <Descriptions.Item label="Relationship Types">Loading...</Descriptions.Item>
                </Descriptions>
              </Card>
            </Col>
            <Col span={12}>
              <Card size="small" title="Schema Overview">
                <div style={{ 
                  height: 200, 
                  border: '1px dashed #d9d9d9', 
                  borderRadius: 6,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  flexDirection: 'column'
                }}>
                  <DatabaseOutlined style={{ fontSize: 48, color: '#d9d9d9', marginBottom: 16 }} />
                  <Text type="secondary">Neo4j schema visualization will appear here</Text>
                  <Text type="secondary" style={{ fontSize: 12 }}>
                    Connect to Neo4j to view project graph structure
                  </Text>
                </div>
              </Card>
            </Col>
          </Row>
        </Card>

        <Card title="Project Data Schema">
          <Alert
            message="Neo4j Integration"
            description={
              <div>
                <Paragraph>
                  The framework exports analysis results to a Neo4j knowledge graph for advanced querying and visualization. 
                  The schema includes:
                </Paragraph>
                <ul>
                  <li><Text code>File</Text> nodes with metadata and metrics</li>
                  <li><Text code>Class</Text> and <Text code>Function</Text> nodes with analysis results</li>
                  <li><Text code>Dependency</Text> relationships between components</li>
                  <li><Text code>Issue</Text> nodes linked to problematic code sections</li>
                  <li><Text code>Recommendation</Text> nodes with improvement suggestions</li>
                </ul>
                <Paragraph style={{ marginTop: 16 }}>
                  Connect to your Neo4j instance to explore the project's knowledge graph interactively.
                </Paragraph>
              </div>
            }
            type="info"
            showIcon
          />
        </Card>
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
          message="Failed to Load Dashboard"
          description={error}
          type="error"
          showIcon
          action={
            <Space>
              <Button size="small" onClick={loadDashboardData}>
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
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card>
        {/* Header */}
        <div style={{ marginBottom: 24 }}>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/')}
            >
              Back
            </Button>
            <Divider type="vertical" />
            <DashboardOutlined style={{ fontSize: 20 }} />
            <Title level={3} style={{ margin: 0 }}>
              Analysis Dashboard
            </Title>
          </Space>
          
          {runDetails && (
            <div style={{ marginTop: 8 }}>
              <Space>
                <Text type="secondary">Project:</Text>
                <Text code>{runDetails.project_path}</Text>
                <Divider type="vertical" />
                <Text type="secondary">Completed:</Text>
                <Text>{new Date(runDetails.completed_at).toLocaleString()}</Text>
                <Divider type="vertical" />
                <Text type="secondary">Files:</Text>
                <Text>{runDetails.file_count}</Text>
              </Space>
            </div>
          )}
        </div>

        {/* Export Actions */}
        <div style={{ marginBottom: 24, textAlign: 'right' }}>
          <Space>
            <Button 
              icon={<CodeOutlined />}
              onClick={() => navigate(`/explorer/${runId}`)}
            >
              File Explorer
            </Button>
            <Button 
              icon={<DownloadOutlined />}
              onClick={() => exportResults('json')}
            >
              Export JSON
            </Button>
            <Button 
              icon={<DownloadOutlined />}
              onClick={() => exportResults('pdf')}
            >
              Export PDF
            </Button>
          </Space>
        </div>

        {/* Dashboard Tabs */}
        <Tabs 
          activeKey={activeTab} 
          onChange={setActiveTab}
          items={[
            {
              key: 'overview',
              label: (
                <span>
                  <DashboardOutlined />
                  Overview
                </span>
              ),
              children: renderOverviewTab()
            },
            {
              key: 'files',
              label: (
                <span>
                  <FileTextOutlined />
                  Files Analysis
                </span>
              ),
              children: renderFilesTab()
            },
            {
              key: 'recommendations',
              label: (
                <span>
                  <CheckCircleOutlined />
                  Recommendations
                </span>
              ),
              children: renderRecommendationsTab()
            },
            {
              key: 'neo4j',
              label: (
                <span>
                  <DatabaseOutlined />
                  Neo4j Graph
                </span>
              ),
              children: renderNeo4jTab()
            }
          ]}
        />
      </Card>
    </div>
  );
};