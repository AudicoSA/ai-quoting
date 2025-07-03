// frontend/src/components/TrainingCenter/EnhancedUploadCenter.jsx
import React, { useState, useCallback } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Alert,
  LinearProgress,
  Stepper,
  Step,
  StepLabel,
  Fade,
  useTheme
} from '@mui/material';
import { Upload, Analytics, Settings, CheckCircle } from '@mui/icons-material';
import FileUploadZone from './FileUploadZone';
import StructureAnalysisDisplay from './StructureAnalysisDisplay';
import ProcessingConfigurationPanel from './ProcessingConfigurationPanel';
import ProcessingMonitor from './ProcessingMonitor';

const steps = ['Upload File', 'Analyze Structure', 'Configure Processing', 'Process & Save'];

const EnhancedUploadCenter = () => {
  const theme = useTheme();
  const [activeStep, setActiveStep] = useState(0);
  const [sessionData, setSessionData] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [processingSessionId, setProcessingSessionId] = useState(null);

  const handleFileUpload = useCallback(async (file) => {
    setProcessing(true);
    setError(null);
    setActiveStep(1);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/training-center/upload/advanced', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const result = await response.json();
      setSessionData(result);
      setActiveStep(2);
      
    } catch (err) {
      setError(err.message);
      setActiveStep(0);
    } finally {
      setProcessing(false);
    }
  }, []);

  const handleStartProcessing = useCallback(async (configOverrides = {}) => {
    if (!sessionData?.session_id) return;

    setProcessing(true);
    setActiveStep(3);

    try {
      const response = await fetch(`/api/training-center/process/enhanced/${sessionData.session_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(configOverrides),
      });

      if (!response.ok) {
        throw new Error(`Processing failed: ${response.status}`);
      }

      const result = await response.json();
      setProcessingSessionId(result.session_id);
      
    } catch (err) {
      setError(err.message);
      setActiveStep(2);
    } finally {
      setProcessing(false);
    }
  }, [sessionData]);

  const handleReset = useCallback(() => {
    setActiveStep(0);
    setSessionData(null);
    setProcessing(false);
    setError(null);
    setProcessingSessionId(null);
  }, []);

  const getStepContent = (step) => {
    switch (step) {
      case 0:
        return (
          <FileUploadZone
            onFileUpload={handleFileUpload}
            uploading={processing}
            disabled={processing}
          />
        );
      case 1:
        return (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', py: 4 }}>
            <LinearProgress sx={{ width: '100%', maxWidth: 400 }} />
            <Typography sx={{ ml: 2 }}>Analyzing file structure...</Typography>
          </Box>
        );
      case 2:
        return sessionData && (
          <Box>
            <StructureAnalysisDisplay 
              analysisData={sessionData.preview_data}
              onStartProcessing={handleStartProcessing}
              processing={processing}
            />
            <ProcessingConfigurationPanel
              recommendations={sessionData.preview_data.config_recommendations}
              onConfigChange={(config) => console.log('Config changed:', config)}
            />
          </Box>
        );
      case 3:
        return processingSessionId && (
          <ProcessingMonitor
            sessionId={processingSessionId}
            onComplete={handleReset}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          🤖 AI Training Center
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Enhanced with GPT-4 Intelligence & Smart Detection
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Upload supplier pricelists to enhance AI knowledge and conversation intelligence
        </Typography>
      </Box>

      {/* Progress Stepper */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Stepper activeStep={activeStep} alternativeLabel>
            {steps.map((label, index) => (
              <Step key={label}>
                <StepLabel
                  StepIconComponent={({ active, completed }) => (
                    <Box
                      sx={{
                        width: 40,
                        height: 40,
                        borderRadius: '50%',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        bgcolor: completed ? 'success.main' : active ? 'primary.main' : 'grey.300',
                        color: completed || active ? 'white' : 'text.secondary',
                      }}
                    >
                      {completed ? <CheckCircle /> : index + 1}
                    </Box>
                  )}
                >
                  {label}
                </StepLabel>
              </Step>
            ))}
          </Stepper>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Fade in={!!error}>
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            <Typography variant="h6">Processing Error</Typography>
            {error}
          </Alert>
        </Fade>
      )}

      {/* Main Content */}
      <Card>
        <CardContent sx={{ minHeight: 400 }}>
          {getStepContent(activeStep)}
        </CardContent>
      </Card>

      {/* Reset Button */}
      {activeStep > 0 && !processing && (
        <Box sx={{ textAlign: 'center', mt: 3 }}>
          <Button
            variant="outlined"
            onClick={handleReset}
            disabled={processing}
          >
            Start Over
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default EnhancedUploadCenter;
