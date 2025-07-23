import React from 'react';
import { Card, Typography, Alert, Button } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const FileExplorer = () => {
  const { runId } = useParams();
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>File Explorer</Title>
      <Text type="secondary">
        Browse analyzed files and view detailed analysis
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Alert
          message="File Explorer Coming Soon"
          description={`File explorer for run ${runId || 'N/A'} will provide:
          • Interactive file tree with analysis results
          • Detailed file-level analysis and metrics
          • Risk assessment and recommendations
          • Code highlighting and annotations
          • IDE integration for opening files`}
          type="info"
          showIcon
          action={
            <Button type="primary" onClick={() => navigate(`/dashboard/${runId}`)}>
              View Dashboard
            </Button>
          }
        />
      </Card>
    </div>
  );
};

export default FileExplorer; 