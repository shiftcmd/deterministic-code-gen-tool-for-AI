import React from 'react';
import { Layout, Typography, Space, Button, Tooltip, Switch } from 'antd';
import {
  CodeOutlined,
  GithubOutlined,
  QuestionCircleOutlined,
  SettingOutlined,
  BulbOutlined,
  BulbFilled
} from '@ant-design/icons';
import { useTheme } from '../../context/ThemeContext';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

export const Header = () => {
  const { isDarkMode, toggleTheme } = useTheme();
  
  return (
    <AntHeader 
      style={{
        background: isDarkMode ? '#000000' : '#001529',
        padding: '0 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: isDarkMode ? '1px solid #330000' : 'none'
      }}
    >
      <Space>
        <CodeOutlined style={{ fontSize: 24, color: isDarkMode ? '#ff0040' : '#1890ff' }} />
        <Title 
          level={4} 
          style={{ 
            color: isDarkMode ? '#ff0040' : 'white', 
            margin: 0,
            fontWeight: isDarkMode ? 400 : 300,
            textShadow: isDarkMode ? '0 0 10px rgba(255, 0, 64, 0.5)' : 'none'
          }}
        >
          Deterministic AI Framework
        </Title>
      </Space>
      
      <Space>
        <Tooltip title={isDarkMode ? "Light Mode" : "SCARLET Protocol"}>
          <Button
            type="text"
            icon={isDarkMode ? <BulbFilled /> : <BulbOutlined />}
            onClick={toggleTheme}
            style={{ 
              color: isDarkMode ? '#ff0040' : 'white',
              fontSize: 18
            }}
          />
        </Tooltip>
        <Tooltip title="Documentation">
          <Button 
            type="text" 
            icon={<QuestionCircleOutlined />}
            style={{ color: isDarkMode ? '#ff6666' : 'white' }}
            href="https://github.com/your-repo/docs"
            target="_blank"
          />
        </Tooltip>
        <Tooltip title="GitHub Repository">
          <Button 
            type="text" 
            icon={<GithubOutlined />}
            style={{ color: isDarkMode ? '#ff6666' : 'white' }}
            href="https://github.com/your-repo"
            target="_blank"
          />
        </Tooltip>
        <Tooltip title="Settings">
          <Button 
            type="text" 
            icon={<SettingOutlined />}
            style={{ color: isDarkMode ? '#ff6666' : 'white' }}
          />
        </Tooltip>
      </Space>
    </AntHeader>
  );
};