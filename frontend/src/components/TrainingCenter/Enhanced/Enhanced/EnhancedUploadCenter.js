// frontend/src/components/TrainingCenter/Enhanced/EnhancedUploadCenter.js
import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Card,
  CardContent,
  Grid,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  CircularProgress
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  Error,
  AutoAwesome,
  Business,
  Inventory
} from '@mui/icons-material';

const EnhancedUploadCenter = () => {
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        setUploadFile(file);
        setError(null);
        setUploadResult(null);
      } else {
        setError('Please select an Excel file (.xlsx or .xls)');
        setUploadFile(null);
      }
    }
  };

  const handleUpload = async () => {
    if (!uploadFile) return;

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);

      const response = await fetch('/api/v1/training-center/enhanced/upload/advanced', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok && result.status === 'analysis_complete') {
        setUploadResult(result);
      } else {
        setError(result.detail || 'Upload failed');
      }
    } catch (err) {
      setError(`Upload error: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const resetUpload = () => {
    setUploadFile(null);
    setUploadResult(null);
    setError(null);
    setUploading(false);
  };

  return (
    <Box>
      {/* Upload Section */}
      <Paper sx={{ p: 4, mb: 3 }}>
        <Box sx={{ textAlign: 'center', mb: 4 }}>
          <AutoAwesome sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
          <Typography variant="h4" gutterBottom>
            🚀 Enhanced AI Training Center
          </Typography>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            Advanced pricelist processing with AI-powered brand detection
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Upload your Excel pricelists - supports Nology format and 50+ other layouts
          </Typography>
        </Box>

        {/* File Upload Area */}
        {!uploadResult && (
          <Box>
            <Box
              sx={{
                border: '2px dashed',
                borderColor: uploadFile ? 'success.main' : 'grey.300',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                backgroundColor: uploadFile ? 'success.50' : 'grey.50',
                cursor: 'pointer',
                transition: 'all 0.3s',
                '&:hover': {
                  borderColor: 'primary.main',
                  backgroundColor: 'primary.50'
                }
              }}
              onClick={() => document.getElementById('file-input').click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".xlsx,.xls"
                style={{ display: 'none' }}
                onChange={handleFileSelect}
              />
              
              {uploadFile ? (
                <Box>
                  <CheckCircle sx={{ fontSize: 60, color: 'success.main', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    📄 {uploadFile.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {(uploadFile.size / 1024 / 1024).toFixed(2)} MB
                  </Typography>
                  <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', gap: 2 }}>
                    <Button
                      variant="contained"
                      onClick={handleUpload}
                      disabled={uploading}
                      startIcon={uploading ? <CircularProgress size={20} /> : <CloudUpload />}
                    >
                      {uploading ? 'Processing...' : 'Process Pricelist'}
                    </Button>
                    <Button variant="outlined" onClick={resetUpload}>
                      Choose Different File
                    </Button>
                  </Box>
                </Box>
              ) : (
                <Box>
                  <CloudUpload sx={{ fontSize: 60, color: 'grey.400', mb: 2 }} />
                  <Typography variant="h6" gutterBottom>
                    Drop your Excel pricelist here or click to browse
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Supports: .xlsx, .xls files
                  </Typography>
                  <Button variant="contained" sx={{ mt: 2 }}>
                    Select Pricelist File
                  </Button>
                </Box>
              )}
            </Box>

            {uploading && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="body2" gutterBottom>
                  🧠 AI is analyzing your pricelist structure...
                </Typography>
                <LinearProgress />
              </Box>
            )}
          </Box>
        )}

        {/* Error Display */}
        {error && (
          <Alert severity="error" sx={{ mt: 3 }} onClose={() => setError(null)}>
            <Typography variant="h6">Upload Failed</Typography>
            {error}
          </Alert>
        )}
      </Paper>

      {/* Results Section */}
      {uploadResult && (
        <Paper sx={{ p: 4 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
            <CheckCircle sx={{ color: 'success.main', mr: 2, fontSize: 40 }} />
            <Box>
              <Typography variant="h5" gutterBottom>
                ✅ Analysis Complete!
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {uploadResult.message}
              </Typography>
            </Box>
          </Box>

          {/* Analysis Summary */}
          <Grid container spacing={3} sx={{ mb: 4 }}>
            <Grid item xs={12} md={4}>
              <Card sx={{ textAlign: 'center', p: 2 }}>
                <Inventory sx={{ fontSize: 40, color: 'primary.main', mb: 1 }} />
                <Typography variant="h4" color="primary">
                  {uploadResult.preview_data?.total_products || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Products Detected
                </Typography>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card sx={{ textAlign: 'center', p: 2 }}>
                <Business sx={{ fontSize: 40, color: 'secondary.main', mb: 1 }} />
                <Typography variant="h4" color="secondary">
                  {uploadResult.preview_data?.brands_detected?.length || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Brands Found
                </Typography>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={4}>
              <Card sx={{ textAlign: 'center', p: 2 }}>
                <AutoAwesome sx={{ fontSize: 40, color: 'success.main', mb: 1 }} />
                <Typography variant="h4" color="success.main">
                  {uploadResult.preview_data?.extraction_summary?.success_rate || 0}%
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Success Rate
                </Typography>
              </Card>
            </Grid>
          </Grid>

          {/* Brands Detected */}
          {uploadResult.preview_data?.brands_detected?.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                🏷️ Brands Detected:
              </Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {uploadResult.preview_data.brands_detected.map((brand, index) => (
                  <Chip
                    key={index}
                    label={brand}
                    color="primary"
                    variant="outlined"
                  />
                ))}
              </Box>
            </Box>
          )}

          {/* Sample Products */}
          {uploadResult.preview_data?.sample_products?.length > 0 && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                📦 Sample Products Extracted:
              </Typography>
              <List>
                {uploadResult.preview_data.sample_products.slice(0, 5).map((product, index) => (
                  <React.Fragment key={index}>
                    <ListItem>
                      <ListItemText
                        primary={`${product.brand} - ${product.stock_code}`}
                        secondary={
                          product.price_excl_vat 
                            ? `R${product.price_excl_vat} (excl. VAT)`
                            : 'Price on request'
                        }
                      />
                    </ListItem>
                    {index < uploadResult.preview_data.sample_products.slice(0, 5).length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </Box>
          )}

          {/* Analysis Details */}
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              <strong>Structure Analysis:</strong> {uploadResult.preview_data?.structure_analysis?.layout_type || 'Standard'}
              <br />
              <strong>Processing Method:</strong> {uploadResult.preview_data?.structure_analysis?.analysis_method || 'Enhanced AI Detection'}
              <br />
              <strong>File Size:</strong> {uploadResult.preview_data?.file_info?.size_mb || 'Unknown'} MB
            </Typography>
          </Alert>

          {/* Action Buttons */}
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
            <Button
              variant="contained"
              size="large"
              onClick={resetUpload}
            >
              Process Another Pricelist
            </Button>
            <Button
              variant="outlined"
              size="large"
            >
              View Training Progress
            </Button>
          </Box>
        </Paper>
      )}

      {/* Features Info */}
      <Paper sx={{ p: 3, mt: 3, bgcolor: 'background.default' }}>
        <Typography variant="h6" gutterBottom>
          🎯 Enhanced AI Features:
        </Typography>
        <Grid container spacing={2}>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              ✅ <strong>Multi-Brand Detection:</strong> Automatically identifies brands like Nology format
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              ✅ <strong>Smart Price Parsing:</strong> Handles "P.O.R", VAT calculations, and pricing logic
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              ✅ <strong>Format Intelligence:</strong> Supports 50+ different pricelist layouts
            </Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="body2" sx={{ mb: 1 }}>
              ✅ <strong>Real-time Analysis:</strong> Instant structure detection and validation
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              ✅ <strong>Quality Scoring:</strong> Success rates and confidence metrics
            </Typography>
            <Typography variant="body2" sx={{ mb: 1 }}>
              ✅ <strong>Chat Enhancement:</strong> Improves AI conversation intelligence
            </Typography>
          </Grid>
        </Grid>
      </Paper>
    </Box>
  );
};

export default EnhancedUploadCenter;
