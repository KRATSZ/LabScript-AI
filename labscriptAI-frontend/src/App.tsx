import { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { SnackbarProvider } from 'notistack';

// Pages
import WelcomePage from './pages/WelcomePage';
import HardwareConfigPage from './pages/HardwareConfigPage';
import SopDefinitionPage from './pages/SopDefinitionPage';
import CodeGenerationPage from './pages/CodeGenerationPage';
import SimulationResultsPage from './pages/SimulationResultsPage';
import AnimationPage from './pages/AnimationPage';
import DevToolsPage from './pages/DevToolsPage';

// Components
import Layout from './components/Layout';

// Theme and Context
import theme from './theme';
import { AppContextProvider } from './context/AppContext';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <SnackbarProvider maxSnack={3}>
        <AppContextProvider>
          <Router>
            <Layout>
              <Routes>
                <Route path="/" element={<WelcomePage />} />
                <Route path="/configure-hardware" element={<HardwareConfigPage />} />
                <Route path="/define-sop" element={<SopDefinitionPage />} />
                <Route path="/generate-code" element={<CodeGenerationPage />} />
                <Route path="/simulation-results" element={<SimulationResultsPage />} />
                <Route path="/animation" element={<AnimationPage />} />
                <Route path="/dev-tools" element={<DevToolsPage />} />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
            </Layout>
          </Router>
        </AppContextProvider>
      </SnackbarProvider>
    </ThemeProvider>
  );
}

export default App;