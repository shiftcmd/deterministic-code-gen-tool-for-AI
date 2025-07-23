import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Input,
  Select,
  Form,
  Space,
  Alert,
  Spin,
  Divider,
  Typography,
  Row,
  Col,
  Tag,
  Tooltip,
  Breadcrumb
} from 'antd';
import {
  FolderOpenOutlined,
  GitlabOutlined,
  GithubOutlined,
  SearchOutlined,
  InfoCircleOutlined,
  CodeOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import { useFramework } from '../../context/FrameworkContext';
import { api } from '../../services/api';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

export const ProjectSelector = () => {
  const navigate = useNavigate();
  const { selectProject, loading, error, clearError } = useFramework();
  const [form] = Form.useForm();
  const [inputType, setInputType] = useState('local');
  const [browsing, setBrowsing] = useState(false);
  const [currentPath, setCurrentPath] = useState('/');
  const [fileTree, setFileTree] = useState([]);
  const [projectStats, setProjectStats] = useState(null);

  useEffect(() => {
    if (inputType === 'local') {
      loadFileTree('/home');
    }
  }, [inputType]);

  const loadFileTree = async (path) => {
    try {
      setBrowsing(true);
      const tree = await api.browseFileSystem(path);
      
      // Add parent directory navigation if not at root
      if (path !== '/' && path !== '/home') {
        const parentPath = path.split('/').slice(0, -1).join('/') || '/';
        tree.unshift({
          name: '..',
          path: parentPath,
          type: 'directory',
          isParent: true
        });
      }
      
      setFileTree(tree);
      setCurrentPath(path);
    } catch (error) {
      console.error('Failed to load file tree:', error);
    } finally {
      setBrowsing(false);
    }
  };

  const validateAndAnalyzeProject = async (values) => {
    try {
      clearError();
      
      let projectPath = values.projectPath;
      let isGitRepo = inputType === 'git';

      // If Git repo, clone it first
      if (isGitRepo) {
        const cloneResult = await api.cloneGitRepo(values.gitUrl, values.targetPath);
        projectPath = cloneResult.path;
      }

      // Validate path
      const validation = await api.validatePath(projectPath);
      if (!validation.valid) {
        throw new Error(validation.message);
      }

      // Get project statistics
      const stats = await getProjectStats(projectPath);
      setProjectStats(stats);

      // Select the project
      await selectProject(projectPath, isGitRepo);
      navigate('/confirm');

    } catch (error) {
      console.error('Project selection failed:', error);
    }
  };

  const getProjectStats = async (path) => {
    try {
      const stats = await api.analyzeProject(path, false);
      return {
        totalFiles: stats.files?.length || 0,
        pythonFiles: stats.files?.filter(f => f.path.endsWith('.py')).length || 0,
        directories: stats.directories?.length || 0,
        estimatedTime: Math.ceil((stats.files?.length || 0) * 0.1) // Rough estimate
      };
    } catch (error) {
      return null;
    }
  };

  const renderFileTreeItem = (item, level = 0) => (
    <div
      key={item.path}
      style={{
        paddingLeft: item.isParent ? 0 : level * 20,
        padding: '6px 12px',
        cursor: item.type === 'directory' ? 'pointer' : 'default',
        borderRadius: 4,
        margin: '2px 0',
        transition: 'all 0.2s ease'
      }}
      className={`file-tree-item ${item.type === 'directory' ? 'file-tree-directory' : ''}`}
      onClick={() => {
        if (item.type === 'directory') {
          form.setFieldsValue({ projectPath: item.path });
          loadFileTree(item.path);
        }
      }}
    >
      <Space>
        {item.isParent ? (
          <>
            <FolderOpenOutlined style={{ color: '#8c8c8c' }} />
            <Text style={{ color: '#8c8c8c' }}>Parent Directory</Text>
          </>
        ) : item.type === 'directory' ? (
          <>
            <FolderOpenOutlined style={{ color: '#1890ff' }} />
            <Text strong>{item.name}</Text>
          </>
        ) : (
          <>
            <FileTextOutlined style={{ color: '#666' }} />
            <Text>{item.name}</Text>
          </>
        )}
        {item.type === 'directory' && !item.isParent && item.children?.length > 0 && (
          <Tag size="small">{item.children.length} items</Tag>
        )}
      </Space>
    </div>
  );

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 0' }}>
      <Card>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <CodeOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <Title level={2}>Deterministic AI Framework</Title>
          <Paragraph type="secondary" style={{ fontSize: 16 }}>
            Select a Python project or Git repository to analyze with the framework
          </Paragraph>
        </div>

        {error && (
          <Alert
            message="Error"
            description={error}
            type="error"
            closable
            onClose={clearError}
            style={{ marginBottom: 24 }}
          />
        )}

        <Form
          form={form}
          layout="vertical"
          onFinish={validateAndAnalyzeProject}
          size="large"
        >
          <Row gutter={24}>
            <Col span={24}>
              <Form.Item label="Source Type">
                <Select
                  value={inputType}
                  onChange={setInputType}
                  style={{ width: '100%' }}
                >
                  <Option value="local">
                    <Space>
                      <FolderOpenOutlined />
                      Local Folder
                    </Space>
                  </Option>
                  <Option value="git">
                    <Space>
                      <GithubOutlined />
                      Git Repository
                    </Space>
                  </Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          {inputType === 'local' && (
            <Row gutter={24}>
              <Col span={16}>
                <Form.Item
                  name="projectPath"
                  label="Project Path"
                  rules={[{ required: true, message: 'Please select a project path' }]}
                >
                  <Input
                    placeholder="/path/to/your/python/project"
                    prefix={<FolderOpenOutlined />}
                    suffix={
                      <Tooltip title="Browse for folder">
                        <Button
                          type="text"
                          icon={<SearchOutlined />}
                          onClick={() => loadFileTree(currentPath)}
                        />
                      </Tooltip>
                    }
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item label=" ">
                  <Button
                    type="default"
                    block
                    onClick={() => loadFileTree(form.getFieldValue('projectPath') || '/home')}
                  >
                    Browse Folders
                  </Button>
                </Form.Item>
              </Col>
            </Row>
          )}

          {inputType === 'git' && (
            <>
              <Row gutter={24}>
                <Col span={24}>
                  <Form.Item
                    name="gitUrl"
                    label="Git Repository URL"
                    rules={[
                      { required: true, message: 'Please enter a Git repository URL' },
                      { type: 'url', message: 'Please enter a valid URL' }
                    ]}
                  >
                    <Input
                      placeholder="https://github.com/username/repository.git"
                      prefix={<GitlabOutlined />}
                    />
                  </Form.Item>
                </Col>
              </Row>
              <Row gutter={24}>
                <Col span={24}>
                  <Form.Item
                    name="targetPath"
                    label="Clone To"
                    rules={[{ required: true, message: 'Please specify where to clone' }]}
                    initialValue="/tmp/framework-analysis"
                  >
                    <Input
                      placeholder="/tmp/framework-analysis"
                      prefix={<FolderOpenOutlined />}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </>
          )}

          {/* File Browser */}
          {inputType === 'local' && fileTree.length > 0 && (
            <Card
              title={
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space>
                    <FolderOpenOutlined />
                    File Browser
                  </Space>
                  <Breadcrumb
                    items={currentPath.split('/').filter(p => p).map((part, index, arr) => {
                      const path = '/' + arr.slice(0, index + 1).join('/');
                      return {
                        key: path,
                        title: (
                          <a onClick={() => loadFileTree(path)} style={{ cursor: 'pointer' }}>
                            {part}
                          </a>
                        )
                      };
                    })}
                  />
                </div>
              }
              style={{ marginBottom: 24 }}
              styles={{ body: { maxHeight: 400, overflowY: 'auto' } }}
            >
              <Spin spinning={browsing}>
                {fileTree.map(item => renderFileTreeItem(item))}
              </Spin>
            </Card>
          )}

          {/* Project Statistics Preview */}
          {projectStats && (
            <Card
              title={
                <Space>
                  <InfoCircleOutlined />
                  Project Preview
                </Space>
              }
              style={{ marginBottom: 24 }}
            >
              <Row gutter={16}>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
                      {projectStats.totalFiles}
                    </Title>
                    <Text type="secondary">Total Files</Text>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ margin: 0, color: '#52c41a' }}>
                      {projectStats.pythonFiles}
                    </Title>
                    <Text type="secondary">Python Files</Text>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ margin: 0, color: '#faad14' }}>
                      {projectStats.directories}
                    </Title>
                    <Text type="secondary">Directories</Text>
                  </div>
                </Col>
                <Col span={6}>
                  <div style={{ textAlign: 'center' }}>
                    <Title level={3} style={{ margin: 0, color: '#722ed1' }}>
                      ~{projectStats.estimatedTime}s
                    </Title>
                    <Text type="secondary">Est. Time</Text>
                  </div>
                </Col>
              </Row>
            </Card>
          )}

          <Divider />

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'center' }}>
              <Button
                type="primary"
                htmlType="submit"
                size="large"
                loading={loading}
                style={{ minWidth: 120 }}
              >
                {loading ? 'Analyzing...' : 'Continue'}
              </Button>
            </Space>
          </Form.Item>
        </Form>

        {/* Framework Features */}
        <Card title="Framework Capabilities" style={{ marginTop: 24 }}>
          <Row gutter={24}>
            <Col span={8}>
              <div style={{ textAlign: 'center', padding: 16 }}>
                <CodeOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />
                <Title level={4}>Code Analysis</Title>
                <Text type="secondary">
                  Complete AST parsing, dependency analysis, and architecture validation
                </Text>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center', padding: 16 }}>
                <SearchOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 8 }} />
                <Title level={4}>Hallucination Detection</Title>
                <Text type="secondary">
                  Multi-layer validation to catch AI hallucinations and suspicious patterns
                </Text>
              </div>
            </Col>
            <Col span={8}>
              <div style={{ textAlign: 'center', padding: 16 }}>
                <InfoCircleOutlined style={{ fontSize: 32, color: '#faad14', marginBottom: 8 }} />
                <Title level={4}>Risk Assessment</Title>
                <Text type="secondary">
                  5-level risk scoring with confidence metrics and actionable recommendations
                </Text>
              </div>
            </Col>
          </Row>
        </Card>
      </Card>
    </div>
  );
};