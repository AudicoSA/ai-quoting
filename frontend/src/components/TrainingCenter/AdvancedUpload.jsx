// frontend/src/components/TrainingCenter/AdvancedUpload.jsx
import React, { useState } from 'react';
import { 
  Box, 
  Button, 
  Typography, 
  CircularProgress, 
  Alert,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow
} from '@mui/material';

const AdvancedUploadWithGPT4 = () => {
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [analysis, setAnalysis] = useState(null);
  const [error, setError] = useState(null);

  const handleFileUpload = async (selectedFile) => {
    setFile(selectedFile);
    setProcessing(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      const response = await fetch('/api/training-center/upload/advanced', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const result = await response.json();
      setAnalysis(result.preview_data);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const handleProcessConfirm = async () => {
    if (!analysis) return;

    setProcessing(true);
    try {
      const response = await fetch('/api/training-center/process/gpt4', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          products: analysis.sample_products,
          config: {
            markup_percentage: 10,
            vat_rate: 15,
            include_vat: false
          }
        }),
      });

      if (!response.ok) {
        throw new Error('Processing failed');
      }

      const result = await response.json();
      alert(`Success! Processed ${result.saved_count} products`);
      
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        🤖 AI Training Center - GPT-4 Enhanced
      </Typography>

      {/* File Upload */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <input
            type="file"
            accept=".xlsx,.csv"
            onChange={(e) => handleFileUpload(e.target.files[0])}
            disabled={processing}
          />
          {processing && (
            <Box sx={{ display: 'flex', alignItems: 'center', mt: 2 }}>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              <Typography>Analyzing with GPT-4...</Typography>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Analysis Results */}
      {analysis && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 GPT-4 Analysis Results
            </Typography>
            
            {/* Structure Info */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Structure Detected:</Typography>
              <Chip 
                label={analysis.structure_analysis.layout_type} 
                color="primary" 
                sx={{ mr: 1 }}
              />
            </Box>

            {/* Brands Detected */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Brands Found ({analysis.brands_detected.length}):</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                {analysis.brands_detected.map((brand, index) => (
                  <Chip key={index} label={brand} variant="outlined" />
                ))}
              </Box>
            </Box>

            {/* Extraction Summary */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1">Extraction Summary:</Typography>
              <Typography>✅ Successful: {analysis.extraction_summary.successful_extractions}</Typography>
              <Typography>❌ Failed: {analysis.extraction_summary.failed_extractions}</Typography>
              <Typography>📦 Total Products: {analysis.total_products}</Typography>
            </Box>

            {/* Sample Products Table */}
            <Typography variant="subtitle1" sx={{ mb: 1 }}>Sample Products:</Typography>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Brand</TableCell>
                  <TableCell>Product Code</TableCell>
                  <TableCell>Raw Price</TableCell>
                  <TableCell>Parsed Price</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {analysis.sample_products.map((product, index) => (
                  <TableRow key={index}>
                    <TableCell>{product.brand}</TableCell>
                    <TableCell>{product.product_code}</TableCell>
                    <TableCell>{product.raw_price}</TableCell>
                    <TableCell>
                      {product.parsed_price ? `R${product.parsed_price}` : 'Failed'}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {/* Process Button */}
            <Button
              variant="contained"
              color="primary"
              onClick={handleProcessConfirm}
              disabled={processing}
              sx={{ mt: 2 }}
            >
              {processing ? 'Processing...' : '✅ Process & Save All Products'}
            </Button>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default AdvancedUploadWithGPT4;
