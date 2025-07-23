import React, { useState, useEffect, useMemo } from 'react';
import { 
  Card, 
  Tree, 
  Button, 
  Space, 
  Typography, 
  Alert, 
  Input,
  Select,
  Checkbox,
  Row,
  Col,
  Divider,
  Tag,
  Progress
} from 'antd';
import { 
  SearchOutlined,
  PlayCircleOutlined,
  CheckOutlined,
  ClearOutlined,
  FileTextOutlined,
  FolderOutlined,
  PythonOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext.jsx';
import { isPythonFile, formatFileSize, debounce } from '../utils/helpers.js';

const { Title, Text } = Typography;
const { Search } = Input;

const FileConfirmation = () => {
  const navigate = useNavigate();
  const { 
    currentProject, 
    selectedFiles, 
    updateSelectedFiles, 
    startProcessing,
    loading,
    error 
  } = useApp();

  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all'); // 'all', 'python', 'directories'
  const [checkedKeys, setCheckedKeys] = useState([]);
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [autoExpandParent, setAutoExpandParent] = useState(true);
  const [treeData, setTreeData] = useState([]);
  const [analysisConfig, setAnalysisConfig] = useState({
    includeRelationships: true,
    exportToNeo4j: false,
    cacheResults: true,
    configPreset: 'standard'
  });

  // Build file tree from project data
  useEffect(() => {
    if (currentProject && currentProject.files) {
      const tree = buildFileTree(currentProject.files);
      setTreeData(tree);
      
      // Auto-expand first level
      const firstLevelKeys = tree.map(node => node.key);
      setExpandedKeys(firstLevelKeys);
    }
  }, [currentProject]);

  // Build hierarchical tree structure
  const buildFileTree = (files) => {
    const tree = {};
    
    files.forEach(file => {
      const parts = file.path.split('/').filter(Boolean);
      let current = tree;
      
      parts.forEach((part, index) => {
        if (!current[part]) {
          const isFile = index === parts.length - 1;
          current[part] = {
            key: parts.slice(0, index + 1).join('/'),
            title: part,
            isLeaf: isFile,
            type: isFile ? 'file' : 'directory',
            path: file.path,
            size: file.size,
            isPython: isFile ? isPythonFile(part) : false,
            children: isFile ? undefined : {}
          };
        }
        current = current[part].children || {};
      });
    });

    return convertToTreeArray(tree);
  };

  // Convert tree object to array format for Ant Design Tree
  const convertToTreeArray = (treeObj) => {
    return Object.values(treeObj).map(node => ({
      ...node,
      children: node.children ? convertToTreeArray(node.children) : undefined,
      icon: node.type === 'directory' ? 
        <FolderOutlined /> : 
        node.isPython ? <PythonOutlined /> : <FileTextOutlined />
    }));
  };

  // Filter tree based on search and filter type
  const filteredTreeData = useMemo(() => {
    if (!searchTerm && filterType === 'all') return treeData;
    
    const filterNode = (nodes) => {
      return nodes.map(node => {
        const matchesSearch = !searchTerm || 
          node.title.toLowerCase().includes(searchTerm.toLowerCase());
        
        const matchesFilter = 
          filterType === 'all' ||
          (filterType === 'python' && node.isPython) ||
          (filterType === 'directories' && node.type === 'directory');

        const filteredChildren = node.children ? filterNode(node.children) : [];
        const hasMatchingChildren = filteredChildren.length > 0;

        if ((matchesSearch && matchesFilter) || hasMatchingChildren) {
          return {
            ...node,
            children: filteredChildren.length > 0 ? filteredChildren : node.children
          };
        }
        return null;
      }).filter(Boolean);
    };

    return filterNode(treeData);
  }, [treeData, searchTerm, filterType]);

  // Handle tree node selection
  const handleCheck = (checkedKeysValue) => {
    setCheckedKeys(checkedKeysValue);
    updateSelectedFiles(checkedKeysValue);
  };

  // Handle tree expansion
  const handleExpand = (expandedKeysValue) => {
    setExpandedKeys(expandedKeysValue);
    setAutoExpandParent(false);
  };

  // Debounced search handler
  const debouncedSearch = useMemo(
    () => debounce((value) => setSearchTerm(value), 300),
    []
  );

  // Select all Python files
  const handleSelectPython = () => {
    const getAllPythonKeys = (nodes) => {
      let keys = [];
      nodes.forEach(node => {
        if (node.isPython) {
          keys.push(node.key);
        }
        if (node.children) {
          keys = keys.concat(getAllPythonKeys(node.children));
        }
      });
      return keys;
    };
    
    const pythonKeys = getAllPythonKeys(treeData);
    setCheckedKeys(pythonKeys);
    updateSelectedFiles(pythonKeys);
  };

  // Clear all selections
  const handleClearAll = () => {
    setCheckedKeys([]);
    updateSelectedFiles([]);
  };

  // Start processing with selected files
  const handleStartProcessing = async () => {
    try {
      const runData = await startProcessing({
        files: selectedFiles,
        ...analysisConfig
      });
      
      navigate(`/processing?runId=${runData.id}`);
    } catch (err) {
      console.error('Failed to start processing:', err);
    }
  };

  const selectedCount = checkedKeys.length;
  const pythonCount = checkedKeys.filter(key => {
    // Find node and check if it's Python
    const findNode = (nodes, targetKey) => {
      for (const node of nodes) {
        if (node.key === targetKey) return node;
        if (node.children) {
          const found = findNode(node.children, targetKey);
          if (found) return found;
        }
      }
      return null;
    };
    
    const node = findNode(treeData, key);
    return node?.isPython;
  }).length;

  if (!currentProject) {
    return (
      <Alert
        message="No project selected"
        description="Please select a project first"
        type="warning"
        action={
          <Button type="primary" onClick={() => navigate('/')}>
            Select Project
          </Button>
        }
      />
    );
  }

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>File Confirmation</Title>
      <Text type="secondary">
        Select Python files to include in the analysis
      </Text>

      {error && (
        <Alert
          message="Error"
          description={error}
          type="error"
          closable
          style={{ marginTop: 16 }}
        />
      )}

      <Row gutter={[24, 24]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="File Selection" bordered={false}>
            <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
              <Row gutter={16}>
                <Col flex="auto">
                  <Search
                    placeholder="Search files..."
                    allowClear
                    onChange={(e) => debouncedSearch(e.target.value)}
                    prefix={<SearchOutlined />}
                  />
                </Col>
                <Col>
                  <Select
                    value={filterType}
                    onChange={setFilterType}
                    style={{ width: 120 }}
                  >
                    <Select.Option value="all">All Files</Select.Option>
                    <Select.Option value="python">Python Only</Select.Option>
                    <Select.Option value="directories">Directories</Select.Option>
                  </Select>
                </Col>
              </Row>

              <Space>
                <Button 
                  icon={<PythonOutlined />} 
                  onClick={handleSelectPython}
                >
                  Select All Python
                </Button>
                <Button 
                  icon={<ClearOutlined />} 
                  onClick={handleClearAll}
                >
                  Clear All
                </Button>
                <Tag color="blue">{selectedCount} files selected</Tag>
                <Tag color="green">{pythonCount} Python files</Tag>
              </Space>
            </Space>

            <Tree
              checkable
              onExpand={handleExpand}
              expandedKeys={expandedKeys}
              autoExpandParent={autoExpandParent}
              onCheck={handleCheck}
              checkedKeys={checkedKeys}
              treeData={filteredTreeData}
              showIcon
              height={500}
              style={{ 
                border: '1px solid #d9d9d9',
                borderRadius: 4,
                padding: 8
              }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="Analysis Configuration" bordered={false}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Configuration Preset</Text>
                <Select
                  value={analysisConfig.configPreset}
                  onChange={(value) => setAnalysisConfig(prev => ({ ...prev, configPreset: value }))}
                  style={{ width: '100%', marginTop: 8 }}
                >
                  <Select.Option value="basic">Basic Analysis</Select.Option>
                  <Select.Option value="standard">Standard Analysis</Select.Option>
                  <Select.Option value="deep">Deep Analysis</Select.Option>
                </Select>
              </div>

              <Checkbox
                checked={analysisConfig.includeRelationships}
                onChange={(e) => setAnalysisConfig(prev => ({ 
                  ...prev, 
                  includeRelationships: e.target.checked 
                }))}
              >
                Include Relationships
              </Checkbox>

              <Checkbox
                checked={analysisConfig.exportToNeo4j}
                onChange={(e) => setAnalysisConfig(prev => ({ 
                  ...prev, 
                  exportToNeo4j: e.target.checked 
                }))}
              >
                Export to Neo4j
              </Checkbox>

              <Checkbox
                checked={analysisConfig.cacheResults}
                onChange={(e) => setAnalysisConfig(prev => ({ 
                  ...prev, 
                  cacheResults: e.target.checked 
                }))}
              >
                Cache Results
              </Checkbox>

              <Divider />

              <div>
                <Text strong>Selection Summary</Text>
                <div style={{ marginTop: 8 }}>
                  <div>Total Files: {selectedCount}</div>
                  <div>Python Files: {pythonCount}</div>
                  <div>Progress: </div>
                  <Progress 
                    percent={pythonCount > 0 ? Math.round((pythonCount / selectedCount) * 100) : 0} 
                    size="small"
                    status={pythonCount > 0 ? 'active' : 'normal'}
                  />
                </div>
              </div>

              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={handleStartProcessing}
                loading={loading}
                disabled={pythonCount === 0}
                style={{ width: '100%', marginTop: 16 }}
                size="large"
              >
                Start Analysis
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default FileConfirmation; 