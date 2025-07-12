import React, { useState } from 'react';
import { Box, Paper, TextField, Button, Typography, Alert } from '@mui/material';
import axios from 'axios';

const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('admin@audico.co.za');
  const [password, setPassword] = useState('admin123');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const response = await axios.post('http://localhost:8000/api/auth/login', {
        email,
        password
      });

      onLogin(response.data);
    } catch (error) {
      setError(error.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box sx={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      minHeight: '80vh',
      p: 3
    }}>
      <Paper sx={{ p: 4, maxWidth: 400, width: '100%' }}>
        <Typography variant="h4" gutterBottom align="center">
          🎵 Audico AI
        </Typography>
        <Typography variant="h6" gutterBottom align="center" color="text.secondary">
          Admin Login
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <form onSubmit={handleSubmit}>
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            margin="normal"
            required
          />
          <Button
            type="submit"
            fullWidth
            variant="contained"
            sx={{ mt: 3, mb: 2 }}
            disabled={loading}
          >
            {loading ? 'Logging in...' : 'Login'}
          </Button>
        </form>
      </Paper>
    </Box>
  );
};

export default Login;