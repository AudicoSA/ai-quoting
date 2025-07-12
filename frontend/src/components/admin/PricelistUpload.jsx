import React, { useState, useCallback, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Switch,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  CloudUpload,
  InsertDriveFile,
  CheckCircle,
  Error,
  Delete,
  Settings,
  Preview,
  Assessment
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import axios from 'axios';

const PricelistUpload = () => {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [configDialog, setConfigDialog] = useState(false);
  const [previewDialog, setPreviewDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [supplierConfig, setSupplierConfig] = useState({
    name: '',
    markup_percentage: 20,
    vat_included: false,
    default_currency: 'ZAR',
    processing_notes: ''
  });
  const [uploadResults, setUploadResults] = useState([]);
  const [previewData, setPreviewData] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    const newFiles = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending',
      progress: 0,
      supplier: '',
      results: null,
      error: null
    }));
    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/pdf': ['.pdf']
    },
    multiple: true
  });

  const removeFile = (fileId) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const configureSupplier = (file) => {
    setSelectedFile(file);
    setSupplierConfig({
      name: file.supplier || file.file.name.replace(/\.(xlsx|xls|pdf)$/i, ''),
      markup_percentage: 20,
      vat_included: false,
      default_currency: 'ZAR',
      processing_notes: ''
    });
    setConfigDialog(true);
  };

  const saveSupplierConfig = () => {
    if (selectedFile) {
      setFiles(prev => prev.map(f => 
        f.id === selectedFile.id 
          ? { ...f, supplier: supplierConfig.name, config: supplierConfig }
          : f
      ));
    }
    setConfigDialog(false);
    setSelectedFile(null);
  };

  const previewFile = async (file) => {
    setSelectedFile(file);
    setPreviewDialog(true);
    
    try {
      const formData = new FormData();
      formData.append('file', file.file);
      formData.append('preview_only', 'true');

      const response = await axios.post('/api/admin/preview-pricelist', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      setPreviewData(response.data);
    } catch (error) {
      console.error('Preview failed:', error);
      setPreviewData({ error: 'Failed to preview file' });
    }
  };

  const uploadFiles = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setUploadResults([]);

    for (const fileItem of files) {
      if (fileItem.status !== 'pending') continue;

      try {
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id 
            ? { ...f, status: 'uploading', progress: 0 }
            : f
        ));

        const formData = new FormData();
        formData.append('file', fileItem.file);
        formData.append('supplier_name', fileItem.supplier || fileItem.file.name);
        
        if (fileItem.config) {
          formData.append('config', JSON.stringify(fileItem.config));
        }

        const response = await axios.post('/api/admin/upload-pricelist', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          onUploadProgress: (progressEvent) => {
            const progress = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setFiles(prev => prev.map(f => 
              f.id === fileItem.id 
                ? { ...f, progress }
                : f
            ));
          }
        });

        setFiles(prev => prev.map(f => 
          f.id === fileItem.id 
            ? { 
                ...f, 
                status: 'completed', 
                progress: 100,
                results: response.data 
              }
            : f
        ));

        setUploadResults(prev => [...prev, {
          file: fileItem.file.name,
          supplier: fileItem.supplier,
          ...response.data
        }]);

      } catch (error) {
        setFiles(prev => prev.map(f => 
          f.id === fileItem.id 
            ? { 
                ...f, 
                status: 'error', 
                error: error.response?.data?.detail || error.message 
              }
            : f
        ));
      }
    }

    setUploading(false);
  };

  const getFileIcon = (filename) => {
    if (filename.toLowerCase().endsWith('.pdf')) {
      return <InsertDriveFile style={{ color: '#d32f2f' }} />;
    }
    return <InsertDriveFile style={{ color: '#2e7d32' }} />;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'error': return 'error';
      case 'uploading': return 'info';
      default: return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        📋 Pricelist Upload Center
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload Excel (.xlsx, .xls) and PDF pricelists from your suppliers. 
        The AI will automatically parse products, prices, and specifications.
      </Typography>

      <Paper
        {...getRootProps()}
        sx={{
          p: 4,
          mb: 3,
          border: '2px dashed',
          borderColor: isDragActive ? 'primary.main' : 'grey.300',
          bgcolor: isDragActive ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          textAlign: 'center',
          transition: 'all 0.2s ease'
        }}
      >
        <input {...getInputProps()} />
        <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
        <Typography variant="h6" gutterBottom>
          {isDragActive ? 'Drop files here...' : 'Drag & drop pricelists here'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Supports Excel (.xlsx, .xls) and PDF files
        </Typography>
        <Button
          variant="contained"
          sx={{ mt: 2 }}
          startIcon={<CloudUpload />}
        >
          Browse Files
        </Button>
      </Paper>

      {files.length > 0 && (
        <Paper sx={{ mb: 3 }}>
          <Box sx={{ p: 2, borderBottom: 1, borderColor: 'divider' }}>
            <Typography variant="h6">
              Files Ready for Processing ({files.length})
            </Typography>
          </Box>
          
          <List>
            {files.map((fileItem) => (
              <ListItem key={fileItem.id} divider>
                <ListItemIcon>
                  {getFileIcon(fileItem.file.name)}
                </ListItemIcon>
                
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body1">
                        {fileItem.file.name}
                      </Typography>
                      <Chip
                        label={fileItem.status}
                        color={getStatusColor(fileItem.status)}
                        size="small"
                      />
                      {fileItem.supplier && (
                        <Chip
                          label={`Supplier: ${fileItem.supplier}`}
                          variant="outlined"
                          size="small"
                        />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Size: {(fileItem.file.size / 1024 / 1024).toFixed(2)} MB
                      </Typography>
                      
                      {fileItem.status === 'uploading' && (
                        <LinearProgress
                          variant="determinate"
                          value={fileItem.progress}
                          sx={{ mt: 1 }}
                        />
                      )}
                      
                      {fileItem.error && (
                        <Alert severity="error" sx={{ mt: 1 }}>
                          {fileItem.error}
                        </Alert>
                      )}
                      
                      {fileItem.results && (
                        <Box sx={{ mt: 1 }}>
                          <Typography variant="body2" color="success.main">
                            ✅ Processed {fileItem.results.total_products} products 
                            from {fileItem.results.brands_detected} brands
                          </Typography>
                        </Box>
                      )}
                    </Box>
                  }
                />
                
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <IconButton
                    onClick={() => previewFile(fileItem)}
                    disabled={fileItem.status === 'uploading'}
                  >
                    <Preview />
                  </IconButton>
                  
                  <IconButton
                    onClick={() => configureSupplier(fileItem)}
                    disabled={fileItem.status === 'uploading'}
                  >
                    <Settings />
                  </IconButton>
                  
                  <IconButton
                    onClick={() => removeFile(fileItem.id)}
                    disabled={fileItem.status === 'uploading'}
                    color="error"
                  >
                    <Delete />
                  </IconButton>
                </Box>
              </ListItem>
            ))}
          </List>
          
          <Box sx={{ p: 2, display: 'flex', gap: 2 }}>
            <Button
              variant="contained"
              onClick={uploadFiles}
              disabled={uploading || files.every(f => f.status !== 'pending')}
              startIcon={<CloudUpload />}
            >
              {uploading ? 'Processing...' : 'Process All Files'}
            </Button>
            
            <Button
              variant="outlined"
              onClick={() => setFiles([])}
              disabled={uploading}
            >
              Clear All
            </Button>
          </Box>
        </Paper>
      )}

      {uploadResults.length > 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            📊 Processing Results
          </Typography>
          
          <Grid container spacing={2}>
            {uploadResults.map((result, index) => (
              <Grid item xs={12} md={6} key={index}>
                <Card>
                  <CardContent>
                    <Typography variant="h6" gutterBottom>
                      {result.file}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Supplier: {result.supplier}
                    </Typography>
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="body2">
                        ✅ Products: {result.total_products}
                      </Typography>
                      <Typography variant="body2">
                        🏢 Brands: {result.brands_detected}
                      </Typography>
                      <Typography variant="body2">
                        📋 Format: {result.structure_type}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Paper>
      )}

      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Configure Supplier Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Supplier Name"
              value={supplierConfig.name}
              onChange={(e) => setSupplierConfig(prev => ({ ...prev, name: e.target.value }))}
              fullWidth
            />
            
            <TextField
              label="Markup Percentage"
              type="number"
              value={supplierConfig.markup_percentage}
              onChange={(e) => setSupplierConfig(prev => ({ ...prev, markup_percentage: parseFloat(e.target.value) }))}
              InputProps={{ endAdornment: '%' }}
              fullWidth
            />
            
            <FormControlLabel
              control={
                <Switch
                  checked={supplierConfig.vat_included}
                  onChange={(e) => setSupplierConfig(prev => ({ ...prev, vat_included: e.target.checked }))}
                />
              }
              label="Prices include VAT"
            />
            
            <FormControl fullWidth>
              <InputLabel>Default Currency</InputLabel>
              <Select
                value={supplierConfig.default_currency}
                onChange={(e) => setSupplierConfig(prev => ({ ...prev, default_currency: e.target.value }))}
              >
                <MenuItem value="ZAR">ZAR (South African Rand)</MenuItem>
                <MenuItem value="USD">USD (US Dollar)</MenuItem>
                <MenuItem value="EUR">EUR (Euro)</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              label="Processing Notes"
              multiline
              rows={3}
              value={supplierConfig.processing_notes}
              onChange={(e) => setSupplierConfig(prev => ({ ...prev, processing_notes: e.target.value }))}
              placeholder="Any special notes about this supplier's pricelist format..."
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Cancel</Button>
          <Button onClick={saveSupplierConfig} variant="contained">Save Configuration</Button>
        </DialogActions>
      </Dialog>

      <Dialog open={previewDialog} onClose={() => setPreviewDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>File Preview</DialogTitle>
        <DialogContent>
          {previewData ? (
            previewData.error ? (
              <Alert severity="error">{previewData.error}</Alert>
            ) : (
              <Box>
                <Typography variant="h6" gutterBottom>
                  Detected Format: {previewData.structure_type}
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Brands Found: {previewData.brands_detected}
                </Typography>
                <Typography variant="body2" paragraph>
                  Sample Products: {previewData.sample_products?.length || 0}
                </Typography>
                
                {previewData.sample_products && (
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="subtitle1" gutterBottom>Sample Products:</Typography>
                    {previewData.sample_products.slice(0, 5).map((product, index) => (
                      <Box key={index} sx={{ p: 1, bgcolor: 'grey.50', mb: 1, borderRadius: 1 }}>
                        <Typography variant="body2">
                          <strong>{product.brand}</strong> - {product.stock_code}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Price: R{product.price_excl_vat}
                        </Typography>
                      </Box>
                    ))}
                  </Box>
                )}
              </Box>
            )
          ) : (
            <Typography>Loading preview...</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewDialog(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default PricelistUpload;