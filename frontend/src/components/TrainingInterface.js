import React, { useState } from 'react';
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
  Alert
} from '@mui/material';
import { CloudUpload, Description, Psychology } from '@mui/icons-material';
import axios from 'axios';

const TrainingInterface = ({ onBack }) => {
  const [uploadStatus, setUploadStatus] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [knowledgeBase, setKnowledgeBase] = useState({});

  const handleFileUpload = async (event) => {
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
      loadKnowledgeBase(); // Refresh knowledge base
    } catch (error) {
      setUploadStatus(`❌ Error processing ${file.name}: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const loadKnowledgeBase = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/training/knowledge-base');
      setKnowledgeBase(response.data.knowledge_base);
    } catch (error) {
      console.error('Error loading knowledge base:', error);
    }
  };

  React.useEffect(() => {
    loadKnowledgeBase();
  }, []);

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
      </Box>

      <Grid container spacing={3}>
        {/* Upload Interface */}
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
                  id="file-upload"
                  type="file"
                  onChange={handleFileUpload}
                  disabled={isUploading}
                />
                <label htmlFor="file-upload">
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
                The system will automatically categorize content and improve responses.
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Knowledge Base Display */}
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
      </Grid>
    </Container>
  );
};

export default TrainingInterface;