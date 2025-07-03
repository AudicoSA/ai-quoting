// frontend/src/components/TrainingCenter/FileUploadZone.jsx
import React, { useCallback, useState } from 'react';
import {
  Box,
  Typography,
  Button,
  Paper,
  LinearProgress,
  Alert,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  TableChart,
  Speed,
  Psychology
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

const FileUploadZone = ({ onFileUpload, uploading, disabled }) => {
  const [uploadProgress, setUploadProgress] = useState(0);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles.length > 0 && !disabled) {
      const file = acceptedFiles[0];
      
      // Simulate upload progress
      setUploadProgress(0);
      const interval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(interval);
            return 90;
          }
          return prev + 10;
        });
      }, 100);

      onFileUpload(file);
    }
  }, [onFileUpload, disabled]);

  const { getRootProps, getInputProps, isDragActive, isDragAccept, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv']
    },
    multiple: false,
    disabled
  });

  const getBorderColor = () => {
    if (isDragReject) return 'error.main';
    if (isDragAccept) return 'success.main';
    if (isDragActive) return 'primary.main';
    return 'grey.300';
  };

  const getBackgroundColor = () => {
    if (isDragReject) return 'error.light';
    if (isDragAccept) return 'success.light';
    if (isDragActive) return 'primary.light';
    return 'grey.50';
  };

  return (
    <Box>
      {/* Feature Highlights */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" gutterBottom textAlign="center">
          ✨ Enhanced Processing Features
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 1, mb: 3, flexWrap: 'wrap' }}>
          <Chip icon={<Psychology />} label="GPT-4 Intelligence" color="primary" />
          <Chip icon={<Speed />} label="Smart Detection" color="secondary" />
          <Chip icon={<TableChart />} label="Multi-Brand Support" color="success" />
          <Chip icon={<CheckCircle />} label="Real-time Validation" color="info" />
        </Box>
      </Box>

      {/* Upload Zone */}
      <Paper
        {...getRootProps()}
        sx={{
          border: 2,
          borderStyle: 'dashed',
          borderColor: getBorderColor(),
          bgcolor: getBackgroundColor(),
          p: 6,
          textAlign: 'center',
          cursor: disabled ? 'not-allowed' : 'pointer',
          transition: 'all 0.3s ease',
          opacity: disabled ? 0.6 : 1,
          '&:hover': !disabled ? {
            borderColor: 'primary.main',
            bgcolor: 'primary.light',
            transform: 'scale(1.02)'
          } : {}
        }}
      >
        <input {...getInputProps()} />
        
        <CloudUpload sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
        
        <Typography variant="h5" gutterBottom>
          {isDragActive ? 'Drop your pricelist here!' : 'Upload Supplier Pricelist'}
        </Typography>
        
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          {uploading 
            ? 'Processing your file with AI...' 
            : 'Drag & drop your Excel or CSV file, or click to browse'
          }
        </Typography>

        {!uploading && (
          <Button
            variant="contained"
            size="large"
            startIcon={<Description />}
            disabled={disabled}
          >
            Choose File
          </Button>
        )}

        {uploading && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress 
              variant="determinate" 
              value={uploadProgress} 
              sx={{ mb: 1, height: 8, borderRadius: 4 }}
            />
            <Typography variant="body2" color="text.secondary">
              {uploadProgress < 90 ? `Uploading... ${uploadProgress}%` : 'Analyzing structure...'}
            </Typography>
          </Box>
        )}
      </Paper>

      {/* Supported Formats */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Supported Formats & Features:
        </Typography>
        <List dense>
          <ListItem>
            <ListItemIcon><TableChart fontSize="small" /></ListItemIcon>
            <ListItemText primary="Excel (.xlsx) - Multi-brand horizontal layouts (like Nology)" />
          </ListItem>
          <ListItem>
            <ListItemIcon><Description fontSize="small" /></ListItemIcon>
            <ListItemText primary="CSV files - Comma-separated values" />
          </ListItem>
          <ListItem>
            <ListItemIcon><Psychology fontSize="small" /></ListItemIcon>
            <ListItemText primary="Intelligent parsing of complex price formats (P.O.R, currencies, etc.)" />
          </ListItem>
          <ListItem>
            <ListItemIcon><Speed fontSize="small" /></ListItemIcon>
            <ListItemText primary="Auto-detection of 30+ audio brands (YEALINK, JABRA, DNAKE, etc.)" />
          </ListItem>
        </List>
      </Alert>
    </Box>
  );
};

export default FileUploadZone;
