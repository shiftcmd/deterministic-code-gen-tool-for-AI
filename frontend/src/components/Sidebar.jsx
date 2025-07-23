import React from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  HomeOutlined,
  FileSearchOutlined,
  PlayCircleOutlined,
  DashboardOutlined,
  HistoryOutlined,
  PartitionOutlined,
  FolderOpenOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useApp } from '../context/AppContext.jsx';

const { Sider } = Layout;

export const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { theme, sidebarCollapsed } = useApp();

  // Menu items configuration
  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'Project Selector',
      path: '/'
    },
    {
      key: '/confirm',
      icon: <FileSearchOutlined />,
      label: 'File Confirmation',
      path: '/confirm'
    },
    {
      key: '/processing',
      icon: <PlayCircleOutlined />,
      label: 'Processing',
      path: '/processing'
    },
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      path: '/dashboard'
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: 'History',
      path: '/history'
    },
    {
      key: '/neo4j',
      icon: <PartitionOutlined />,
      label: 'Neo4j Graph',
      path: '/neo4j'
    },
    {
      key: '/explorer',
      icon: <FolderOpenOutlined />,
      label: 'File Explorer',
      path: '/explorer'
    },
    {
      key: '/errors',
      icon: <ExclamationCircleOutlined />,
      label: 'Error Dashboard',
      path: '/errors'
    }
  ];

  const handleMenuClick = ({ key }) => {
    // Direct navigation approach - this should fix the click-then-enter issue
    const menuItem = menuItems.find(m => m.key === key);
    if (menuItem && menuItem.path !== location.pathname) {
      // Only navigate if we're not already on the target path
      navigate(menuItem.path);
    }
  };

  const getSelectedKeys = () => {
    // Find the menu item that matches the current location
    const currentItem = menuItems.find(item => {
      if (item.path === '/') {
        return location.pathname === '/';
      }
      return location.pathname.startsWith(item.path);
    });
    
    return currentItem ? [currentItem.key] : ['/'];
  };

  return (
    <Sider 
      trigger={null} 
      collapsible 
      collapsed={sidebarCollapsed}
      theme={theme}
      width={200}
      collapsedWidth={80}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 64, // Height of header
        zIndex: 100,
        boxShadow: theme === 'dark' ? 'none' : '2px 0 8px rgba(0,0,0,0.1)',
        borderRight: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`
      }}
    >
      <div style={{ 
        padding: sidebarCollapsed ? '16px 8px' : '16px 24px',
        borderBottom: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
        textAlign: sidebarCollapsed ? 'center' : 'left'
      }}>
        {!sidebarCollapsed && (
          <div style={{ 
            color: theme === 'dark' ? '#a0a0a0' : '#666',
            fontSize: '12px',
            fontWeight: 500,
            textTransform: 'uppercase',
            letterSpacing: '1px'
          }}>
            Navigation
          </div>
        )}
      </div>

      <Menu
        theme={theme}
        mode="inline"
        selectedKeys={getSelectedKeys()}
        onClick={handleMenuClick}
        style={{
          height: '100%',
          borderRight: 0,
          paddingTop: 8
        }}
        items={menuItems.map(item => ({
          key: item.key,
          icon: <span style={{ fontSize: '16px' }}>{item.icon}</span>,
          label: (
            <span style={{ 
              fontSize: '14px',
              fontWeight: getSelectedKeys().includes(item.key) ? 600 : 400
            }}>
              {item.label}
            </span>
          ),
          style: {
            margin: '4px 8px',
            borderRadius: 8,
            height: 48,
            lineHeight: '48px',
            paddingLeft: sidebarCollapsed ? 0 : 16
          }
        }))}
      />

      {!sidebarCollapsed && (
        <div style={{ 
          position: 'absolute',
          bottom: 16,
          left: 24,
          right: 24,
          color: theme === 'dark' ? '#666' : '#999',
          fontSize: '11px',
          textAlign: 'center'
        }}>
          Python Debug Tool v1.0
        </div>
      )}
    </Sider>
  );
};

export default Sidebar; 