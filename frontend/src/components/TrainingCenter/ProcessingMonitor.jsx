// frontend/src/components/TrainingCenter/ProcessingMonitor.jsx
import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  LinearProgress,
  Alert,
  Button,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Fade,
  CircularProgress,
  Paper
} from '@mui/material';
import {
  CheckCircle,
  Error,
  Refresh,
  Download,
  Analytics,
  Speed,
  Storage,
  Celebration
} from '@mui/icons-material';

const ProcessingMonitor = ({ sessionId, onComplete }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isPolling, setIsPolling] = useState(true);

  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`/api/training-center/status/${sessionId}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch status: ${response.status}`);
      }
      
      const statusData = await response.json();
      setStatus(statusData);
      setLoading(false);
      
      // Stop polling if completed or failed
      if (statusData.status === 'completed' || statusData.status === 'failed') {
        setIsPolling(false);
      }
      
    } catch (err) {
      setError(err.message);
      setLoading(false);
      setIsPolling(false);
    }
  }, [sessionId]);

  useEffect(() => {
    // Initial fetch
    fetchStatus();
  }, [fetchStatus]);

  useEffect(() => {
    // Set up polling for status updates
    if (!isPolling) return;

    const interval = setInterval(() => {
      fetchStatus();
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(interval);
  }, [isPolling, fetchStatus]);

  const getStageInfo = (stage) => {
    const stages = {
      extracting: {
        label: 'Extracting Products',
        icon: <Analytics color="primary" />,
        description: 'Using AI to extract products from your pricelist'
      },
      processing: {
        label: 'Processing Data',
        icon: <Speed color="secondary" />,
        description: 'Applying configurations and validating products'
      },
      saving: {
        label: 'Saving to Database',
        icon: <Storage color="success" />,
        description: 'Storing products in the AI knowledge base'
      },
      completed: {
        label: 'Processing Complete',
        icon: <Celebration color="success" />,
        description: 'All products have been successfully processed'
      }
    };
    
    return stages[stage] || {
      label: 'Processing...',
      icon: <CircularProgress size={20} />,
      description: 'Working on your data'
    };
  };

  const getProgressColor = (percent) => {
    if (percent >= 100) return 'success';
    if (percent >= 75) return 'info';
    if (percent >= 50) return 'warning';
    return 'primary';
  };

  const handleRetry = () => {
    setLoading(true);
    setError(null);
    setIsPolling(true);
    fetchStatus();
  };

  if (loading && !status) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Starting processing...
        </Typography>
      </Box>
    );
  }

  if (error && !status) {
    return (
      <Alert 
        severity="error" 
        action={
          <Button color="inherit" size="small" onClick={handleRetry}>
            <Refresh /> Retry
          </Button>
        }
      >
        <Typography variant="h6">Connection Error</Typography>
        {error}
      </Alert>
    );
  }

  const currentStage = status?.progress?.stage || 'extracting';
  const progressPercent = status?.progress?.percent || 0;
  const stageInfo = getStageInfo(currentStage);

  return (
    <Box>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h4" gutterBottom>
          {status?.status === 'completed' ? '🎉' : '⚡'} Processing Status
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Session: {sessionId}
        </Typography>
      </Box>

      {/* Main Status Card */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          {/* Current Stage */}
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            {stageInfo.icon}
            <Box sx={{ ml: 2, flex: 1 }}>
              <Typography variant="h6">{stageInfo.label}</Typography>
              <Typography variant="body2" color="text.secondary">
                {stageInfo.description}
              </Typography>
            </Box>
            <Chip 
              label={`${progressPercent}%`} 
              color={getProgressColor(progressPercent)}
              variant="outlined"
            />
          </Box>

          {/* Progress Bar */}
          <Box sx={{ mb: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={progressPercent} 
              color={getProgressColor(progressPercent)}
              sx={{ height: 12, borderRadius: 6 }}
            />
          </Box>

          {/* Status Message */}
          <Typography variant="body1" textAlign="center" sx={{ mb: 2 }}>
            {status?.message || status?.current_message || 'Processing your data...'}
          </Typography>

          {/* Processing Stages List */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Processing Stages</Typography>
              <List dense>
                {['extracting', 'processing', 'saving', 'completed'].map((stage, index) => {
                  const isCurrentStage = currentStage === stage;
                  const isCompleted = ['extracting', 'processing', 'saving'].indexOf(currentStage) > index;
                  const stageData = getStageInfo(stage);
                  
                  return (
                    <ListItem key={stage}>
                      <ListItemIcon>
                        {isCompleted ? (
                          <CheckCircle color="success" />
                        ) : isCurrentStage ? (
                          stageData.icon
                        ) : (
                          <Box sx={{ width: 24, height: 24, bgcolor: 'grey.300', borderRadius: '50%' }} />
                        )}
                      </ListItemIcon>
                      <ListItemText 
                        primary={stageData.label}
                        primaryTypographyProps={{
                          fontWeight: isCurrentStage ? 'bold' : 'normal',
                          color: isCompleted ? 'success.main' : isCurrentStage ? 'primary.main' : 'text.secondary'
                        }}
                      />
                    </ListItem>
                  );
                })}
              </List>
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>Session Details</Typography>
              <Paper sx={{ p: 2, bgcolor: 'grey.50' }}>
                <Grid container spacing={1}>
                  <Grid item xs={6}>
                    <Typography variant="caption">Status:</Typography>
                    <Typography variant="body2" fontWeight="bold">
                      {status?.status || 'Unknown'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption">Started:</Typography>
                    <Typography variant="body2">
                      {status?.started_at ? new Date(status.started_at).toLocaleTimeString() : 'N/A'}
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption">Progress:</Typography>
                    <Typography variant="body2" fontWeight="bold" color="primary">
                      {progressPercent}%
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="caption">ETA:</Typography>
                    <Typography variant="body2">
                      {status?.estimated_completion ? 
                        new Date(status.estimated_completion).toLocaleTimeString() : 
                        'Calculating...'
                      }
                    </Typography>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Completion Results */}
      {status?.status === 'completed' && status?.result && (
        <Fade in={true}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ textAlign: 'center', mb: 3 }}>
                <Celebration sx={{ fontSize: 64, color: 'success.main' }} />
                <Typography variant="h4" color="success.main" gutterBottom>
                  Processing Complete!
                </Typography>
                <Typography variant="h6" color="text.secondary">
                  Your AI knowledge base has been successfully updated
                </Typography>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} sm={4}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'success.light' }}>
                    <Typography variant="h3" color="success.dark">
                      {status.result.successfully_saved?.toLocaleString() || 0}
                    </Typography>
                    <Typography variant="subtitle1">Products Saved</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'info.light' }}>
                    <Typography variant="h3" color="info.dark">
                      {status.result.total_processed?.toLocaleString() || 0}
                    </Typography>
                    <Typography variant="subtitle1">Total Processed</Typography>
                  </Paper>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <Paper sx={{ p: 2, textAlign: 'center', bgcolor: 'primary.light' }}>
                    <Typography variant="h3" color="primary.dark">
                      {Math.round(((status.result.successfully_saved || 0) / (status.result.total_processed || 1)) * 100)}%
                    </Typography>
                    <Typography variant="subtitle1">Success Rate</Typography>
                  </Paper>
                </Grid>
              </Grid>

              <Alert severity="success" sx={{ mt: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  🚀 AI Training Complete!
                </Typography>
                <Typography variant="body2">
                  Your AI assistant now has enhanced knowledge about these products and can provide better quotes and recommendations.
                  Completed at: {status.result.completion_time ? new Date(status.result.completion_time).toLocaleString() : 'Unknown'}
                </Typography>
              </Alert>

              <Box sx={{ textAlign: 'center', mt: 3 }}>
                <Button
                  variant="contained"
                  size="large"
                  onClick={onComplete}
                  startIcon={<CheckCircle />}
                >
                  Start New Upload
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Fade>
      )}

      {/* Error State */}
      {status?.status === 'failed' && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            ❌ Processing Failed
          </Typography>
          <Typography variant="body2">
            {status.current_message || 'An error occurred during processing.'}
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Button variant="outlined" onClick={handleRetry} startIcon={<Refresh />}>
              Check Status Again
            </Button>
            <Button variant="contained" onClick={onComplete} sx={{ ml: 2 }}>
              Start Over
            </Button>
          </Box>
        </Alert>
      )}

      {/* Real-time Updates Indicator */}
      {isPolling && status?.status !== 'completed' && status?.status !== 'failed' && (
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Chip 
            icon={<Refresh />} 
            label="Live Updates Active" 
            color="primary" 
            variant="outlined" 
            size="small"
          />
        </Box>
      )}
    </Box>
  );
};

export default ProcessingMonitor;
