import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Row,
  Col,
  Button,
  Input,
  Typography,
  Space,
  Alert,
  Spin,
  Descriptions,
  Table,
  Tag,
  Divider,
  Tabs,
  Form,
  Select,
  Tooltip
} from 'antd';
import {
  DatabaseOutlined,
  PlayCircleOutlined,
  ArrowLeftOutlined,
  ApiOutlined,
  NodeIndexOutlined,
  LinkOutlined,
  SearchOutlined,
  DownloadOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;
const { TabPane } = Tabs;
const { Option } = Select;

export const Neo4jView = () => {
  const { runId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState(false);
  const [schema, setSchema] = useState(null);
  const [queryResult, setQueryResult] = useState(null);
  const [queryLoading, setQueryLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  
  const [form] = Form.useForm();

  useEffect(() => {
    if (runId) {
      loadSchema();
    }
  }, [runId]);

  const loadSchema = async () => {
    try {
      setLoading(true);
      setError(null);
      const schemaData = await api.getNeo4jSchema(runId);
      setSchema(schemaData);
      setConnected(true);
    } catch (error) {
      console.error('Failed to load Neo4j schema:', error);
      setError(error.message);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const executeQuery = async (values) => {
    try {
      setQueryLoading(true);
      const result = await api.getNeo4jQuery(runId, values.query);
      setQueryResult(result);
    } catch (error) {
      console.error('Query failed:', error);
      setError(error.message);
    } finally {
      setQueryLoading(false);
    }
  };

  const sampleQueries = [
    {
      name: 'All Files with Risk Level',
      query: 'MATCH (f:File) RETURN f.path, f.risk_level, f.lines_of_code ORDER BY f.risk_level DESC LIMIT 20'
    },
    {
      name: 'High Risk Files',
      query: 'MATCH (f:File) WHERE f.risk_level IN ["high", "critical"] RETURN f.path, f.risk_level, f.issues'
    },
    {
      name: 'Function Dependencies',
      query: 'MATCH (f1:Function)-[r:CALLS]->(f2:Function) RETURN f1.name, f2.name, type(r) LIMIT 50'
    },
    {
      name: 'Files with Most Issues',
      query: 'MATCH (f:File)-[:HAS_ISSUE]->(i:Issue) WITH f, count(i) as issue_count RETURN f.path, issue_count ORDER BY issue_count DESC LIMIT 10'
    },
    {
      name: 'Class Inheritance Tree',
      query: 'MATCH (c1:Class)-[:INHERITS_FROM]->(c2:Class) RETURN c1.name, c2.name'
    }
  ];

  const renderOverviewTab = () => (
    <Space direction="vertical" style={{ width: '100%' }} size={24}>
      <Card title="Connection Status">
        <Row gutter={24}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Neo4j Status: </Text>
                <Tag color={connected ? 'success' : 'error'} icon={<DatabaseOutlined />}>
                  {connected ? 'Connected' : 'Disconnected'}
                </Tag>
              </div>
              <div>
                <Text strong>Run ID: </Text>
                <Text code>{runId}</Text>
              </div>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadSchema}
                loading={loading}
              >
                Refresh Connection
              </Button>
            </Space>
          </Col>
          <Col span={12}>
            {schema && (
              <Descriptions title="Database Statistics" size="small" column={1}>
                <Descriptions.Item label="Total Nodes">
                  {schema.node_count || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Total Relationships">
                  {schema.relationship_count || 'N/A'}
                </Descriptions.Item>
                <Descriptions.Item label="Node Types">
                  {schema.node_types?.length || 0}
                </Descriptions.Item>
                <Descriptions.Item label="Relationship Types">
                  {schema.relationship_types?.length || 0}
                </Descriptions.Item>
              </Descriptions>
            )}
          </Col>
        </Row>
      </Card>

      {schema && (
        <>
          <Card title="Node Types">
            <Row gutter={16}>
              {schema.node_types?.map((nodeType, index) => (
                <Col span={6} key={index}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <NodeIndexOutlined style={{ fontSize: 24, color: '#1890ff', marginBottom: 8 }} />
                    <div>
                      <Text strong>{nodeType.label}</Text>
                      <br />
                      <Text type="secondary">{nodeType.count} nodes</Text>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>

          <Card title="Relationship Types">
            <Row gutter={16}>
              {schema.relationship_types?.map((relType, index) => (
                <Col span={6} key={index}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <LinkOutlined style={{ fontSize: 24, color: '#52c41a', marginBottom: 8 }} />
                    <div>
                      <Text strong>{relType.type}</Text>
                      <br />
                      <Text type="secondary">{relType.count} relationships</Text>
                    </div>
                  </Card>
                </Col>
              ))}
            </Row>
          </Card>
        </>
      )}
    </Space>
  );

  const renderQueryTab = () => (
    <Space direction="vertical" style={{ width: '100%' }} size={24}>
      <Card title="Query Interface">
        <Form form={form} onFinish={executeQuery} layout="vertical">
          <Row gutter={24}>
            <Col span={16}>
              <Form.Item
                name="query"
                label="Cypher Query"
                rules={[{ required: true, message: 'Please enter a Cypher query' }]}
              >
                <TextArea
                  rows={6}
                  placeholder="MATCH (n:File) RETURN n.path, n.risk_level LIMIT 10"
                  style={{ fontFamily: 'monospace' }}
                />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Sample Queries">
                <Select
                  placeholder="Select a sample query"
                  onChange={(value) => {
                    const query = sampleQueries.find(q => q.name === value)?.query;
                    if (query) {
                      form.setFieldsValue({ query });
                    }
                  }}
                  style={{ width: '100%', marginBottom: 16 }}
                >
                  {sampleQueries.map(query => (
                    <Option key={query.name} value={query.name}>
                      {query.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              <Form.Item>
                <Button
                  type="primary"
                  htmlType="submit"
                  icon={<PlayCircleOutlined />}
                  loading={queryLoading}
                  block
                  size="large"
                >
                  Execute Query
                </Button>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Card>

      {queryResult && (
        <Card 
          title="Query Results"
          extra={
            <Button
              icon={<DownloadOutlined />}
              onClick={() => {
                const dataStr = JSON.stringify(queryResult, null, 2);
                const dataBlob = new Blob([dataStr], { type: 'application/json' });
                const url = URL.createObjectURL(dataBlob);
                const link = document.createElement('a');
                link.href = url;
                link.download = 'neo4j-query-result.json';
                link.click();
              }}
            >
              Export
            </Button>
          }
        >
          {queryResult.records && queryResult.records.length > 0 ? (
            <Table
              dataSource={queryResult.records.map((record, index) => ({
                key: index,
                ...record
              }))}
              columns={
                queryResult.columns?.map(col => ({
                  title: col,
                  dataIndex: col,
                  key: col,
                  render: (value) => {
                    if (typeof value === 'object') {
                      return <Text code>{JSON.stringify(value)}</Text>;
                    }
                    return value;
                  }
                })) || []
              }
              pagination={{ pageSize: 20 }}
              scroll={{ x: 800 }}
            />
          ) : (
            <Alert
              message="No Results"
              description="The query returned no results."
              type="info"
              showIcon
            />
          )}
        </Card>
      )}
    </Space>
  );

  const renderVisualizationTab = () => (
    <Space direction="vertical" style={{ width: '100%' }} size={24}>
      <Card title="Graph Visualization">
        <Alert
          message="Visualization Coming Soon"
          description={
            <div>
              <Paragraph>
                Interactive graph visualization will be available here. This will include:
              </Paragraph>
              <ul>
                <li>Node-link diagrams showing file dependencies</li>
                <li>Risk heat maps overlayed on code structure</li>
                <li>Interactive filtering by node and relationship types</li>
                <li>Zoom and pan capabilities for large graphs</li>
                <li>Export capabilities for presentations</li>
              </ul>
              <Paragraph style={{ marginTop: 16 }}>
                Use the Query tab to explore your data in the meantime.
              </Paragraph>
            </div>
          }
          type="info"
          showIcon
        />
        
        <div style={{ 
          height: 400, 
          border: '2px dashed #d9d9d9', 
          borderRadius: 8,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          marginTop: 24
        }}>
          <DatabaseOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 16 }} />
          <Text type="secondary" style={{ fontSize: 16 }}>
            Graph visualization area
          </Text>
          <Text type="secondary">
            Interactive Neo4j graph will render here
          </Text>
        </div>
      </Card>
    </Space>
  );

  if (!connected && !loading) {
    return (
      <div style={{ maxWidth: 800, margin: '0 auto', padding: '64px 24px' }}>
        <Card>
          <div style={{ textAlign: 'center' }}>
            <DatabaseOutlined style={{ fontSize: 64, color: '#d9d9d9', marginBottom: 24 }} />
            <Title level={3}>Neo4j Not Connected</Title>
            <Paragraph>
              Unable to connect to Neo4j database for this analysis run.
              The framework may not have exported data to Neo4j yet, or the connection configuration needs to be updated.
            </Paragraph>
            <Space>
              <Button onClick={() => navigate('/')} icon={<ArrowLeftOutlined />}>
                Back to Home
              </Button>
              <Button type="primary" onClick={loadSchema} icon={<ReloadOutlined />}>
                Retry Connection
              </Button>
            </Space>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 1400, margin: '0 auto' }}>
      <Card>
        <div style={{ marginBottom: 24 }}>
          <Space>
            <Button 
              icon={<ArrowLeftOutlined />} 
              onClick={() => navigate('/')}
            >
              Back
            </Button>
            <Divider type="vertical" />
            <DatabaseOutlined style={{ fontSize: 20 }} />
            <Title level={3} style={{ margin: 0 }}>
              Neo4j Knowledge Graph
            </Title>
          </Space>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            Explore the project's knowledge graph and execute Cypher queries
          </Text>
        </div>

        {error && (
          <Alert
            message="Neo4j Error"
            description={error}
            type="error"
            closable
            style={{ marginBottom: 24 }}
            onClose={() => setError(null)}
          />
        )}

        <Spin spinning={loading}>
          <Tabs activeKey={activeTab} onChange={setActiveTab}>
            <TabPane 
              tab={
                <span>
                  <DatabaseOutlined />
                  Overview
                </span>
              } 
              key="overview"
            >
              {renderOverviewTab()}
            </TabPane>
            
            <TabPane 
              tab={
                <span>
                  <ApiOutlined />
                  Query
                </span>
              } 
              key="query"
            >
              {renderQueryTab()}
            </TabPane>
            
            <TabPane 
              tab={
                <span>
                  <NodeIndexOutlined />
                  Visualization
                </span>
              } 
              key="visualization"
            >
              {renderVisualizationTab()}
            </TabPane>
          </Tabs>
        </Spin>
      </Card>
    </div>
  );
};