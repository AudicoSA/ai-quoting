// frontend/src/components/TrainingCenter/Enhanced/EnhancedUploadCenter.jsx (UPDATE)
import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  Alert,
  LinearProgress,
  CircularProgress
} from '@mui/material';
import { CloudUpload, Psychology, CheckCircle } from '@mui/icons-material';

const EnhancedUploadCenter = () => {
  const [uploading, setUploading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    setError(null);
    setAnalysisResult(null);

    try {
      // Use our real enhanced API endpoint
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('http://localhost:8000/training-center/enhanced/upload/advanced', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult(result);
      
      // Show success popup
      alert(`🎉 SUCCESS! 
File: ${file.name}
Brands Detected: ${result.preview_data?.brands_detected?.length || 0}
Products Found: ${result.preview_data?.total_products || 0}
Analysis: ${result.preview_data?.structure_analysis?.analysis_method || 'Unknown'}
Ready to Process: ${result.processing_ready ? 'YES' : 'NO'}`);

    } catch (err) {
      console.error('Upload error:', err);
      setError(err.message);
      alert(`❌ Upload Error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper sx={{ p: 4, mb: 3, textAlign: 'center', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Psychology sx={{ fontSize: 64, mb: 2 }} />
        <Typography variant="h3" gutterBottom>
          🤖 Enhanced AI Training Center
        </Typography>
        <Typography variant="h6">
          Powered by GPT-4 Intelligence & Smart Detection
        </Typography>
      </Paper>

      {/* Features Alert */}
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          ✨ Enhanced Features Active
        </Typography>
        <Typography>
          🧠 GPT-4 Analysis • ⚡ Smart Column Detection • 📊 Multi-Brand Support • 🔍 Real-time Validation
        </Typography>
      </Alert>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          <Typography variant="h6">Upload Error</Typography>
          {error}
        </Alert>
      )}

      {/* Upload Zone */}
      <Paper
        sx={{
          border: 2,
          borderStyle: 'dashed',
          borderColor: uploading ? 'warning.main' : 'primary.main',
          p: 6,
          textAlign: 'center',
          cursor: uploading ? 'wait' : 'pointer',
          transition: 'all 0.3s ease',
          '&:hover': !uploading ? {
            borderColor: 'primary.dark',
            bgcolor: 'primary.light',
            transform: 'scale(1.02)'
          } : {}
        }}
        onClick={() => !uploading && document.getElementById('file-input').click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".xlsx,.csv"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          disabled={uploading}
        />
        
        {uploading ? (
          <CircularProgress size={64} sx={{ mb: 2 }} />
        ) : (
          <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        )}
        
        <Typography variant="h5" gutterBottom>
          {uploading ? 'Analyzing with GPT-4...' : 'Upload Supplier Pricelist'}
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {uploading 
            ? 'Using Smart Detection + GPT-4 Intelligence...' 
            : 'Drag & drop your Excel or CSV file, or click to browse'
          }
        </Typography>

        {!uploading && (
          <Button
            variant="contained"
            size="large"
            startIcon={<CloudUpload />}
          >
            Choose File
          </Button>
        )}

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress sx={{ mb: 1, height: 8, borderRadius: 4 }} />
            <Typography variant="body2" color="text.secondary">
              🤖 GPT-4 + Smart Detection analyzing your pricelist...
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Results Display */}
      {analysisResult && (
        <Alert severity="success" sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            <CheckCircle sx={{ mr: 1, verticalAlign: 'middle' }} />
            Analysis Complete!
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Brands Found:</strong> {analysisResult.preview_data?.brands_detected?.length || 0}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Products Detected:</strong> {analysisResult.preview_data?.total_products?.toLocaleString() || 0}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Analysis Method:</strong> {analysisResult.preview_data?.structure_analysis?.analysis_method || 'Unknown'}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Layout Type:</strong> {analysisResult.preview_data?.structure_analysis?.layout_type || 'Unknown'}
          </Typography>
          <Typography variant="body2">
            <strong>Ready to Process:</strong> {analysisResult.processing_ready ? '✅ YES' : '❌ NO'}
          </Typography>
        </Alert>
      )}

      {/* Status */}
      <Alert severity="success" sx={{ mt: 3 }}>
        <Typography variant="h6">🚀 Enhanced AI Training Center Ready!</Typography>
        <Typography>
          Backend running on port 8000 • GPT-4 Integration Active • Smart Detection Enabled
        </Typography>
      </Alert>
    </Box>
  );
};

export default EnhancedUploadCenter;
