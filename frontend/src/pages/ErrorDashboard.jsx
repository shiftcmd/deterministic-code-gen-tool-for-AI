import React from 'react';
import { Card, Typography, Alert, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const ErrorDashboard = () => {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>Error Dashboard</Title>
      <Text type="secondary">
        Monitor and troubleshoot application errors
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Alert
          message="Error Dashboard Coming Soon"
          description="This dashboard will provide:
          • Real-time error monitoring and alerts
          • Error categorization and severity levels
          • Stack traces and debugging information
          • Error frequency and trends analysis
          • Integration with external logging services"
          type="info"
          showIcon
          action={
            <Button type="primary" onClick={() => navigate('/')}>
              Go to Home
            </Button>
          }
        />
      </Card>
    </div>
  );
};

export default ErrorDashboard; 