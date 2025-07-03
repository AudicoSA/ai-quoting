import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Button,
  Grid,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ExpandMore,
  CheckCircle,
  Warning,
  Error,
  Info,
  PlayArrow,
  Visibility,
  Analytics
} from '@mui/icons-material';

const StructureAnalysisDisplay = ({ analysisData, onStartProcessing, processing }) => {
  const [expandedPanels, setExpandedPanels] = useState({
    overview: true,
    brands: true,
    samples: false,
    validation: true
  });

  const handlePanelChange = (panel) => (event, isExpanded) => {
    setExpandedPanels(prev => ({
      ...prev,
      [panel]: isExpanded
    }));
  };

  const {
    structure_analysis,
    brands_detected,
    total_products,
    sample_products,
    extraction_summary,
    processing_validation,
    file_info
  } = analysisData;

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success': return <CheckCircle color="success" />;
      case 'warning': return <Warning color="warning" />;
      case 'error': return <Error color="error" />;
      default: return <Info color="info" />;
    }
  };

  const getStatusColor = (rate) => {
    if (rate >= 90) return 'success';
    if (rate >= 70) return 'warning';
    return 'error';
  };

  return (
    <Box>
      {/* Header with Action Button */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h2">
          📊 Analysis Results
        </Typography>
        <Button
          variant="contained"
          size="large"
          startIcon={processing ? <Analytics /> : <PlayArrow />}
          onClick={() => onStartProcessing()}
          disabled={!processing_validation.ready_to_process || processing}
          color={processing_validation.ready_to_process ? 'primary' : 'warning'}
        >
          {processing ? 'Starting...' : 'Start Processing'}
        </Button>
      </Box>

      {/* Overall Status Alert */}
      <Alert 
        severity={processing_validation.ready_to_process ? 'success' : 'warning'} 
        sx={{ mb: 3 }}
        icon={getStatusIcon(processing_validation.ready_to_process ? 'success' : 'warning')}
      >
        <Typography variant="h6">
          {processing_validation.ready_to_process 
            ? '✅ Ready for Processing' 
            : '⚠️ Issues Detected'
          }
        </Typography>
        <Typography>
          {processing_validation.ready_to_process
            ? `File structure recognized. Found ${brands_detected.length} brands with ${total_products} total products.`
            : `${processing_validation.issues.length} issues found. Review before processing.`
          }
        </Typography>
      </Alert>

      {/* Quick Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="primary">{brands_detected.length}</Typography>
              <Typography variant="subtitle1">Brands Detected</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="info.main">{total_products.toLocaleString()}</Typography>
              <Typography variant="subtitle1">Total Products</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography 
                variant="h3" 
                color={getStatusColor(extraction_summary.success_rate)}
              >
                {extraction_summary.success_rate}%
              </Typography>
              <Typography variant="subtitle1">Success Rate</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h3" color="secondary">{file_info.size_mb}</Typography>
              <Typography variant="subtitle1">MB File Size</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Analysis Sections */}
      
      {/* Structure Overview */}
      <Accordion 
        expanded={expandedPanels.overview} 
        onChange={handlePanelChange('overview')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">🏗️ Structure Analysis</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">File Information</Typography>
              <Box sx={{ mt: 1 }}>
                <Chip label={`Format: ${file_info.format}`} sx={{ mr: 1 }} />
                <Chip label={`Layout: ${structure_analysis.layout_type}`} color="primary" sx={{ mr: 1 }} />
                <Chip label={`Method: ${structure_analysis.analysis_method}`} color="secondary" />
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2">Quality Indicators</Typography>
              <Box sx={{ mt: 1 }}>
                {structure_analysis.gpt4_validation && (
                  <Chip 
                    label={`GPT-4: ${structure_analysis.gpt4_validation}`} 
                    color={structure_analysis.gpt4_validation === 'confirmed' ? 'success' : 'warning'}
                    sx={{ mr: 1 }}
                  />
                )}
                {structure_analysis.quality_score && (
                  <Chip 
                    label={`Quality: ${structure_analysis.quality_score}/10`} 
                    color={structure_analysis.quality_score >= 8 ? 'success' : 'warning'}
                  />
                )}
              </Box>
            </Grid>
          </Grid>
        </AccordionDetails>
      </Accordion>

      {/* Brands Detected */}
      <Accordion 
        expanded={expandedPanels.brands} 
        onChange={handlePanelChange('brands')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">🏷️ Brands Detected ({brands_detected.length})</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {brands_detected.map((brand, index) => (
              <Chip 
                key={index} 
                label={brand} 
                color="primary" 
                variant="outlined"
                size="medium"
              />
            ))}
          </Box>
          {brands_detected.length === 0 && (
            <Alert severity="warning">
              No brands detected. This may indicate an unsupported file format.
            </Alert>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Sample Products */}
      <Accordion 
        expanded={expandedPanels.samples} 
        onChange={handlePanelChange('samples')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">🔍 Sample Products Preview</Typography>
          <Tooltip title="View sample extracted products">
            <IconButton size="small">
              <Visibility />
            </IconButton>
          </Tooltip>
        </AccordionSummary>
        <AccordionDetails>
          {sample_products.length > 0 ? (
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Brand</TableCell>
                  <TableCell>Product Code</TableCell>
                  <TableCell>Raw Price</TableCell>
                  <TableCell>Parsed Price</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {sample_products.map((product, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Chip label={product.brand} size="small" color="primary" />
                    </TableCell>
                    <TableCell>{product.product_code}</TableCell>
                    <TableCell>{product.raw_price}</TableCell>
                    <TableCell>
                      {product.parsed_price 
                        ? `R${product.parsed_price.toFixed(2)}` 
                        : '-'
                      }
                    </TableCell>
                    <TableCell>
                      {product.parsed_price ? (
                        <CheckCircle color="success" fontSize="small" />
                      ) : (
                        <Error color="error" fontSize="small" />
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <Alert severity="info">
              No sample products available. Processing may still work if structure is valid.
            </Alert>
          )}
        </AccordionDetails>
      </Accordion>

      {/* Processing Validation */}
      <Accordion 
        expanded={expandedPanels.validation} 
        onChange={handlePanelChange('validation')}
      >
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Typography variant="h6">✅ Processing Validation</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ space: 2 }}>
            {/* Issues */}
            {processing_validation.issues.length > 0 && (
              <Alert severity="error" sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Issues Found:</Typography>
                <ul>
                  {processing_validation.issues.map((issue, index) => (
                    <li key={index}>{issue}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Warnings */}
            {processing_validation.warnings.length > 0 && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                <Typography variant="subtitle2">Warnings:</Typography>
                <ul>
                  {processing_validation.warnings.map((warning, index) => (
                    <li key={index}>{warning}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* Recommendations */}
            {processing_validation.recommendations.length > 0 && (
              <Alert severity="info">
                <Typography variant="subtitle2">Recommendations:</Typography>
                <ul>
                  {processing_validation.recommendations.map((rec, index) => (
                    <li key={index}>{rec}</li>
                  ))}
                </ul>
              </Alert>
            )}

            {/* All Good */}
            {processing_validation.issues.length === 0 && processing_validation.warnings.length === 0 && (
              <Alert severity="success">
                <Typography variant="subtitle2">All validation checks passed!</Typography>
                <Typography>Your file is ready for processing.</Typography>
              </Alert>
            )}
          </Box>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default StructureAnalysisDisplay;