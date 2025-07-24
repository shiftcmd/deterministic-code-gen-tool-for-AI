import React, { useEffect } from 'react';
import { Card, Typography, Alert, Button, Row, Col } from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import Phase3Manager from '../components/Phase3Manager.jsx';

const { Title, Text } = Typography;

const Dashboard = () => {
  const { runId } = useParams();
  const navigate = useNavigate();

  // useEffect to preload data - This will be used to fetch dashboard analytics,
  // run details, analysis results, and other dashboard-specific data when the backend is connected
  useEffect(() => {
    // TODO: Preload dashboard data when backend is ready
    // - Fetch run details and analysis results
    // - Load code quality metrics and risk analysis
    // - Get file-by-file analysis data
    // - Prepare charts and visualization data
    // - Cache frequently accessed data for better performance
    
    if (runId) {
      console.log(`Dashboard: Preloading data for run ${runId}`);
      // Example: 
      // const loadDashboardData = async () => {
      //   try {
      //     const [runDetails, metrics, files] = await Promise.all([
      //       api.getRun(runId),
      //       api.getDashboardMetrics(runId), 
      //       api.getRunFiles(runId)
      //     ]);
      //     // Set state with loaded data
      //   } catch (error) {
      //     console.error('Failed to load dashboard data:', error);
      //   }
      // };
      // loadDashboardData();
    } else {
      console.log('Dashboard: No runId provided, loading general dashboard data');
      // Load general dashboard data (recent runs, summary stats, etc.)
    }
  }, [runId]); // Re-run when runId changes

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto' }}>
      <Title level={2}>Analysis Dashboard</Title>
      <Text type="secondary">
        View analysis results and insights {runId && `for run: ${runId}`}
      </Text>

      {/* Phase 3 Management - Only show if we have a runId */}
      {runId && (
        <Card style={{ marginTop: 24 }}>
          <Phase3Manager jobId={runId} />
        </Card>
      )}

      <Card style={{ marginTop: 24 }}>
        <Alert
          message="Dashboard Coming Soon"
          description={`Dashboard ${runId ? `for run ${runId}` : ''} will show:
          • Risk analysis and code quality metrics
          • File-by-file analysis results
          • Code relationships and dependencies
          • Recommendations for improvements
          • Export capabilities (JSON, PDF)`}
          type="info"
          showIcon
          action={
            <Button type="primary" onClick={() => navigate('/history')}>
              View All Runs
            </Button>
          }
        />
      </Card>
    </div>
  );
};

export default Dashboard; 