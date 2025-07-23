import React from 'react';
import { Card, Typography, Alert, Button } from 'antd';
import { useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const History = () => {
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>Analysis History</Title>
      <Text type="secondary">
        View and manage previous analysis runs
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Alert
          message="History View Coming Soon"
          description="This page will show:
          • List of all previous analysis runs
          • Run status, duration, and completion time
          • Quick access to results and dashboards
          • Delete and export functionality
          • Search and filter capabilities"
          type="info"
          showIcon
          action={
            <Button type="primary" onClick={() => navigate('/')}>
              Start New Analysis
            </Button>
          }
        />
      </Card>
    </div>
  );
};

export default History; 