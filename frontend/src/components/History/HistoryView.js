import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Tooltip,
  Popconfirm,
  Empty,
  Alert,
  Row,
  Col,
  Statistic,
  Input,
  Select,
  DatePicker
} from 'antd';
import {
  PlayCircleOutlined,
  DashboardOutlined,
  DeleteOutlined,
  HistoryOutlined,
  ReloadOutlined,
  SearchOutlined,

  FileTextOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';

import { api } from '../../services/api';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

export const HistoryView = () => {
  const navigate = useNavigate();
  // Note: removed unused loading from useFramework()
  
  const [runs, setRuns] = useState([]);
  const [filteredRuns, setFilteredRuns] = useState([]);
  const [loadingRuns, setLoadingRuns] = useState(true);
  const [error, setError] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateRange, setDateRange] = useState([]);

  useEffect(() => {
    loadRuns();
  }, []);

  const filterRuns = useCallback(() => {
    let filtered = runs;

    // Search filter
    if (searchQuery) {
      filtered = filtered.filter(run => 
        run.project_path.toLowerCase().includes(searchQuery.toLowerCase()) ||
        run.id.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }

    // Status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(run => run.status === statusFilter);
    }

    // Date range filter
    if (dateRange.length === 2) {
      filtered = filtered.filter(run => {
        const runDate = new Date(run.created_at);
        return runDate >= dateRange[0].toDate() && runDate <= dateRange[1].toDate();
      });
    }

    setFilteredRuns(filtered);
  }, [runs, searchQuery, statusFilter, dateRange]);

  const loadRuns = async () => {
    try {
      setLoadingRuns(true);
      setError(null);
      const runsData = await api.getRuns();
      setRuns(runsData);
    } catch (error) {
      console.error('Failed to load runs:', error);
      setError(error.message);
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => {
    filterRuns();
  }, [filterRuns]);

  const deleteRun = async (runId) => {
    try {
      await api.deleteRun(runId);
      setRuns(runs.filter(run => run.id !== runId));
    } catch (error) {
      console.error('Failed to delete run:', error);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'running': return 'processing';
      case 'failed': return 'error';
      case 'stopped': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined />;
      case 'running': return <PlayCircleOutlined />;
      case 'failed': return <ExclamationCircleOutlined />;
      case 'stopped': return <ClockCircleOutlined />;
      default: return <ClockCircleOutlined />;
    }
  };

  const formatDuration = (startedAt, completedAt) => {
    if (!startedAt || !completedAt) return 'N/A';
    
    const start = new Date(startedAt);
    const end = new Date(completedAt);
    const durationMs = end - start;
    const durationSec = Math.floor(durationMs / 1000);
    
    if (durationSec < 60) return `${durationSec}s`;
    const minutes = Math.floor(durationSec / 60);
    const seconds = durationSec % 60;
    return `${minutes}m ${seconds}s`;
  };

  const getStats = () => {
    const total = runs.length;
    const completed = runs.filter(run => run.status === 'completed').length;
    const failed = runs.filter(run => run.status === 'failed').length;
    const running = runs.filter(run => run.status === 'running').length;
    
    return { total, completed, failed, running };
  };

  const columns = [
    {
      title: 'Project Path',
      dataIndex: 'project_path',
      key: 'project_path',
      render: (path) => (
        <Tooltip title={path}>
          <Text code style={{ fontSize: 12 }}>
            {path.length > 50 ? `...${path.slice(-47)}` : path}
          </Text>
        </Tooltip>
      ),
      ellipsis: true,
      width: '35%'
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status?.toUpperCase()}
        </Tag>
      ),
      width: '12%'
    },
    {
      title: 'Files',
      dataIndex: 'file_count',
      key: 'file_count',
      render: (count) => (
        <Space>
          <FileTextOutlined />
          {count || 0}
        </Space>
      ),
      sorter: (a, b) => (a.file_count || 0) - (b.file_count || 0),
      width: '10%'
    },
    {
      title: 'Duration',
      key: 'duration',
      render: (_, record) => (
        <Text>{formatDuration(record.started_at, record.completed_at)}</Text>
      ),
      width: '10%'
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      render: (date) => date ? new Date(date).toLocaleString() : 'N/A',
      sorter: (a, b) => new Date(a.started_at || 0) - new Date(b.started_at || 0),
      width: '15%'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {record.status === 'completed' && (
            <Tooltip title="View Dashboard">
              <Button
                type="primary"
                size="small"
                icon={<DashboardOutlined />}
                onClick={() => navigate(`/dashboard/${record.id}`)}
              >
                Dashboard
              </Button>
            </Tooltip>
          )}
          <Tooltip title="Delete Run">
            <Popconfirm
              title="Delete this analysis run?"
              description="This action cannot be undone."
              onConfirm={() => deleteRun(record.id)}
              okText="Delete"
              cancelText="Cancel"
              okType="danger"
            >
              <Button
                danger
                size="small"
                icon={<DeleteOutlined />}
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
      width: '18%'
    }
  ];

  const stats = getStats();

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Space>
            <HistoryOutlined style={{ fontSize: 20 }} />
            <Title level={3} style={{ margin: 0 }}>
              Analysis History
            </Title>
          </Space>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            View and manage previous framework analysis runs
          </Text>
        </div>

        {error && (
          <Alert
            message="Failed to Load History"
            description={error}
            type="error"
            closable
            style={{ marginBottom: 24 }}
            action={
              <Button size="small" onClick={loadRuns}>
                Retry
              </Button>
            }
          />
        )}

        {/* Statistics */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Total Runs"
                value={stats.total}
                prefix={<HistoryOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Completed"
                value={stats.completed}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Failed"
                value={stats.failed}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ color: '#ff4d4f' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="Running"
                value={stats.running}
                prefix={<PlayCircleOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>

        {/* Filters */}
        <Card size="small" style={{ marginBottom: 24 }}>
          <Row gutter={16} align="middle">
            <Col flex="300px">
              <Search
                placeholder="Search by project path or run ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                allowClear
                prefix={<SearchOutlined />}
              />
            </Col>
            <Col flex="150px">
              <Select
                value={statusFilter}
                onChange={setStatusFilter}
                style={{ width: '100%' }}
                placeholder="Filter by status"
              >
                <Option value="all">All Status</Option>
                <Option value="completed">Completed</Option>
                <Option value="running">Running</Option>
                <Option value="failed">Failed</Option>
                <Option value="stopped">Stopped</Option>
              </Select>
            </Col>
            <Col flex="250px">
              <RangePicker
                value={dateRange}
                onChange={setDateRange}
                style={{ width: '100%' }}
                placeholder={['Start Date', 'End Date']}
              />
            </Col>
            <Col flex="auto">
              <Space>
                <Button
                  icon={<ReloadOutlined />}
                  onClick={loadRuns}
                  loading={loadingRuns}
                >
                  Refresh
                </Button>
                <Button
                  type="primary"
                  icon={<PlayCircleOutlined />}
                  onClick={() => navigate('/')}
                >
                  New Analysis
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* Results Table */}
        <Card>
          {filteredRuns.length === 0 && !loadingRuns ? (
            <Empty 
              description="No analysis runs found"
              image={Empty.PRESENTED_IMAGE_SIMPLE}
            >
              <Button 
                type="primary" 
                icon={<PlayCircleOutlined />}
                onClick={() => navigate('/')}
              >
                Start First Analysis
              </Button>
            </Empty>
          ) : (
            <Table
              columns={columns}
              dataSource={filteredRuns}
              rowKey="id"
              loading={loadingRuns}
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) => 
                  `${range[0]}-${range[1]} of ${total} runs`
              }}
              scroll={{ x: 1000 }}
            />
          )}
        </Card>
      </Card>
    </div>
  );
};