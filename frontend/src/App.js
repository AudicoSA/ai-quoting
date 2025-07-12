import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, AppBar, Toolbar, Typography, Button } from '@mui/material';
import Login from './components/Login';
import AdminDashboard from './components/AdminDashboard';
import PricelistUpload from './components/admin/PricelistUpload';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  const [user, setUser] = useState(null);

  const handleLogin = (userData) => {
    setUser(userData);
    localStorage.setItem('token', userData.access_token);
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem('token');
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ flexGrow: 1 }}>
          <AppBar position="static">
            <Toolbar>
              <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                🎵 Audico AI Quoting System
              </Typography>
              {user && (
                <Button color="inherit" onClick={handleLogout}>
                  Logout
                </Button>
              )}
            </Toolbar>
          </AppBar>

          <Routes>
            <Route 
              path="/login" 
              element={!user ? <Login onLogin={handleLogin} /> : <Navigate to="/admin" />} 
            />
            <Route 
              path="/admin" 
              element={user ? <AdminDashboard user={user} /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/admin/upload" 
              element={user ? <PricelistUpload /> : <Navigate to="/login" />} 
            />
            <Route 
              path="/" 
              element={<Navigate to={user ? "/admin" : "/login"} />} 
            />
          </Routes>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;