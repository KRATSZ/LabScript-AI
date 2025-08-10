import React, { useState } from 'react';
import { 
  Container, 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  Button, 
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Paper,
  Divider,
  CircularProgress,
  Alert,
  AlertTitle
} from '@mui/material';
import { 
  CheckCircle, 
  XCircle, 
  Settings, 
  Wifi, 
  Code, 
  Play, 
  TestTube,
  Activity,
  AlertTriangle
} from 'lucide-react';
import { ApiTester } from '../utils/apiTester';

interface TestResults {
  connection: boolean;
  endpoints: {
    health: boolean;
    sopGeneration: boolean;
    simulation: boolean;
    tools: boolean;
  };
  codeGeneration: boolean;
  overall: boolean;
}

const DevToolsPage: React.FC = () => {
  const [testResults, setTestResults] = useState<TestResults | null>(null);
  const [testing, setTesting] = useState(false);
  const [currentTest, setCurrentTest] = useState<string>('');

  const runQuickTests = async () => {
    setTesting(true);
    setCurrentTest('Connection Test');
    try {
      const results = await ApiTester.testAllEndpoints();
      setTestResults({
        connection: true,
        endpoints: results,
        codeGeneration: false,
        overall: Object.values(results).every(Boolean)
      });
    } catch (error) {
      console.error('Test execution failed:', error);
    } finally {
      setTesting(false);
      setCurrentTest('');
    }
  };

  const runFullTests = async () => {
    setTesting(true);
    setCurrentTest('Full Test Suite');
    try {
      const results = await ApiTester.runFullTest();
      setTestResults(results);
    } catch (error) {
      console.error('Full test execution failed:', error);
    } finally {
      setTesting(false);
      setCurrentTest('');
    }
  };

  const testConnection = async () => {
    setTesting(true);
    setCurrentTest('Connection Test');
    try {
      const isConnected = await ApiTester.testConnection();
      setTestResults({
        connection: isConnected,
        endpoints: {
          health: isConnected,
          sopGeneration: false,
          simulation: false,
          tools: false
        },
        codeGeneration: false,
        overall: isConnected
      });
    } catch (error) {
      console.error('Connection test failed:', error);
    } finally {
      setTesting(false);
      setCurrentTest('');
    }
  };

  const getStatusIcon = (status: boolean) => {
    return status ? 
      <CheckCircle size={20} color="#4caf50" /> : 
      <XCircle size={20} color="#f44336" />;
  };

  const getStatusChip = (status: boolean, label: string) => {
    return (
      <Chip 
        icon={getStatusIcon(status)}
        label={label} 
        color={status ? 'success' : 'error'}
        size="small"
        variant="outlined"
      />
    );
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ fontWeight: 700 }}>
          Developer Tools
        </Typography>
        <Typography variant="body1" color="text.secondary">
          API connection tests, debugging tools, and system status monitoring.
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Test Controls */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TestTube size={24} style={{ marginRight: 8 }} />
                <Typography variant="h6">
                  API Test Suite
                </Typography>
              </Box>
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                Test connectivity with the backend API server and the functionality of various endpoints.
              </Typography>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Button 
                  variant="outlined" 
                  startIcon={<Wifi />}
                  onClick={testConnection}
                  disabled={testing}
                  fullWidth
                >
                  Test Connection
                </Button>

                <Button 
                  variant="outlined" 
                  startIcon={<Activity />}
                  onClick={runQuickTests}
                  disabled={testing}
                  fullWidth
                >
                  Quick Tests (Endpoints)
                </Button>
                
                <Button 
                  variant="contained" 
                  startIcon={<Play />}
                  onClick={runFullTests}
                  disabled={testing}
                  fullWidth
                >
                  Full Test Suite
                </Button>
              </Box>

              {testing && (
                <Box sx={{ mt: 3, textAlign: 'center' }}>
                  <CircularProgress size={24} sx={{ mr: 1 }} />
                  <Typography variant="body2" color="text.secondary">
                    Running: {currentTest}
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* System Info */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Settings size={24} style={{ marginRight: 8 }} />
                <Typography variant="h6">
                  System Information
                </Typography>
              </Box>
              
              <List dense>
                <ListItem>
                  <ListItemText 
                    primary="API Server URL" 
                    secondary={import.meta.env.VITE_API_BASE_URL || 'https://api.ai4ot.cn'} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Development Mode" 
                    secondary={import.meta.env.VITE_DEV_MODE || 'true'} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="Build Time" 
                    secondary={new Date().toLocaleString()} 
                  />
                </ListItem>
                <ListItem>
                  <ListItemText 
                    primary="User Agent" 
                    secondary={navigator.userAgent.substring(0, 50) + '...'} 
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Test Results */}
        {testResults && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center'}}>
                    <Code size={24} style={{ marginRight: 8 }} />
                    <Typography variant="h6">
                      Test Results
                    </Typography>
                  </Box>
                  {getStatusChip(testResults.overall, testResults.overall ? 'All Passed' : 'Issues Found')}
                </Box>

                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <Paper variant="outlined" sx={{ p: 2 }}>
                      <Typography variant="subtitle1" gutterBottom>Connection Status</Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>{getStatusIcon(testResults.connection)}</ListItemIcon>
                          <ListItemText primary="Backend Connection" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>{getStatusIcon(testResults.endpoints.health)}</ListItemIcon>
                          <ListItemText primary="Endpoint Health Check (/)" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>{getStatusIcon(testResults.endpoints.sopGeneration)}</ListItemIcon>
                          <ListItemText primary="SOP Generation (/generate-sop)" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>{getStatusIcon(testResults.endpoints.simulation)}</ListItemIcon>
                          <ListItemText primary="Simulation Endpoint (/simulate-protocol)" />
                        </ListItem>
                        <ListItem>
                          <ListItemIcon>{getStatusIcon(testResults.endpoints.tools)}</ListItemIcon>
                          <ListItemText primary="Tools Interface (/tools)" />
                        </ListItem>
                      </List>
                    </Paper>
                  </Grid>
                  
                  <Grid item xs={12} sm={6}>
                    <Paper variant="outlined" sx={{ p: 2, height: '100%' }}> 
                      <Typography variant="subtitle1" gutterBottom>Advanced Tests</Typography>
                      <List dense>
                        <ListItem>
                          <ListItemIcon>{getStatusIcon(testResults.codeGeneration)}</ListItemIcon>
                          <ListItemText primary="Code Generation Functionality (Full Test Req.)" />
                        </ListItem>
                      </List>
                       {!testResults.overall && testResults.connection && (
                        <Alert severity="warning" sx={{ mt: 2 }}>
                          <AlertTitle>Partial Test Failure</AlertTitle>
                          Some API endpoint tests failed. Please check the console logs for more details.
                        </Alert>
                      )}
                      {!testResults.connection && (
                         <Alert severity="error" sx={{ mt: 2 }}>
                          <AlertTitle>Test Failure</AlertTitle>
                          API connection test failed. Please ensure the backend server is running and network connectivity is okay.
                        </Alert>
                      )}
                      {testResults.overall && (
                        <Alert severity="success" sx={{ mt: 2 }}>
                          <AlertTitle>All Tests Passed</AlertTitle>
                          All API endpoints and functionalities passed successfully!
                        </Alert>
                      )}
                    </Paper>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default DevToolsPage;