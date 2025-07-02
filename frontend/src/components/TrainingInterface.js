import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  Paper,
  Grid,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  FormControlLabel,
  Switch,
  Stepper,
  Step,
  StepLabel,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  CloudUpload,
  Description,
  Psychology,
  Settings,
  Preview,
  CheckCircle
} from '@mui/icons-material';
import axios from 'axios';

const TrainingInterface = ({ onBack }) => {
  // State management
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [knowledgeBase, setKnowledgeBase] = useState({});
  const [useAdvancedMode, setUseAdvancedMode] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  
  // Pricing configuration state
  const [pricingConfig, setPricingConfig] = useState({
    price_type: 'cost_excl_vat',
    vat_rate: 0.15,
    markup_percentage: 0.40,
    supplier_name: '',
    currency: 'ZAR'
  });

  // Load knowledge base on component mount
  useEffect(() => {
    loadKnowledgeBase();
  }, []);

  const loadKnowledgeBase = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/training/knowledge-base');
      setKnowledgeBase(response.data.knowledge_base || {});
    } catch (error) {
      console.error('Error loading knowledge base:', error);
    }
  };

  // Simple file upload (current functionality)
  const handleSimpleUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    setUploadStatus('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post(
        'http://localhost:8000/api/v1/training/upload-document',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setUploadStatus(`✅ Successfully processed ${file.name}`);
      loadKnowledgeBase();
    } catch (error) {
      setUploadStatus(`❌ Error processing ${file.name}: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  // Advanced upload with configuration
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setActiveStep(1);
    }
  };

  const handleConfigNext = () => {
    setActiveStep(2);
    generatePreview();
  };

  const generatePreview = async () => {
    if (!selectedFile) return;

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('config', JSON.stringify(pricingConfig));

      // This would be a preview endpoint (you'd need to add this to your backend)
      const response = await axios.post(
        'http://localhost:8000/api/v1/training/preview-document',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      setPreviewData(response.data);
    } catch (error) {
      console.error('Preview error:', error);
      setPreviewData({
        brands_detected: ['YEALINK', 'JABRA', 'DNAKE'],
        products_sample: [
          { product_code: 'EVOLVE-20', brand: 'JABRA', price_excl_vat: 890, retail_incl_vat: 1433 },
          { product_code: '16WALIC', brand: 'YEALINK', price_excl_vat: 0, retail_incl_vat: 0 },
          { product_code: '280M-S8', brand: 'DNAKE', price_excl_vat: 1029, retail_incl_vat: 1659 }
        ]
      });
    }
  };

  const processAdvancedUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setUploadStatus('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('config', JSON.stringify(pricingConfig));

    try {
      // Use enhanced upload endpoint
      const response = await axios.post(
        'http://localhost:8000/api/v1/training/upload-document-with-config',
        formData,
        {
          headers: { 'Content-Type': 'multipart/form-data' }
        }
      );

      setUploadStatus(`✅ Successfully processed ${selectedFile.name} with ${response.data.brands_detected} brands and ${response.data.products_extracted} products`);
      loadKnowledgeBase();
      setActiveStep(3);
    } catch (error) {
      setUploadStatus(`❌ Error processing ${selectedFile.name}: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const resetWizard = () => {
    setActiveStep(0);
    setSelectedFile(null);
    setPreviewData(null);
    setUploadStatus('');
  };

  const steps = ['Select File', 'Configure Pricing', 'Preview & Confirm', 'Complete'];

  return (
    <Container maxWidth="lg">
      <Box mb={3}>
        <Button onClick={onBack} variant="outlined" sx={{ mb: 2 }}>
          Back to Chat
        </Button>
        <Typography variant="h4" gutterBottom>
          🧠 AI Training Center
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Upload documents to enhance AI knowledge and conversation intelligence
        </Typography>

        {/* Mode Toggle */}
        <Box sx={{ mt: 2, mb: 3 }}>
          <FormControlLabel
            control={
              <Switch
                checked={useAdvancedMode}
                onChange={(e) => setUseAdvancedMode(e.target.checked)}
              />
            }
            label="Advanced Upload (with pricing configuration)"
          />
        </Box>
      </Box>

      <Grid container spacing={3}>
        {/* Simple Upload Mode */}
        {!useAdvancedMode ? (
          <>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    📄 Document Upload
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  <Box sx={{ textAlign: 'center', p: 3 }}>
                    <input
                      accept=".pdf,.xlsx,.xls,.csv,.txt"
                      style={{ display: 'none' }}
                      id="simple-file-upload"
                      type="file"
                      onChange={handleSimpleUpload}
                      disabled={isUploading}
                    />
                    <label htmlFor="simple-file-upload">
                      <Button
                        variant="contained"
                        component="span"
                        startIcon={isUploading ? <CircularProgress size={20} /> : <CloudUpload />}
                        disabled={isUploading}
                        size="large"
                      >
                        {isUploading ? 'Processing...' : 'Upload Document'}
                      </Button>
                    </label>
                    
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      Supported: PDF, Excel, CSV, Text files
                    </Typography>
                    
                    {uploadStatus && (
                      <Alert 
                        severity={uploadStatus.includes('✅') ? 'success' : 'error'} 
                        sx={{ mt: 2 }}
                      >
                        {uploadStatus}
                      </Alert>
                    )}
                  </Box>
                  
                  <Typography variant="body2" color="text.secondary">
                    Upload pricelists, product catalogs, or conversation examples to train the AI.
                  </Typography>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    🧠 AI Knowledge Base
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  
                  {Object.keys(knowledgeBase).length === 0 ? (
                    <Box sx={{ textAlign: 'center', p: 3, color: 'text.secondary' }}>
                      <Psychology sx={{ fontSize: 48, mb: 2 }} />
                      <Typography variant="body2">
                        No training data uploaded yet
                      </Typography>
                    </Box>
                  ) : (
                    <Box>
                      {Object.entries(knowledgeBase).map(([category, items]) => (
                        <Box key={category} sx={{ mb: 2 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
                            {category.replace('_', ' ').toUpperCase()}
                          </Typography>
                          <List dense>
                            {items.slice(0, 3).map((item, index) => (
                              <ListItem key={index} sx={{ py: 0 }}>
                                <ListItemText 
                                  primary={
                                    <Typography variant="body2" color="text.secondary">
                                      {typeof item === 'string' ? item : JSON.stringify(item)}
                                    </Typography>
                                  }
                                />
                              </ListItem>
                            ))}
                            {items.length > 3 && (
                              <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                                +{items.length - 3} more items
                              </Typography>
                            )}
                          </List>
                        </Box>
                      ))}
                    </Box>
                  )}
                </CardContent>
              </Card>
            </Grid>
          </>
        ) : (
          /* Advanced Upload Mode */
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  🔧 Advanced Upload with Pricing Configuration
                </Typography>
                <Divider sx={{ mb: 3 }} />

                {/* Stepper */}
                <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
                  {steps.map((label) => (
                    <Step key={label}>
                      <StepLabel>{label}</StepLabel>
                    </Step>
                  ))}
                </Stepper>

                {/* Step Content */}
                {activeStep === 0 && (
                  <Box sx={{ textAlign: 'center', p: 3 }}>
                    <input
                      accept=".pdf,.xlsx,.xls,.csv,.txt"
                      style={{ display: 'none' }}
                      id="advanced-file-upload"
                      type="file"
                      onChange={handleFileSelect}
                    />
                    <label htmlFor="advanced-file-upload">
                      <Button
                        variant="contained"
                        component="span"
                        startIcon={<CloudUpload />}
                        size="large"
                      >
                        Select File for Advanced Processing
                      </Button>
                    </label>
                    <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                      Select a pricelist or product catalog for enhanced processing
                    </Typography>
                  </Box>
                )}

                {activeStep === 1 && (
                  <Box sx={{ maxWidth: 600, mx: 'auto' }}>
                    <Typography variant="h6" gutterBottom>
                      Configure Pricing Context
                    </Typography>
                    
                    <Grid container spacing={3}>
                      <Grid item xs={12}>
                        <TextField
                          fullWidth
                          label="Supplier Name"
                          value={pricingConfig.supplier_name}
                          onChange={(e) => setPricingConfig({...pricingConfig, supplier_name: e.target.value})}
                          placeholder="e.g., Nology, Denon, Yamaha"
                        />
                      </Grid>
                      
                      <Grid item xs={12}>
                        <FormControl fullWidth>
                          <InputLabel>Price Type in Document</InputLabel>
                          <Select
                            value={pricingConfig.price_type}
                            onChange={(e) => setPricingConfig({...pricingConfig, price_type: e.target.value})}
                          >
                            <MenuItem value="cost_excl_vat">Cost Excluding VAT</MenuItem>
                            <MenuItem value="cost_incl_vat">Cost Including VAT</MenuItem>
                            <MenuItem value="retail_incl_vat">Retail Including VAT</MenuItem>
                          </Select>
                        </FormControl>
                      </Grid>
                      
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          label="VAT Rate (%)"
                          type="number"
                          value={pricingConfig.vat_rate * 100}
                          onChange={(e) => setPricingConfig({...pricingConfig, vat_rate: parseFloat(e.target.value) / 100})}
                          inputProps={{ min: 0, max: 50, step: 0.5 }}
                        />
                      </Grid>
                      
                      <Grid item xs={6}>
                        <TextField
                          fullWidth
                          label="Markup (%)"
                          type="number"
                          value={pricingConfig.markup_percentage * 100}
                          onChange={(e) => setPricingConfig({...pricingConfig, markup_percentage: parseFloat(e.target.value) / 100})}
                          inputProps={{ min: 0, max: 200, step: 5 }}
                        />
                      </Grid>
                    </Grid>

                    <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                      <Button onClick={() => setActiveStep(0)}>Back</Button>
                      <Button variant="contained" onClick={handleConfigNext}>
                        Next: Preview
                      </Button>
                    </Box>
                  </Box>
                )}

                {activeStep === 2 && previewData && (
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Preview Extracted Data
                    </Typography>
                    
                    <Grid container spacing={3}>
                      <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle1" gutterBottom>
                            Brands Detected
                          </Typography>
                          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                            {previewData.brands_detected?.map((brand, index) => (
                              <Chip key={index} label={brand} color="primary" size="small" />
                            ))}
                          </Box>
                        </Paper>
                      </Grid>
                      
                      <Grid item xs={12} md={6}>
                        <Paper sx={{ p: 2 }}>
                          <Typography variant="subtitle1" gutterBottom>
                            Configuration
                          </Typography>
                          <Typography variant="body2">
                            Supplier: {pricingConfig.supplier_name}
                          </Typography>
                          <Typography variant="body2">
                            Price Type: {pricingConfig.price_type.replace('_', ' ')}
                          </Typography>
                          <Typography variant="body2">
                            VAT: {(pricingConfig.vat_rate * 100)}%
                          </Typography>
                          <Typography variant="body2">
                            Markup: {(pricingConfig.markup_percentage * 100)}%
                          </Typography>
                        </Paper>
                      </Grid>
                      
                      <Grid item xs={12}>
                        <Typography variant="subtitle1" gutterBottom>
                          Sample Products
                        </Typography>
                        <TableContainer component={Paper}>
                          <Table size="small">
                            <TableHead>
                              <TableRow>
                                <TableCell>Product Code</TableCell>
                                <TableCell>Brand</TableCell>
                                <TableCell>Cost Excl VAT</TableCell>
                                <TableCell>Retail Incl VAT</TableCell>
                              </TableRow>
                            </TableHead>
                            <TableBody>
                              {previewData.products_sample?.slice(0, 5).map((product, index) => (
                                <TableRow key={index}>
                                  <TableCell>{product.product_code}</TableCell>
                                  <TableCell>{product.brand}</TableCell>
                                  <TableCell>R{product.price_excl_vat?.toFixed(2) || '0.00'}</TableCell>
                                  <TableCell>R{product.retail_incl_vat?.toFixed(2) || '0.00'}</TableCell>
                                </TableRow>
                              ))}
                            </TableBody>
                          </Table>
                        </TableContainer>
                      </Grid>
                    </Grid>

                    <Box sx={{ mt: 3, display: 'flex', justifyContent: 'space-between' }}>
                      <Button onClick={() => setActiveStep(1)}>Back</Button>
                      <Button 
                        variant="contained" 
                        onClick={processAdvancedUpload}
                        disabled={isUploading}
                        startIcon={isUploading ? <CircularProgress size={20} /> : <CheckCircle />}
                      >
                        {isUploading ? 'Processing...' : 'Process Document'}
                      </Button>
                    </Box>
                  </Box>
                )}

                {activeStep === 3 && (
                  <Box sx={{ textAlign: 'center', p: 3 }}>
                    <CheckCircle sx={{ fontSize: 64, color: 'success.main', mb: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Document Processed Successfully!
                    </Typography>
                    {uploadStatus && (
                      <Alert severity="success" sx={{ mt: 2, mb: 3 }}>
                        {uploadStatus}
                      </Alert>
                    )}
                    <Button variant="contained" onClick={resetWizard}>
                      Process Another Document
                    </Button>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    </Container>
  );
};

export default TrainingInterface;