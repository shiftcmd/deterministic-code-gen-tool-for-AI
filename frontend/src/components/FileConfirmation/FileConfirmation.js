import React, { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Button,
  Tree,
  Typography,
  Space,
  Row,
  Col,
  Divider,
  Input,
  Select,
  Tag,
  Alert,
  Statistic
} from 'antd';
import {
  FolderOutlined,
  FileOutlined,
  SearchOutlined,
  PlayCircleOutlined,
  CheckCircleOutlined,
  SelectOutlined,
  ClearOutlined
} from '@ant-design/icons';
import { useFramework } from '../../context/FrameworkContext';
import { useErrorLogger } from '../../services/errorLogger';

const { Title, Text } = Typography;
const { Search } = Input;
const { Option } = Select;

// Helper function to build Ant Design compatible tree structure
const buildFileTree = (files) => {
  const tree = {};
  
  files.forEach(file => {
    const parts = file.path.split('/').filter(part => part);
    let current = tree;
    
    parts.forEach((part, index) => {
      const isFile = index === parts.length - 1;
      const key = parts.slice(0, index + 1).join('/');
      
      if (!current[part]) {
        const isPython = isFile && (file.path.endsWith('.py') || file.path.endsWith('.pyi'));
        
        current[part] = {
          key,
          title: (
            <Space>
              {isFile ? (
                <FileOutlined style={{ color: isPython ? '#52c41a' : '#d9d9d9' }} />
              ) : (
                <FolderOutlined style={{ color: '#1890ff' }} />
              )}
              <Text style={{ color: isPython ? '#000' : '#999' }}>
                {part}
              </Text>
              {isPython && <Tag color="green" size="small">Python</Tag>}
            </Space>
          ),
          isLeaf: isFile,
          children: isFile ? undefined : {},
          fileData: isFile ? file : undefined,
          type: isFile ? 'file' : 'directory'
        };
      }
      
      if (!isFile) {
        current = current[part].children;
      }
    });
  });
  
  // Convert to array format for Ant Design Tree
  const convertToArray = (obj) => {
    return Object.values(obj).map(node => ({
      ...node,
      children: node.children ? convertToArray(node.children) : undefined
    }));
  };
  
  return convertToArray(tree);
};

// Helper function to filter tree based on search term
const filterTree = (tree, searchTerm) => {
  if (!searchTerm) return tree;
  
  const filterNode = (node) => {
    const titleText = typeof node.title === 'string' ? node.title : node.key.split('/').pop();
    const matches = titleText.toLowerCase().includes(searchTerm.toLowerCase());
    
    if (node.children) {
      const filteredChildren = node.children.map(filterNode).filter(Boolean);
      if (matches || filteredChildren.length > 0) {
        return {
          ...node,
          children: filteredChildren.length > 0 ? filteredChildren : undefined
        };
      }
    } else if (matches) {
      return node;
    }
    
    return null;
  };
  
  return tree.map(filterNode).filter(Boolean);
};

