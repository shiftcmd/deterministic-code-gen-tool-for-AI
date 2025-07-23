import React, { useState, useCallback } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Space, 
  Typography, 
  Alert, 
  Spin,
  Row,
  Col,
  Divider,
  Tree,
  Statistic,
  message
} from 'antd';
import { 
  FolderOpenOutlined, 
  GithubOutlined, 
  FileTextOutlined,
  FolderOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import { useFileSystem } from '../hooks/useApi.js';
import { formatFileSize, isPythonFile } from '../utils/helpers.js';

const { Title, Text } = Typography;

const ProjectSelector = () => {
  const navigate = useNavigate();
  const { selectProject, loading, error, clearError } = useApp();
  const [form] = Form.useForm();
  const [projectType, setProjectType] = useState('local'); // 'local' or 'git'
  const [projectStats, setProjectStats] = useState(null);
  const [showFileTree, setShowFileTree] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  
  const {
    currentPath,
    files,
    loading: filesLoading,
    error: filesError,
    browsePath,
    navigateUp,
    navigateToPath
  } = useFileSystem('.');

  // Handle project validation and analysis
  const handleProjectSubmit = async (values) => {
    try {
      setAnalyzing(true);
      clearError();
      const { projectPath } = values;
      
      // Validate and analyze project using real backend
      const analysisResult = await selectProject(projectPath, projectType === 'git');
      
      if (analysisResult && analysisResult.valid) {
        // Calculate project stats from real backend data
        const stats = {
          totalFiles: analysisResult.totalFiles || 0,
          pythonFiles: analysisResult.pythonFiles || 0,
          directories: analysisResult.directories || 0,
          totalSize: analysisResult.totalSize || 0
        };
        
        setProjectStats(stats);
        setShowFileTree(true);
        
        // Browse the project directory to show file tree
        if (projectPath) {
          await browsePath(projectPath);
        }
        
        message.success('Project analyzed successfully!');
      } else {
        message.error('Failed to analyze project - no Python files found or invalid path');
      }
      
    } catch (err) {
      console.error('Failed to analyze project:', err);
      message.error(`Analysis failed: ${err.message}`);
    } finally {
      setAnalyzing(false);
    }
  };

  // Handle file tree navigation
  const handleTreeSelect = async (selectedKeys, { node }) => {
    if (node.type === 'directory') {
      try {
        await navigateToPath(node.path);
      } catch (err) {
        message.error(`Failed to navigate to ${node.path}: ${err.message}`);
      }
    }
  };

  // Build tree data for file explorer with real backend data
  const buildTreeData = (fileList) => {
    return fileList.map(file => ({
      key: file.path,
      title: (
        <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span>{file.name}</span>
          {file.type === 'file' && file.is_python && (
            <span style={{ color: '#52c41a', fontSize: '12px' }}>PY</span>
          )}
          {file.size && (
            <span style={{ color: '#999', fontSize: '11px' }}>
              ({formatFileSize(file.size)})
            </span>
          )}
        </span>
      ),
      icon: file.type === 'directory' ? <FolderOutlined /> : <FileTextOutlined />,
      isLeaf: file.type !== 'directory',
      type: file.type,
      path: file.path,
      size: file.size
    }));
  };

  // Continue to file confirmation with real project data
  const handleContinue = () => {
    if (projectStats && projectStats.pythonFiles > 0) {
      navigate('/confirm');
    } else {
      message.warning('No Python files found in this project to analyze');
    }
  };

  return (
    <div>
      <div style={{ marginBottom: 32 }}>
        <Title level={2} style={{ marginBottom: 8 }}>
          Project Selection
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Select a Python project directory or Git repository to analyze
        </Text>
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

      <Row gutter={[32, 32]}>
        <Col xs={24} lg={12}>
          <Card 
            title={
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <FolderOpenOutlined />
                <span>Project Source</span>
              </div>
            } 
            variant="outlined"
            style={{ height: '100%' }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              <Space.Compact style={{ width: '100%' }}>
                <Button 
                  type={projectType === 'local' ? 'primary' : 'default'}
                  icon={<FolderOpenOutlined />}
                  onClick={() => setProjectType('local')}
                  style={{ width: '50%', height: 48 }}
                  size="large"
                >
                  Local Folder
                </Button>
                <Button 
                  type={projectType === 'git' ? 'primary' : 'default'}
                  icon={<GithubOutlined />}
                  onClick={() => setProjectType('git')}
                  style={{ width: '50%', height: 48 }}
                  size="large"
                >
                  Git Repository
                </Button>
              </Space.Compact>

              <Form
                form={form}
                layout="vertical"
                onFinish={handleProjectSubmit}
              >
                <Form.Item
                  name="projectPath"
                  label={
                    <Text strong>
                      {projectType === 'local' ? 'Project Directory Path' : 'Git Repository URL'}
                    </Text>
                  }
                  rules={[
                    { required: true, message: 'Please enter a project path or URL' },
                    {
                      validator: (_, value) => {
                        if (projectType === 'git' && value && !value.includes('git')) {
                          return Promise.reject('Please enter a valid Git repository URL');
                        }
                        return Promise.resolve();
                      }
                    }
                  ]}
                >
                  <Input
                    placeholder={
                      projectType === 'local' 
                        ? '/path/to/your/python/project or .'
                        : 'https://github.com/user/repo.git'
                    }
                    size="large"
                    style={{ fontSize: 14 }}
                  />
                </Form.Item>

                <Form.Item>
                  <Button 
                    type="primary" 
                    htmlType="submit" 
                    loading={analyzing || loading}
                    size="large"
                    style={{ width: '100%', height: 48 }}
                  >
                    {analyzing ? 'Analyzing Project...' : 'Analyze Project Structure'}
                  </Button>
                </Form.Item>
              </Form>
            </Space>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          {projectStats ? (
            <Card 
              title={
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <FileTextOutlined />
                  <span>Project Statistics</span>
                </div>
              } 
              bordered={false}
              style={{ height: '100%' }}
            >
              <Row gutter={[16, 24]}>
                <Col span={12}>
                  <Statistic
                    title="Total Files"
                    value={projectStats.totalFiles}
                    prefix={<FileTextOutlined />}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Python Files"
                    value={projectStats.pythonFiles}
                    valueStyle={{ color: '#52c41a' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Directories"
                    value={projectStats.directories}
                    prefix={<FolderOutlined />}
                    valueStyle={{ color: '#722ed1' }}
                  />
                </Col>
                <Col span={12}>
                  <Statistic
                    title="Total Size"
                    value={formatFileSize(projectStats.totalSize)}
                    valueStyle={{ color: '#fa8c16' }}
                  />
                </Col>
              </Row>

              <Divider />

              <Button 
                type="primary" 
                onClick={handleContinue}
                style={{ width: '100%', height: 48 }}
                size="large"
                disabled={!projectStats.pythonFiles}
                icon={<FolderOpenOutlined />}
              >
                Continue to File Selection
              </Button>

              {!projectStats.pythonFiles && (
                <Alert
                  message="No Python files found"
                  description="This directory doesn't contain any Python files to analyze."
                  type="warning"
                  style={{ marginTop: 16 }}
                />
              )}
            </Card>
          ) : (
            <Card 
              style={{ 
                height: '100%', 
                display: 'flex', 
                alignItems: 'center', 
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)'
              }}
              styles={{ 
                body: {
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '300px'
                }
              }}
            >
              <div style={{ textAlign: 'center', color: '#999' }}>
                <FolderOpenOutlined style={{ fontSize: 48, marginBottom: 16 }} />
                <Text type="secondary" style={{ fontSize: 16 }}>
                  Project statistics will appear here after analysis
                </Text>
              </div>
            </Card>
          )}
        </Col>
      </Row>

      {showFileTree && (
        <Card 
          title={
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <FolderOutlined />
              <span>Project Structure Preview</span>
              <Text type="secondary" style={{ marginLeft: 8 }}>
                {currentPath}
              </Text>
            </div>
          }
          style={{ marginTop: 32 }}
          extra={
            <Space>
              <Button onClick={navigateUp} disabled={!currentPath || currentPath === '/'}>
                ↑ Up Directory
              </Button>
              <Text type="secondary">{files.length} items</Text>
            </Space>
          }
        >
          <Spin spinning={filesLoading}>
            {filesError ? (
              <Alert
                message="Failed to load project structure"
                description={filesError}
                type="error"
                style={{ margin: '24px 0' }}
              />
            ) : (
              <Tree
                showIcon
                treeData={buildTreeData(files)}
                onSelect={handleTreeSelect}
                height={400}
                style={{ 
                  border: '1px solid #d9d9d9',
                  borderRadius: 8,
                  padding: 16,
                  background: '#fafafa'
                }}
              />
            )}
          </Spin>
        </Card>
      )}
    </div>
  );
};

export default ProjectSelector; 