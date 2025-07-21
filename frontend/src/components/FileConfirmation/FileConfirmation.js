import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Tree,
  Space,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Checkbox,
  Input,
  Select,
  Divider,
  Tag,
  Progress,
  Tooltip,
  notification
} from 'antd';
import {
  FileOutlined,
  FolderOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  FilterOutlined,
  SelectOutlined,
  ClearOutlined,
  PlayCircleOutlined,
  ArrowLeftOutlined
} from '@ant-design/icons';
import { useFramework } from '../../context/FrameworkContext';
import { useErrorLogger } from '../../services/errorLogger';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

export const FileConfirmation = () => {
  const navigate = useNavigate();
  const { currentProject, selectedFiles, updateSelectedFiles, startProcessing, loading } = useFramework();
  const { logError, logUserAction } = useErrorLogger();
  
  const [treeData, setTreeData] = useState([]);
  const [checkedKeys, setCheckedKeys] = useState([]);
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [searchValue, setSearchValue] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [autoExpandParent, setAutoExpandParent] = useState(true);

  useEffect(() => {
    if (!currentProject) {
      navigate('/');
      return;
    }
    
    const tree = buildTreeData(currentProject.files || []);
    setTreeData(tree);
    
    // Initially select all Python files
    const pythonFiles = (currentProject.files || [])
      .filter(file => file.path.endsWith('.py') || file.path.endsWith('.pyi'))
      .map(file => file.path);
    
    setCheckedKeys(pythonFiles);
    updateSelectedFiles(pythonFiles);
    
    // Auto-expand first level
    const firstLevel = tree.map(item => item.key);
    setExpandedKeys(firstLevel);
  }, [currentProject, navigate, updateSelectedFiles]);

  const buildTreeData = (files) => {
    const tree = {};
    
    files.forEach(file => {
      const parts = file.path.split('/').filter(part => part);
      let current = tree;
      
      parts.forEach((part, index) => {
        const isLast = index === parts.length - 1;
        const key = parts.slice(0, index + 1).join('/');
        
        if (!current[part]) {
          current[part] = {
            key,
            title: part,
            isLeaf: isLast,
            children: isLast ? undefined : {},
            file: isLast ? file : undefined,
            type: isLast ? 'file' : 'directory'
          };
        }
        
        current = current[part].children || {};
      });
    });
    
    return convertToAntdTree(tree);
  };

  const convertToAntdTree = (tree) => {
    return Object.values(tree).map(node => ({
      ...node,
      title: renderTreeNode(node),
      children: node.children ? convertToAntdTree(node.children) : undefined
    }));
  };

  const renderTreeNode = (node) => {
    const { title, type, file } = node;
    const isPython = file?.path.endsWith('.py') || file?.path.endsWith('.pyi');
    const isSelected = checkedKeys.includes(node.key);
    
    return (
      <Space>
        {type === 'directory' ? (
          <FolderOutlined style={{ color: '#1890ff' }} />
        ) : (
          <FileOutlined style={{ color: isPython ? '#52c41a' : '#d9d9d9' }} />
        )}
        <Text style={{ 
          color: isPython ? '#000' : '#999',
          fontWeight: isSelected ? 'bold' : 'normal'
        }}>
          {title}
        </Text>
        {file && (
          <Space size={4}>
            {isPython && <Tag color="green" size="small">Python</Tag>}
            {file.size && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {formatFileSize(file.size)}
              </Text>
            )}
          </Space>
        )}
      </Space>
    );
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const onCheck = (checkedKeysValue, info) => {
    console.log('Tree onCheck called:', { checkedKeysValue, info });
    
    // When using checkStrictly, checkedKeysValue is an object with 'checked' and 'halfChecked'
    let actualCheckedKeys;
    if (typeof checkedKeysValue === 'object' && checkedKeysValue.checked) {
      actualCheckedKeys = checkedKeysValue.checked;
    } else {
      actualCheckedKeys = checkedKeysValue;
    }
    
    setCheckedKeys(actualCheckedKeys);
    updateSelectedFiles(actualCheckedKeys);
  };

  const onExpand = (expandedKeysValue) => {
    setExpandedKeys(expandedKeysValue);
    setAutoExpandParent(false);
  };

  const handleSelectAll = () => {
    const allPythonFiles = (currentProject.files || [])
      .filter(file => file.path.endsWith('.py') || file.path.endsWith('.pyi'))
      .map(file => file.path);
    
    setCheckedKeys(allPythonFiles);
    updateSelectedFiles(allPythonFiles);
  };

  const handleSelectNone = () => {
    setCheckedKeys([]);
    updateSelectedFiles([]);
  };

  const handleFilterChange = (value) => {
    setFilterType(value);
    // Apply filter logic here if needed
  };

  const handleSearch = (value) => {
    setSearchValue(value);
    // Implement search functionality
  };

  const handleStartProcessing = async () => {
    try {
      await logUserAction('START_PROCESSING_ATTEMPT', {
        selectedFilesCount: checkedKeys.length,
        projectPath: currentProject?.path,
        selectedFiles: checkedKeys.slice(0, 10) // Log first 10 files for context
      });

      // Show progress notification
      notification.info({
        message: 'Analysis Started',
        description: `Analyzing ${stats.selectedPythonFiles} Python files. You'll be redirected to the processing view.`,
        duration: 3
      });

      const run = await startProcessing();
      
      await logUserAction('START_PROCESSING_SUCCESS', {
        runId: run.id,
        selectedFilesCount: checkedKeys.length
      });

      navigate(`/processing?runId=${run.id}`);
    } catch (error) {
      await logError(error, {
        component: 'FileConfirmation',
        action: 'handleStartProcessing',
        selectedFilesCount: checkedKeys.length,
        projectPath: currentProject?.path
      });
      
      console.error('Failed to start processing:', error);
      
      // Show user-friendly error message
      notification.error({
        message: 'Analysis Failed to Start',
        description: 'There was an error starting the analysis. Please check your configuration and try again.',
        duration: 5
      });
    }
  };

  const getStats = () => {
    const selectedPythonFiles = checkedKeys.filter(key => 
      key.endsWith('.py') || key.endsWith('.pyi')
    );
    
    const totalFiles = currentProject?.files?.length || 0;
    const totalPythonFiles = (currentProject?.files || [])
      .filter(file => file.path.endsWith('.py') || file.path.endsWith('.pyi')).length;
    
    const estimatedTime = Math.ceil(selectedPythonFiles.length * 0.1);
    const estimatedComplexity = selectedPythonFiles.length > 50 ? 'High' : 
                              selectedPythonFiles.length > 20 ? 'Medium' : 'Low';

    return {
      totalFiles,
      totalPythonFiles,
      selectedFiles: checkedKeys.length,
      selectedPythonFiles: selectedPythonFiles.length,
      estimatedTime,
      estimatedComplexity
    };
  };

  const stats = getStats();

  if (!currentProject) {
    return null;
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
            <Title level={3} style={{ margin: 0 }}>
              Confirm Files for Analysis
            </Title>
          </Space>
          <Text type="secondary" style={{ display: 'block', marginTop: 8 }}>
            Project: {currentProject.path}
          </Text>
        </div>

        <Row gutter={24}>
          {/* Left Panel - File Tree */}
          <Col span={16}>
            <Card 
              title={
                <Space>
                  <FileOutlined />
                  File Selection
                  <Tag color="blue">{stats.selectedFiles} selected</Tag>
                </Space>
              }
              extra={
                <Space>
                  <Search
                    placeholder="Search files..."
                    value={searchValue}
                    onChange={(e) => handleSearch(e.target.value)}
                    style={{ width: 200 }}
                    allowClear
                  />
                  <Select
                    value={filterType}
                    onChange={handleFilterChange}
                    style={{ width: 120 }}
                  >
                    <Option value="all">All Files</Option>
                    <Option value="python">Python Only</Option>
                    <Option value="large">Large Files</Option>
                  </Select>
                </Space>
              }
            >
              <div style={{ marginBottom: 16 }}>
                <Space>
                  <Button 
                    size="small" 
                    icon={<SelectOutlined />}
                    onClick={handleSelectAll}
                  >
                    Select All Python
                  </Button>
                  <Button 
                    size="small" 
                    icon={<ClearOutlined />}
                    onClick={handleSelectNone}
                  >
                    Clear All
                  </Button>
                  <Divider type="vertical" />
                  <Text type="secondary">
                    {stats.selectedPythonFiles} Python files selected for analysis
                  </Text>
                </Space>
              </div>
              
              <div style={{ 
                maxHeight: 600, 
                overflowY: 'auto',
                border: '1px solid #f0f0f0',
                borderRadius: 6,
                padding: 12
              }}>
                <Tree
                  checkable
                  checkStrictly
                  checkedKeys={{ checked: checkedKeys, halfChecked: [] }}
                  expandedKeys={expandedKeys}
                  autoExpandParent={autoExpandParent}
                  treeData={treeData}
                  onCheck={onCheck}
                  onExpand={onExpand}
                  height={600}
                />
              </div>
            </Card>
          </Col>

          {/* Right Panel - Statistics and Actions */}
          <Col span={8}>
            <Space direction="vertical" style={{ width: '100%' }} size={16}>
              
              {/* Statistics */}
              <Card title="Analysis Overview">
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Total Files"
                      value={stats.totalFiles}
                      prefix={<FileOutlined />}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Python Files"
                      value={stats.totalPythonFiles}
                      prefix={<FileOutlined style={{ color: '#52c41a' }} />}
                    />
                  </Col>
                </Row>
                <Divider />
                <Row gutter={16}>
                  <Col span={12}>
                    <Statistic
                      title="Selected"
                      value={stats.selectedPythonFiles}
                      prefix={<CheckCircleOutlined style={{ color: '#1890ff' }} />}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Est. Time"
                      value={stats.estimatedTime}
                      suffix="sec"
                      prefix={<ExclamationCircleOutlined />}
                    />
                  </Col>
                </Row>
              </Card>

              {/* Processing Configuration */}
              <Card title="Analysis Settings">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text strong>Complexity Level: </Text>
                    <Tag color={
                      stats.estimatedComplexity === 'High' ? 'red' :
                      stats.estimatedComplexity === 'Medium' ? 'orange' : 'green'
                    }>
                      {stats.estimatedComplexity}
                    </Tag>
                  </div>
                  
                  <div>
                    <Checkbox defaultChecked>
                      Enable hallucination detection
                    </Checkbox>
                  </div>
                  
                  <div>
                    <Checkbox defaultChecked>
                      Generate architectural insights
                    </Checkbox>
                  </div>
                  
                  <div>
                    <Checkbox defaultChecked>
                      Export to Neo4j knowledge graph
                    </Checkbox>
                  </div>
                </Space>
              </Card>

              {/* Progress Estimate */}
              <Card title="Expected Analysis Phases">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <Text>File Discovery & Parsing</Text>
                    <Progress percent={0} size="small" />
                  </div>
                  <div>
                    <Text>AST Analysis & Validation</Text>
                    <Progress percent={0} size="small" />
                  </div>
                  <div>
                    <Text>Risk Assessment</Text>
                    <Progress percent={0} size="small" />
                  </div>
                  <div>
                    <Text>Knowledge Graph Export</Text>
                    <Progress percent={0} size="small" />
                  </div>
                  <div>
                    <Text>Dashboard Generation</Text>
                    <Progress percent={0} size="small" />
                  </div>
                </Space>
              </Card>

              {/* Action Buttons */}
              <Card>
                <Space direction="vertical" style={{ width: '100%' }}>
                  {stats.selectedPythonFiles === 0 && (
                    <Alert
                      message="No Python files selected"
                      description="Please select at least one Python file to analyze."
                      type="warning"
                      showIcon
                    />
                  )}
                  
                  <Button
                    type="primary"
                    size="large"
                    block
                    icon={<PlayCircleOutlined />}
                    loading={loading}
                    disabled={stats.selectedPythonFiles === 0}
                    onClick={handleStartProcessing}
                  >
                    {loading ? 'Analyzing...' : 'Analyze'}
                  </Button>
                  
                  <Text type="secondary" style={{ textAlign: 'center', display: 'block' }}>
                    This will analyze {stats.selectedPythonFiles} Python files
                  </Text>
                </Space>
              </Card>
            </Space>
          </Col>
        </Row>
      </Card>
    </div>
  );
};