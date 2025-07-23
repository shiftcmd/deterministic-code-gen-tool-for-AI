import React from 'react';
import { Layout, Button, Typography, Space, Tooltip, Avatar } from 'antd';
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined, 
  BugOutlined,
  BulbOutlined,
  BulbFilled,
  SettingOutlined
} from '@ant-design/icons';
import { useApp } from '../context/AppContext.jsx';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

export const Header = () => {
  const { theme, sidebarCollapsed, toggleTheme, toggleSidebar } = useApp();

  return (
    <AntHeader 
      style={{ 
        padding: '0 24px',
        background: theme === 'dark' ? '#001529' : '#fff',
        borderBottom: `1px solid ${theme === 'dark' ? '#303030' : '#f0f0f0'}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}
    >
      <Space align="center" size="middle">
        <Button
          type="text"
          icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
          onClick={toggleSidebar}
          style={{
            fontSize: '18px',
            width: 48,
            height: 48,
            color: theme === 'dark' ? '#fff' : '#000',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        />
        
        <Space align="center" size="middle">
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            width: 40,
            height: 40,
            borderRadius: '50%',
            background: 'linear-gradient(135deg, #1890ff, #722ed1)',
            boxShadow: '0 2px 8px rgba(24, 144, 255, 0.3)'
          }}>
            <BugOutlined style={{ fontSize: '20px', color: '#fff' }} />
          </div>
          <div>
            <Title 
              level={3} 
              style={{ 
                margin: 0, 
                color: theme === 'dark' ? '#fff' : '#000',
                fontWeight: 600,
                letterSpacing: '-0.5px'
              }}
            >
              Python Debug Tool
            </Title>
            <div style={{ 
              fontSize: '12px', 
              color: theme === 'dark' ? '#a0a0a0' : '#666',
              marginTop: '-4px'
            }}>
              Code Analysis Platform
            </div>
          </div>
        </Space>
      </Space>

      <Space size="middle">
        <Tooltip title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}>
          <Button
            type="text"
            icon={theme === 'light' ? <BulbOutlined /> : <BulbFilled />}
            onClick={toggleTheme}
            style={{
              color: theme === 'dark' ? '#fff' : '#000',
              fontSize: '16px',
              width: 40,
              height: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          />
        </Tooltip>
        
        <Tooltip title="Settings">
          <Button
            type="text"
            icon={<SettingOutlined />}
            style={{
              color: theme === 'dark' ? '#fff' : '#000',
              fontSize: '16px',
              width: 40,
              height: 40,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          />
        </Tooltip>

        <Avatar 
          style={{ 
            backgroundColor: '#1890ff',
            cursor: 'pointer'
          }}
          size="default"
        >
          U
        </Avatar>
      </Space>
    </AntHeader>
  );
};

export default Header; 