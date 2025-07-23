import React from 'react';
import { Card, Typography, Alert, Button } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';

const { Title, Text } = Typography;

const Neo4jGraph = () => {
  const { runId } = useParams();
  const navigate = useNavigate();

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>Knowledge Graph Visualization</Title>
      <Text type="secondary">
        Explore code relationships and dependencies
      </Text>

      <Card style={{ marginTop: 24 }}>
        <Alert
          message="Neo4j Graph View Coming Soon"
          description={`Graph visualization for run ${runId || 'N/A'} will include:
          • Interactive graph visualization of code relationships
          • Cypher query interface for custom queries
          • Node and relationship filtering
          • Export graph data in various formats
          • Schema exploration and validation`}
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

export default Neo4jGraph; 