export const FileConfirmation = () => {
  const navigate = useNavigate();
  const { currentProject, updateSelectedFiles, startProcessing, loading } = useFramework();
  const { logError, logUserAction } = useErrorLogger();
  
  const [checkedKeys, setCheckedKeys] = useState([]);
  const [expandedKeys, setExpandedKeys] = useState([]);
  const [searchValue, setSearchValue] = useState('');
  const [filterType, setFilterType] = useState('all');
  
  // Build tree data with memoization
  const treeData = useMemo(() => {
    if (!currentProject?.files) return [];
    return buildFileTree(currentProject.files);
  }, [currentProject?.files]);
  
  // Filter tree based on search and filter type
  const filteredTreeData = useMemo(() => {
    let filtered = filterTree(treeData, searchValue);
    
    if (filterType === 'python') {
      const filterPythonFiles = (nodes) => {
        return nodes.filter(node => {
          if (node.type === 'file') {
            return node.fileData?.path.endsWith('.py') || node.fileData?.path.endsWith('.pyi');
          } else {
            // Keep directories that have Python files in them
            const hasChildren = node.children && filterPythonFiles(node.children).length > 0;
            return hasChildren;
          }
        }).map(node => ({
          ...node,
          children: node.children ? filterPythonFiles(node.children) : undefined
        }));
      };
      filtered = filterPythonFiles(filtered);
    }
    
    return filtered;
  }, [treeData, searchValue, filterType]);
  
  // Calculate statistics
  const stats = useMemo(() => {
    const allFiles = currentProject?.files || [];
    const pythonFiles = allFiles.filter(file => 
      file.path.endsWith('.py') || file.path.endsWith('.pyi')
    );
    
    return {
      totalFiles: allFiles.length,
      pythonFiles: pythonFiles.length,
      selectedFiles: checkedKeys.length,
      selectedPythonFiles: checkedKeys.filter(key => 
        key.endsWith('.py') || key.endsWith('.pyi')
      ).length
    };
  }, [currentProject?.files, checkedKeys]);
  
  // Initialize component
  useEffect(() => {
    if (!currentProject) {
      navigate('/');
      return;
    }
    
    // Auto-select Python files
    const pythonFiles = (currentProject.files || [])
      .filter(file => file.path.endsWith('.py') || file.path.endsWith('.pyi'))
      .map(file => file.path);
    
    setCheckedKeys(pythonFiles);
    updateSelectedFiles(pythonFiles);
    
    // Expand first level directories
    const firstLevelKeys = treeData
      .filter(node => !node.isLeaf)
      .map(node => node.key);
    setExpandedKeys(firstLevelKeys);
  }, [currentProject, navigate, updateSelectedFiles, treeData]);

  // Event handlers
  const handleCheck = (checkedKeysValue) => {
    const actualCheckedKeys = Array.isArray(checkedKeysValue) 
      ? checkedKeysValue 
      : checkedKeysValue.checked || [];
    
    setCheckedKeys(actualCheckedKeys);
    updateSelectedFiles(actualCheckedKeys);
  };

  const handleExpand = (expandedKeysValue) => {
    setExpandedKeys(expandedKeysValue);
  };

  const handleSearch = (value) => {
    setSearchValue(value);
  };

  const handleFilterChange = (value) => {
    setFilterType(value);
  };

  const handleSelectAll = () => {
    const allFileKeys = currentProject.files?.map(file => file.path) || [];
    setCheckedKeys(allFileKeys);
    updateSelectedFiles(allFileKeys);
  };

  const handleSelectPython = () => {
    const pythonFiles = (currentProject.files || [])
      .filter(file => file.path.endsWith('.py') || file.path.endsWith('.pyi'))
      .map(file => file.path);
    setCheckedKeys(pythonFiles);
    updateSelectedFiles(pythonFiles);
  };

  const handleClearAll = () => {
    setCheckedKeys([]);
    updateSelectedFiles([]);
  };

  const handleStartProcessing = async () => {
    try {
      await logUserAction('START_PROCESSING_ATTEMPT', {
        selectedFilesCount: checkedKeys.length,
        projectPath: currentProject?.path,
        selectedFiles: checkedKeys.slice(0, 10) // Log first 10 files for context
      });

      if (checkedKeys.length === 0) {
        Alert.error({
          message: 'No Files Selected',
          description: 'Please select at least one file to process.',
        });
        return;
      }

      startProcessing();
      navigate('/processing');
    } catch (error) {
      console.error('Failed to start processing:', error);
      await logError(error, 'START_PROCESSING_ERROR', {
        selectedFilesCount: checkedKeys.length,
        projectPath: currentProject?.path
      });
    }
  };

  if (!currentProject) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Alert
          message="No Project Selected"
          description="Please go back and select a project to continue."
          type="warning"
          showIcon
          action={
            <Button type="primary" onClick={() => navigate('/')}>
              Select Project
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 1200, margin: '0 auto' }}>
      <Card>
        <Title level={2} style={{ marginBottom: 24 }}>
          <CheckCircleOutlined style={{ color: '#52c41a', marginRight: 8 }} />
          Confirm Files for Processing
        </Title>
        
        <Text type="secondary" style={{ display: 'block', marginBottom: 24 }}>
          Project: <Text strong>{currentProject.name}</Text> ({currentProject.path})
        </Text>

        {/* Statistics Row */}
        <Row gutter={16} style={{ marginBottom: 24 }}>
          <Col span={6}>
            <Statistic title="Total Files" value={stats.totalFiles} />
          </Col>
          <Col span={6}>
            <Statistic title="Python Files" value={stats.pythonFiles} />
          </Col>
          <Col span={6}>
            <Statistic title="Selected Files" value={stats.selectedFiles} />
          </Col>
          <Col span={6}>
            <Statistic 
              title="Selected Python Files" 
              value={stats.selectedPythonFiles}
              valueStyle={{ color: '#52c41a' }}
            />
          </Col>
        </Row>

        <Divider />

        {/* Search and Filter Controls */}
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={12}>
            <Search
              placeholder="Search files..."
              prefix={<SearchOutlined />}
              value={searchValue}
              onChange={(e) => handleSearch(e.target.value)}
              allowClear
            />
          </Col>
          <Col span={6}>
            <Select
              style={{ width: '100%' }}
              value={filterType}
              onChange={handleFilterChange}
              placeholder="Filter by type"
            >
              <Option value="all">All Files</Option>
              <Option value="python">Python Files Only</Option>
            </Select>
          </Col>
          <Col span={6}>
            <Space>
              <Button
                type="default"
                icon={<SelectOutlined />}
                onClick={handleSelectAll}
                size="small"
              >
                All
              </Button>
              <Button
                type="default"
                icon={<FileOutlined />}
                onClick={handleSelectPython}
                size="small"
              >
                Python
              </Button>
              <Button
                type="default"
                icon={<ClearOutlined />}
                onClick={handleClearAll}
                size="small"
              >
                Clear
              </Button>
            </Space>
          </Col>
        </Row>

        {/* File Tree */}
        <Card 
          size="small" 
          style={{ marginBottom: 24, maxHeight: 500, overflow: 'auto' }}
        >
          <Tree
            checkable
            onExpand={handleExpand}
            expandedKeys={expandedKeys}
            onCheck={handleCheck}
            checkedKeys={checkedKeys}
            treeData={filteredTreeData}
            height={400}
            virtual
          />
        </Card>

        {/* Action Buttons */}
        <Row justify="space-between" align="middle">
          <Col>
            <Button onClick={() => navigate('/')}>
              Back to Project Selection
            </Button>
          </Col>
          <Col>
            <Space>
              <Text type="secondary">
                {stats.selectedFiles} files selected
              </Text>
              <Button
                type="primary"
                size="large"
                icon={<PlayCircleOutlined />}
                onClick={handleStartProcessing}
                loading={loading}
                disabled={stats.selectedFiles === 0}
              >
                Start Processing
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>
    </div>
  );
};
