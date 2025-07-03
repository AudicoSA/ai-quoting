// frontend/src/components/TrainingCenter/TrainingStatus.js
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Alert,
  LinearProgress,
  Grid
} from '@mui/material';
import { Psychology, Storage, Business, CheckCircle } from '@mui/icons-material';

const TrainingStatus = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await fetch('/api/v1/training/status');
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error('Failed to fetch training status:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchStatus();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchStatus, 30000);
    return () => clearInterval(interval);
  }, []);
  
  if (loading) {
    return (
      <Card sx={{ m: 2 }}>
        <CardContent>
          <Typography variant="h6">Loading training status...</Typography>
          <LinearProgress sx={{ mt: 2 }} />
        </CardContent>
      </Card>
    );
  }
  
  if (!status?.ai_training_available) {
    return (
      <Alert severity="warning" sx={{ m: 2 }}>
        <Typography variant="h6">⚠️ AI Training Configuration Needed</Typography>
        <Typography variant="body2" sx={{ mt: 1 }}>
          {!status?.openai_configured 
            ? "OpenAI API key not configured. Please set OPENAI_API_KEY in your environment."
            : "AI Training system not initialized properly."
          }
        </Typography>
      </Alert>
    );
  }
  
  const knowledgeBase = status.knowledge_base_summary || {};
  const totalProducts = knowledgeBase.total_products || 0;
  const supplierCount = Object.keys(knowledgeBase.suppliers || {}).length;
  
  return (
    <Card sx={{ m: 2 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Psychology sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="h6">🧠 AI Training Status</Typography>
          <Box sx={{ flexGrow: 1 }} />
          <Chip 
            icon={<CheckCircle />}
            label={status.system_status === 'operational' ? 'Operational' : 'Configuration Needed'}
            color={status.system_status === 'operational' ? 'success' : 'warning'}
            size="small"
          />
        </Box>
        
        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Storage sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
              <Typography variant="h4" color="primary">
                {totalProducts.toLocaleString()}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Products Trained
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Business sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
              <Typography variant="h4" color="secondary">
                {supplierCount}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Suppliers Processed
              </Typography>
            </Box>
          </Grid>
          
          <Grid item xs={12} md={4}>
            <Box sx={{ textAlign: 'center', p: 2, bgcolor: 'background.paper', borderRadius: 1 }}>
              <Psychology sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
              <Typography variant="h4" color="success.main">
                {status.document_intelligence_ready && status.audio_consultant_ready ? '✅' : '⚠️'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                AI Intelligence
              </Typography>
            </Box>
          </Grid>
        </Grid>
        
        {/* Recent Suppliers */}
        {supplierCount > 0 && (
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>
              Recent Suppliers:
            </Typography>
            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
              {Object.entries(knowledgeBase.suppliers || {}).slice(0, 5).map(([supplier, data]) => (
                <Chip
                  key={supplier}
                  label={`${supplier} (${data.product_count} products)`}
                  size="small"
                  variant="outlined"
                />
              ))}
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default TrainingStatus;
