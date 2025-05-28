import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Container,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  Divider,
  Chip
} from '@mui/material';
import { Settings, Server, TestTube, Info, CheckCircle, XCircle } from 'lucide-react';
import { apiService } from '../services/api';
import { useSnackbar } from 'notistack';

interface TestResult {
  name: string;
  status: 'success' | 'error' | 'running';
  message: string;
  details?: string;
}

const DevToolsPage: React.FC = () => {
  const { enqueueSnackbar } = useSnackbar();
  const [healthStatus, setHealthStatus] = useState<any>(null);
  const [healthLoading, setHealthLoading] = useState(false);
  const [testResults, setTestResults] = useState<TestResult[]>([]);
  const [runningTests, setRunningTests] = useState(false);

  const checkHealth = async () => {
    setHealthLoading(true);
    try {
      const health = await apiService.healthCheck();
      setHealthStatus(health);
      enqueueSnackbar('API server is healthy!', { variant: 'success' });
    } catch (error: any) {
      setHealthStatus({ status: 'error', message: error.message });
      enqueueSnackbar(`Health check failed: ${error.message}`, { variant: 'error' });
    } finally {
      setHealthLoading(false);
    }
  };

  const runTests = async () => {
    setRunningTests(true);
    setTestResults([]);
    
    const tests: TestResult[] = [];
    
    // Test 1: API Health Check
    tests.push({ name: 'API Health Check', status: 'running', message: 'Checking API server status...' });
    setTestResults([...tests]);
    
    try {
      await apiService.healthCheck();
      tests[tests.length - 1] = { name: 'API Health Check', status: 'success', message: 'API server is responsive' };
    } catch (error: any) {
      tests[tests.length - 1] = { name: 'API Health Check', status: 'error', message: error.message };
    }
    setTestResults([...tests]);
    
    // Test 2: SOP Generation (Mock)
    tests.push({ name: 'SOP Generation Test', status: 'running', message: 'Testing SOP generation endpoint...' });
    setTestResults([...tests]);
    
    try {
      const mockResponse = await apiService.generateSOP({
        hardware_config: 'Robot Model: Flex\nAPI Version: 2.20',
        user_goal: 'Test protocol generation'
      });
      tests[tests.length - 1] = { 
        name: 'SOP Generation Test', 
        status: 'success', 
        message: 'SOP generation endpoint is functional',
        details: `Generated ${mockResponse.sop_markdown.length} characters of SOP content`
      };
    } catch (error: any) {
      tests[tests.length - 1] = { name: 'SOP Generation Test', status: 'error', message: error.message };
    }
    setTestResults([...tests]);
    
    // Test 3: Protocol Simulation (Mock)
    tests.push({ name: 'Protocol Simulation Test', status: 'running', message: 'Testing protocol simulation...' });
    setTestResults([...tests]);
    
    try {
      const mockCode = `from opentrons import protocol_api\n\nmetadata = {'apiLevel': '2.20'}\n\ndef run(protocol):\n    pass`;
      const simResponse = await apiService.simulateProtocol({ protocol_code: mockCode });
      tests[tests.length - 1] = { 
        name: 'Protocol Simulation Test', 
        status: 'success', 
        message: 'Protocol simulation is functional',
        details: `Simulation status: ${simResponse.final_status_message}`
      };
    } catch (error: any) {
      tests[tests.length - 1] = { name: 'Protocol Simulation Test', status: 'error', message: error.message };
    }
    setTestResults([...tests]);
    
    setRunningTests(false);
    
    const successCount = tests.filter(t => t.status === 'success').length;
    const totalTests = tests.length;
    
    if (successCount === totalTests) {
      enqueueSnackbar('All tests passed!', { variant: 'success' });
    } else {
      enqueueSnackbar(`${successCount}/${totalTests} tests passed`, { variant: 'warning' });
    }
  };

  const getSystemInfo = () => {
    return {
      'User Agent': navigator.userAgent,
      'Platform': navigator.platform,
      'Language': navigator.language,
      'Online Status': navigator.onLine ? 'Online' : 'Offline',
      'Screen Resolution': `${screen.width}x${screen.height}`,
      'Viewport': `${window.innerWidth}x${window.innerHeight}`,
      'Local Storage Available': typeof Storage !== 'undefined' ? 'Yes' : 'No',
      'API Base URL': 'http://localhost:8000'
    };
  };

  useEffect(() => {
    checkHealth();
  }, []);

  return (
    <Container maxWidth="lg">
      <Box sx={{ py: 4 }}>
        {/* Header */}
        <Box sx={{ mb: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
            Developer Tools
          </Typography>
          
          <Typography variant="body1" color="text.secondary">
            Development utilities and system diagnostics
          </Typography>
        </Box>

        <Grid container spacing={3}>
          {/* API Health Status */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Server size={24} style={{ marginRight: 8 }} />
                  <Typography variant="h6">API Health Status</Typography>
                </Box>
                
                {healthLoading ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={20} />
                    <Typography>Checking...</Typography>
                  </Box>
                ) : healthStatus ? (
                  <Box>
                    <Alert severity={healthStatus.status === 'error' ? 'error' : 'success'}>
                      {healthStatus.message}
                    </Alert>
                    {healthStatus.status !== 'error' && (
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Status: {healthStatus.status || 'Unknown'}
                      </Typography>
                    )}
                  </Box>
                ) : (
                  <Typography color="text.secondary">No health data available</Typography>
                )}
                
                <Button 
                  variant="outlined" 
                  onClick={checkHealth} 
                  sx={{ mt: 2 }}
                  disabled={healthLoading}
                >
                  Refresh Health Check
                </Button>
              </CardContent>
            </Card>
          </Grid>

          {/* Test Suite */}
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <TestTube size={24} style={{ marginRight: 8 }} />
                  <Typography variant="h6">API Test Suite</Typography>
                </Box>
                
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Run comprehensive tests on all API endpoints
                </Typography>
                
                <Button 
                  variant="contained" 
                  onClick={runTests}
                  disabled={runningTests}
                  startIcon={runningTests ? <CircularProgress size={20} /> : <TestTube size={20} />}
                >
                  {runningTests ? 'Running Tests...' : 'Run All Tests'}
                </Button>
                
                {testResults.length > 0 && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle2" gutterBottom>
                      Test Results:
                    </Typography>
                    <List dense>
                      {testResults.map((result, index) => (
                        <ListItem key={index}>
                          <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                            {result.status === 'running' && <CircularProgress size={16} sx={{ mr: 1 }} />}
                            {result.status === 'success' && <CheckCircle size={16} color="green" style={{ marginRight: 8 }} />}
                            {result.status === 'error' && <XCircle size={16} color="red" style={{ marginRight: 8 }} />}
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="body2" fontWeight={500}>
                                {result.name}
                              </Typography>
                              <Typography variant="caption" color="text.secondary">
                                {result.message}
                              </Typography>
                              {result.details && (
                                <Typography variant="caption" display="block" color="text.secondary">
                                  {result.details}
                                </Typography>
                              )}
                            </Box>
                            <Chip 
                              label={result.status.toUpperCase()} 
                              size="small" 
                              color={result.status === 'success' ? 'success' : result.status === 'error' ? 'error' : 'default'}
                            />
                          </Box>
                        </ListItem>
                      ))}
                    </List>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* System Information */}
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  <Info size={24} style={{ marginRight: 8 }} />
                  <Typography variant="h6">System Information</Typography>
                </Box>
                
                <Grid container spacing={2}>
                  {Object.entries(getSystemInfo()).map(([key, value]) => (
                    <Grid item xs={12} sm={6} md={4} key={key}>
                      <Paper variant="outlined" sx={{ p: 2 }}>
                        <Typography variant="caption" color="text.secondary">
                          {key}
                        </Typography>
                        <Typography variant="body2" sx={{ wordBreak: 'break-all' }}>
                          {value}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
};

export default DevToolsPage;