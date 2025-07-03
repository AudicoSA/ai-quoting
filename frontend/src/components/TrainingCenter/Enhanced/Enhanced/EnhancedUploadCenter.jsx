// frontend/src/components/TrainingCenter/Enhanced/EnhancedUploadCenter.jsx (COMPLETE CORRECTED VERSION)
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
      const formData = new FormData();
      formData.append('file', file);
      formData.append('supplier_name', 'Nology');

      // *** CORRECTED: Use the working backend endpoint ***
      const response = await fetch('http://localhost:8000/api/v1/training-center/advanced-upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Upload result:', result);
      setAnalysisResult(result);
      
      // Show success popup with correct data structure
      alert(`🎉 AI ANALYSIS SUCCESS! 
File: ${file.name}
Brands Detected: ${result.preview?.brands_detected || 0}
Products Found: ${result.preview?.total_products || 0}
Structure: ${result.preview?.structure_type || 'Unknown'}
Status: ${result.status || 'Complete'}
Brands Found: ${result.preview?.brands_found?.join(', ') || 'None'}`);

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
      <Paper sx={{ 
        p: 4, 
        mb: 3, 
        textAlign: 'center', 
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', 
        color: 'white' 
      }}>
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
          🧠 AI Analysis • ⚡ Multi-Brand Detection • 📊 Horizontal Layout Support • 🔍 Real-time Processing
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
          accept=".xlsx,.xls"
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
          {uploading ? 'AI Analysis in Progress...' : 'Upload Supplier Pricelist'}
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {uploading 
            ? '🤖 Using AI-powered multi-brand detection...' 
            : 'Drag & drop your Excel file, or click to browse'
          }
        </Typography>

        {!uploading && (
          <Button
            variant="contained"
            size="large"
            startIcon={<CloudUpload />}
          >
            Choose Excel File
          </Button>
        )}

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress sx={{ mb: 1, height: 8, borderRadius: 4 }} />
            <Typography variant="body2" color="text.secondary">
              🤖 AI analyzing horizontal multi-brand layout...
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Results Display */}
      {analysisResult && (
        <Alert severity="success" sx={{ mt: 3 }}>
          <Typography variant="h6" gutterBottom>
            <CheckCircle sx={{ mr: 1, verticalAlign: 'middle' }} />
            AI Analysis Complete! 🎉
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Total Products:</strong> {analysisResult.preview?.total_products || 0}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Brands Detected:</strong> {analysisResult.preview?.brands_detected || 0}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Structure Type:</strong> {analysisResult.preview?.structure_type || 'Unknown'}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>Status:</strong> {analysisResult.status || 'Complete'}
          </Typography>
          {analysisResult.preview?.brands_found && (
            <Typography variant="body2" sx={{ mb: 1 }}>
              <strong>Brands Found:</strong> {analysisResult.preview.brands_found.join(', ')}
            </Typography>
          )}
          {analysisResult.preview?.sample_products && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Sample Products:</strong>
              </Typography>
              {analysisResult.preview.sample_products.slice(0, 3).map((product, index) => (
                <Typography key={index} variant="caption" display="block" sx={{ ml: 2 }}>
                  • {product.brand}: {product.stock_code} - R{product.price_excl_vat}
                </Typography>
              ))}
            </Box>
          )}
        </Alert>
      )}

      {/* Status */}
      <Alert severity="success" sx={{ mt: 3 }}>
        <Typography variant="h6">🚀 Enhanced AI Training Center Ready!</Typography>
        <Typography>
          Connected to backend API • AI Analysis Active • Multi-brand Support Enabled
        </Typography>
      </Alert>

      {/* Instructions */}
      <Paper sx={{ p: 3, mt: 3, bgcolor: 'grey.50' }}>
        <Typography variant="h6" gutterBottom>
          📋 How to Use:
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          1. Click "Choose Excel File" or drag & drop your pricelist
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          2. AI will automatically detect the layout and brands
        </Typography>
        <Typography variant="body2" sx={{ mb: 1 }}>
          3. View the analysis results below
        </Typography>
        <Typography variant="body2">
          4. Products are processed and ready for your AI assistant
        </Typography>
      </Paper>

      {/* Supported Formats */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          🎯 Supported Pricelist Formats:
        </Typography>
        <Typography variant="body2">
          • Horizontal multi-brand layouts (like Nology)
          • Single brand vertical layouts
          • Excel files (.xlsx, .xls)
          • Automatic brand detection: YEALINK, JABRA, DNAKE, CALL4TEL, LG, SHELLY, MIKROTIK, ZYXEL, and many more
        </Typography>
      </Alert>
    </Box>
  );
};

export default EnhancedUploadCenter;
