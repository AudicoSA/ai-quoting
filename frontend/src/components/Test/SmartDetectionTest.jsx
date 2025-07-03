// frontend/src/components/Test/SmartDetectionTest.jsx
import React, { useState } from 'react';
import { Box, Button, Typography, Alert, Card, CardContent } from '@mui/material';

const SmartDetectionTest = () => {
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);

  const runTest = async () => {
    setTesting(true);
    setTestResult(null);

    try {
      // Create a test file input
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.xlsx,.csv';
      
      input.onchange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('file', file);

        try {
          const response = await fetch('/api/training-center/upload/advanced', {
            method: 'POST',
            body: formData,
          });

          const result = await response.json();
          setTestResult(result);
        } catch (err) {
          setTestResult({ error: err.message });
        } finally {
          setTesting(false);
        }
      };

      input.click();
    } catch (err) {
      setTestResult({ error: err.message });
      setTesting(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        🧪 Smart Detection Test
      </Typography>

      <Button 
        variant="contained" 
        onClick={runTest}
        disabled={testing}
        sx={{ mb: 2 }}
      >
        {testing ? 'Testing...' : 'Test Upload with Nology Pricelist'}
      </Button>

      {testResult && (
        <Card>
          <CardContent>
            {testResult.error ? (
              <Alert severity="error">
                Error: {testResult.error}
              </Alert>
            ) : (
              <>
                <Alert severity={testResult.status === 'success' ? 'success' : 'error'}>
                  {testResult.message}
                </Alert>
                
                {testResult.preview_data && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="h6">Test Results:</Typography>
                    <Typography>Brands: {testResult.preview_data.brands_detected?.length || 0}</Typography>
                    <Typography>Products: {testResult.preview_data.total_products || 0}</Typography>
                    <Typography>Structure: {testResult.preview_data.structure_analysis?.layout_type || 'Unknown'}</Typography>
                    <Typography>Analysis Method: {testResult.preview_data.structure_analysis?.analysis_method || 'Unknown'}</Typography>
                    <Typography>Success Rate: {
                      testResult.preview_data.extraction_summary ? 
                      Math.round((testResult.preview_data.extraction_summary.successful_extractions / testResult.preview_data.total_products) * 100) : 0
                    }%</Typography>
                  </Box>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default SmartDetectionTest;
