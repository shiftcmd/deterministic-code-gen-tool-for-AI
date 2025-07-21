import React, { useState, useEffect } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Table,
  Button,
  Space,
  Tag,
  Typography,
  Alert,
  Drawer,
  Descriptions,
  Timeline,
  Select,
  DatePicker,
  message,
  Tooltip,
  Badge
} from 'antd';
import {
  ExclamationCircleOutlined,
  BugOutlined,
  ApiOutlined,
  UserOutlined,
  ReloadOutlined,
  EyeOutlined,
  DownloadOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { errorLogger } from '../../services/errorLogger';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

export const ErrorDashboard = () => {
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState([]);
  const [stats, setStats] = useState(null);
  const [selectedError, setSelectedError] = useState(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [timeframe, setTimeframe] = useState('24h');
  const [errorReport, setErrorReport] = useState(null);

  useEffect(() => {
    loadErrorData();
  }, [timeframe]);

  const loadErrorData = async () => {
    setLoading(true);
    try {
      // Load local errors (always available)
      const localErrors = errorLogger.getLocalErrors();
      setErrors(localErrors.slice(-100)); // Show last 100 errors

      // Load stats from Supabase if available
      const statsData = await errorLogger.getErrorStats(timeframe);
      setStats(statsData);
    } catch (error) {
      console.error('Failed to load error data:', error);
      message.error('Failed to load error statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleViewError = async (errorId) => {
    try {
      const report = await errorLogger.createErrorReport(errorId);
      setErrorReport(report);
      setSelectedError(report?.error);
      setDrawerVisible(true);
    } catch (error) {
      console.error('Failed to create error report:', error);
      message.error('Failed to load error details');
    }
  };

  const handleExportErrors = () => {
    const errorData = {
      errors: errors,
      stats: stats,
      exportedAt: new Date().toISOString(),
      timeframe: timeframe
    };

    const blob = new Blob([JSON.stringify(errorData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `error-report-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getErrorTypeColor = (type) => {
    const colors = {
      'api_error': 'red',
      'javascript_error': 'orange',
      'react_component_error': 'blue',
      'console_error': 'purple',
      'unhandled_promise_rejection': 'magenta',
      'performance_issue': 'gold',
      'user_action': 'green'
    };
    return colors[type] || 'default';
  };

  const getErrorSeverity = (error) => {
    if (error.status >= 500) return { level: 'critical', color: 'red' };
    if (error.status >= 400) return { level: 'high', color: 'orange' };
    if (error.type === 'javascript_error') return { level: 'medium', color: 'yellow' };
    if (error.type === 'performance_issue') return { level: 'medium', color: 'blue' };
    return { level: 'low', color: 'green' };
  };

  const columns = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 150,
      render: (timestamp) => new Date(timestamp).toLocaleString(),
      sorter: (a, b) => new Date(a.timestamp) - new Date(b.timestamp),
      defaultSortOrder: 'descend'
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      width: 130,
      render: (type) => (
        <Tag color={getErrorTypeColor(type)}>
          {type.replace('_', ' ').toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'API Error', value: 'api_error' },
        { text: 'JavaScript Error', value: 'javascript_error' },
        { text: 'React Component Error', value: 'react_component_error' },
        { text: 'Console Error', value: 'console_error' },
        { text: 'Promise Rejection', value: 'unhandled_promise_rejection' },
        { text: 'Performance Issue', value: 'performance_issue' },
        { text: 'User Action', value: 'user_action' }
      ],
      onFilter: (value, record) => record.type === value
    },
    {
      title: 'Severity',
      key: 'severity',
      width: 100,
      render: (_, record) => {
        const severity = getErrorSeverity(record);
        return (
          <Badge
            color={severity.color}
            text={severity.level.toUpperCase()}
          />
        );
      }
    },
    {
      title: 'Message',
      dataIndex: 'message',
      key: 'message',
      ellipsis: {
        showTitle: false,
      },
      render: (message) => (
        <Tooltip title={message}>
          <Text>{message || 'No message'}</Text>
        </Tooltip>
      )
    },
    {
      title: 'Endpoint',
      dataIndex: 'endpoint',
      key: 'endpoint',
      width: 150,
      ellipsis: true,
      render: (endpoint) => endpoint ? (
        <Text code>{endpoint}</Text>
      ) : '-'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status) => status ? (
        <Tag color={status >= 500 ? 'red' : status >= 400 ? 'orange' : 'green'}>
          {status}
        </Tag>
      ) : '-'
    },
    {
      title: 'Action',
      key: 'action',
      width: 100,
      render: (_, record) => (
        <Button
          icon={<EyeOutlined />}
          size="small"
          onClick={() => handleViewError(record.id)}
        >
          View
        </Button>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <div style={{ marginBottom: 24 }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={2}>
              <BugOutlined /> Error Dashboard
            </Title>
          </Col>
          <Col>
            <Space>
              <Select
                value={timeframe}
                onChange={setTimeframe}
                style={{ width: 120 }}
              >
                <Option value="1h">Last Hour</Option>
                <Option value="24h">Last 24h</Option>
                <Option value="7d">Last 7 days</Option>
                <Option value="30d">Last 30 days</Option>
              </Select>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadErrorData}
                loading={loading}
              >
                Refresh
              </Button>
              <Button
                icon={<DownloadOutlined />}
                onClick={handleExportErrors}
              >
                Export
              </Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* Statistics Cards */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Errors"
              value={stats?.total_errors || errors.length}
              prefix={<ExclamationCircleOutlined style={{ color: '#cf1322' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="API Errors"
              value={stats?.api_errors || errors.filter(e => e.type === 'api_error').length}
              prefix={<ApiOutlined style={{ color: '#fa8c16' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="JavaScript Errors"
              value={stats?.javascript_errors || errors.filter(e => e.type === 'javascript_error').length}
              prefix={<BugOutlined style={{ color: '#fadb14' }} />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Unique Sessions"
              value={stats?.unique_sessions || new Set(errors.map(e => e.sessionId)).size}
              prefix={<UserOutlined style={{ color: '#52c41a' }} />}
            />
          </Card>
        </Col>
      </Row>

      {/* Most Common Error Alert */}
      {stats?.most_common_error && (
        <Alert
          message="Most Common Error"
          description={stats.most_common_error}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      {/* Error Table */}
      <Card title="Recent Errors" extra={<Text type="secondary">Showing last 100 errors</Text>}>
        <Table
          columns={columns}
          dataSource={errors.map(error => ({ ...error, key: error.id }))}
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} errors`
          }}
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* Error Detail Drawer */}
      <Drawer
        title="Error Details"
        width={800}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedError && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Card title="Error Information">
              <Descriptions column={1} bordered>
                <Descriptions.Item label="Error ID">{selectedError.id}</Descriptions.Item>
                <Descriptions.Item label="Type">
                  <Tag color={getErrorTypeColor(selectedError.type)}>
                    {selectedError.type}
                  </Tag>
                </Descriptions.Item>
                <Descriptions.Item label="Timestamp">
                  {new Date(selectedError.timestamp).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="Message">
                  {selectedError.message || 'No message'}
                </Descriptions.Item>
                <Descriptions.Item label="URL">{selectedError.url}</Descriptions.Item>
                {selectedError.endpoint && (
                  <Descriptions.Item label="Endpoint">
                    <Text code>{selectedError.endpoint}</Text>
                  </Descriptions.Item>
                )}
                {selectedError.status && (
                  <Descriptions.Item label="Status Code">
                    <Tag color={selectedError.status >= 500 ? 'red' : selectedError.status >= 400 ? 'orange' : 'green'}>
                      {selectedError.status}
                    </Tag>
                  </Descriptions.Item>
                )}
              </Descriptions>
            </Card>

            {selectedError.stack && (
              <Card title="Stack Trace">
                <Text code style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
                  {selectedError.stack}
                </Text>
              </Card>
            )}

            {errorReport?.possibleSolutions?.length > 0 && (
              <Card title="Possible Solutions">
                <Timeline
                  items={errorReport.possibleSolutions.map((solution, index) => ({
                    children: solution,
                    color: 'blue'
                  }))}
                />
              </Card>
            )}

            {errorReport?.debugSteps?.length > 0 && (
              <Card title="Debug Steps">
                <Timeline
                  items={errorReport.debugSteps.map((step, index) => ({
                    children: step,
                    color: 'green'
                  }))}
                />
              </Card>
            )}

            {errorReport?.relatedDocs?.length > 0 && (
              <Card title="Related Documentation">
                <Space direction="vertical" style={{ width: '100%' }}>
                  {errorReport.relatedDocs.map((doc, index) => (
                    <Card key={index} size="small">
                      <Card.Meta
                        title={doc.title}
                        description={
                          <div>
                            <Paragraph ellipsis={{ rows: 3 }}>
                              {doc.content}
                            </Paragraph>
                            {doc.url && (
                              <Button
                                type="link"
                                href={doc.url}
                                target="_blank"
                                icon={<SearchOutlined />}
                              >
                                View Documentation
                              </Button>
                            )}
                          </div>
                        }
                      />
                    </Card>
                  ))}
                </Space>
              </Card>
            )}

            {selectedError.browserInfo && (
              <Card title="Browser Information">
                <Descriptions column={2} size="small">
                  <Descriptions.Item label="User Agent">
                    {selectedError.browserInfo.userAgent}
                  </Descriptions.Item>
                  <Descriptions.Item label="Platform">
                    {selectedError.browserInfo.platform}
                  </Descriptions.Item>
                  <Descriptions.Item label="Language">
                    {selectedError.browserInfo.language}
                  </Descriptions.Item>
                  <Descriptions.Item label="Online">
                    {selectedError.browserInfo.onLine ? 'Yes' : 'No'}
                  </Descriptions.Item>
                  <Descriptions.Item label="Screen Resolution">
                    {selectedError.browserInfo.screen?.width} x {selectedError.browserInfo.screen?.height}
                  </Descriptions.Item>
                  <Descriptions.Item label="Viewport">
                    {selectedError.browserInfo.viewport?.width} x {selectedError.browserInfo.viewport?.height}
                  </Descriptions.Item>
                </Descriptions>
              </Card>
            )}
          </Space>
        )}
      </Drawer>
    </div>
  );
};