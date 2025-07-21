import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu } from 'antd';
import {
  DashboardOutlined,
  FileSearchOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  PlayCircleOutlined,
  SettingOutlined,
  BugOutlined
} from '@ant-design/icons';
import { useTheme } from '../../context/ThemeContext';

const { Sider } = Layout;

export const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isDarkMode } = useTheme();

  const menuItems = [
    {
      key: '/',
      icon: <PlayCircleOutlined />,
      label: 'New Analysis',
      role: 'menuitem',
      tabIndex: 0
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: 'History',
      role: 'menuitem',
      tabIndex: 0
    },
    {
      type: 'divider'
    },
    {
      key: 'analysis',
      icon: <FileSearchOutlined />,
      label: 'Current Analysis',
      role: 'menuitem',
      children: [
        {
          key: '/confirm',
          label: 'File Selection',
          role: 'menuitem',
          tabIndex: 0
        },
        {
          key: '/processing',
          label: 'Processing',
          role: 'menuitem',
          tabIndex: 0
        },
        {
          key: '/dashboard',
          label: 'Dashboard',
          role: 'menuitem',
          tabIndex: 0
        }
      ]
    },
    {
      key: '/neo4j',
      icon: <DatabaseOutlined />,
      label: 'Knowledge Graph',
      role: 'menuitem',
      tabIndex: 0
    },
    {
      type: 'divider'
    },
    {
      key: '/errors',
      icon: <BugOutlined />,
      label: 'Error Dashboard',
      role: 'menuitem',
      tabIndex: 0
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      role: 'menuitem',
      tabIndex: 0
    }
  ];

  const handleMenuClick = (info) => {
    const { key, domEvent } = info;
    
    // Ensure navigation works for both click and keyboard events
    if (key.startsWith('/')) {
      // Prevent default behavior that might interfere
      if (domEvent) {
        domEvent.preventDefault();
        domEvent.stopPropagation();
      }
      
      // Use navigate programmatically
      navigate(key);
    }
  };

  const handleKeyDown = (e) => {
    // Handle keyboard navigation
    if (e.key === 'Enter' || e.key === ' ') {
      const activeElement = document.activeElement;
      if (activeElement && activeElement.getAttribute('data-menu-id')) {
        e.preventDefault();
        const key = activeElement.getAttribute('data-menu-id');
        if (key && key.startsWith('/')) {
          navigate(key);
        }
      }
    }
  };

  // Get selected keys based on current path
  const getSelectedKeys = () => {
    const path = location.pathname;
    
    // Handle dashboard with runId
    if (path.startsWith('/dashboard/')) {
      return ['/dashboard'];
    }
    
    // Handle neo4j with runId
    if (path.startsWith('/neo4j/')) {
      return ['/neo4j'];
    }
    
    return [path];
  };

  return (
    <Sider
      width={250}
      style={{
        background: isDarkMode ? '#0a0000' : '#fff',
        boxShadow: isDarkMode ? '2px 0 8px rgba(255, 0, 64, 0.15)' : '2px 0 8px rgba(0,0,0,0.15)',
        borderRight: isDarkMode ? '1px solid #330000' : 'none'
      }}
    >
      <Menu
        mode="inline"
        selectedKeys={getSelectedKeys()}
        style={{
          height: '100%',
          borderRight: 0,
          paddingTop: 16
        }}
        items={menuItems}
        onClick={handleMenuClick}
        onSelect={handleMenuClick}
        onKeyDown={handleKeyDown}
        tabIndex={0}
      />
    </Sider>
  );
};