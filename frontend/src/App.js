// frontend/src/App.js (COMPLETE ENHANCED VERSION)
import React, { useState } from 'react';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
  AppBar,
  Toolbar,
  IconButton,
  Tabs,
  Tab,
  Paper,
  Chip
} from '@mui/material';
import { Psychology, School, AutoAwesome } from '@mui/icons-material';

// Your existing components
import ChatInterface from './components/ChatInterface';
import TrainingInterface from './components/TrainingInterface';

// NEW: Import our enhanced training center
import EnhancedUploadCenter from './components/TrainingCenter/Enhanced/EnhancedUploadCenter';

const categories = [
  { id: 'restaurants', name: 'RESTAURANTS', description: 'Background music, zone control, dining atmosphere', color: '#4CAF50' },
  { id: 'home', name: 'HOME', description: 'Home theater, music systems, hi-fi setups', color: '#2196F3' },
  { id: 'office', name: 'OFFICE', description: 'Conference rooms, background music, PA systems', color: '#FF9800' },
  { id: 'gym', name: 'GYM', description: 'Fitness center audio, zone control, background music', color: '#F44336' },
  { id: 'worship', name: 'WORSHIP', description: 'Sound systems, microphones, AV integration', color: '#9C27B0' }
];

function App() {
  const [selectedCategory, setSelectedCategory] = useState(null);
  const [showTraining, setShowTraining] = useState(false);
  const [trainingMode, setTrainingMode] = useState('standard'); // NEW: Track training mode

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
    setShowTraining(false);
    setTrainingMode('standard');
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
    setShowTraining(false);
    setTrainingMode('standard');
  };

  const handleShowTraining = (mode = 'standard') => {
    setShowTraining(true);
    setTrainingMode(mode);
    setSelectedCategory(null);
  };

  return (
    <div>
      {/* Enhanced App Bar */}
      <AppBar position="static" sx={{ background: 'linear-gradient(45deg, #1976d2 30%, #42a5f5 90%)' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
            🎵 Audico AI Audio Solutions
          </Typography>
          
          {/* Enhanced Training Center Buttons */}
          <Box sx={{ display: 'flex', gap: 1 }}>
            <IconButton 
              color="inherit" 
              onClick={() => handleShowTraining('standard')}
              title="Standard Training Center"
            >
              <School />
            </IconButton>
            <IconButton 
              color="inherit" 
              onClick={() => handleShowTraining('enhanced')}
              title="Enhanced AI Training Center"
              sx={{ 
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%': { transform: 'scale(1)' },
                  '50%': { transform: 'scale(1.1)' },
                  '100%': { transform: 'scale(1)' }
                }
              }}
            >
              <Psychology />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {/* Main Category Selection View */}
        {!selectedCategory && !showTraining && (
          <Box>
            {/* Hero Section */}
            <Paper sx={{ p: 4, mb: 4, textAlign: 'center', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
              <Typography variant="h3" component="h1" gutterBottom fontWeight="bold">
                AI-Powered Audio Solutions
              </Typography>
              <Typography variant="h6" sx={{ mb: 3, opacity: 0.9 }}>
                Get expert recommendations tailored to your specific audio needs
              </Typography>
              
              {/* Enhanced Training Center CTA */}
              <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, flexWrap: 'wrap' }}>
                <Button
                  variant="outlined"
                  size="large"
                  onClick={() => handleShowTraining('standard')}
                  startIcon={<School />}
                  sx={{ 
                    color: 'white', 
                    borderColor: 'white',
                    '&:hover': { 
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      borderColor: 'white'
                    }
                  }}
                >
                  Standard Training Center
                </Button>
                <Button
                  variant="contained"
                  size="large"
                  onClick={() => handleShowTraining('enhanced')}
                  startIcon={<AutoAwesome />}
                  sx={{ 
                    background: 'linear-gradient(45deg, #ff6b6b, #4ecdc4)',
                    boxShadow: '0 3px 5px 2px rgba(255, 105, 135, .3)',
                    '&:hover': {
                      background: 'linear-gradient(45deg, #ff5252, #26a69a)',
                    }
                  }}
                >
                  Enhanced AI Training Center
                </Button>
              </Box>
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center', flexWrap: 'wrap', gap: 1 }}>
                <Chip label="🤖 GPT-4 Powered" color="primary" />
                <Chip label="⚡ Smart Detection" color="secondary" />
                <Chip label="📊 Real-time Analysis" color="success" />
              </Box>
            </Paper>

            {/* Categories Grid */}
            <Typography variant="h4" component="h2" gutterBottom textAlign="center" sx={{ mb: 4 }}>
              Choose Your Audio Solution Category
            </Typography>
            
            <Grid container spacing={3}>
              {categories.map((category) => (
                <Grid item xs={12} sm={6} md={4} key={category.id}>
                  <Card 
                    sx={{ 
                      height: '100%',
                      cursor: 'pointer',
                      transition: 'all 0.3s ease',
                      '&:hover': {
                        transform: 'translateY(-8px)',
                        boxShadow: 6
                      },
                      border: `3px solid ${category.color}`,
                      borderRadius: 2
                    }}
                    onClick={() => handleCategorySelect(category)}
                  >
                    <CardContent sx={{ textAlign: 'center', p: 3 }}>
                      <Box
                        sx={{
                          width: 60,
                          height: 60,
                          borderRadius: '50%',
                          backgroundColor: category.color,
                          margin: '0 auto 16px auto',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center'
                        }}
                      >
                        <Typography variant="h6" sx={{ color: 'white', fontWeight: 'bold' }}>
                          {category.name.charAt(0)}
                        </Typography>
                      </Box>
                      <Typography variant="h5" component="h3" gutterBottom fontWeight="bold">
                        {category.name}
                      </Typography>
                      <Typography variant="body1" color="text.secondary">
                        {category.description}
                      </Typography>
                    </CardContent>
                    <CardActions sx={{ justifyContent: 'center', pb: 3 }}>
                      <Button 
                        variant="contained" 
                        sx={{ 
                          backgroundColor: category.color,
                          '&:hover': {
                            backgroundColor: category.color,
                            filter: 'brightness(0.9)'
                          }
                        }}
                      >
                        Get Started
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Box>
        )}

        {/* Chat Interface (Your existing functionality) */}
        {selectedCategory && !showTraining && (
          <ChatInterface 
            category={selectedCategory} 
            onBack={handleBackToCategories}
          />
        )}

        {/* Training Center Interface */}
        {showTraining && (
          <Box>
            {/* Training Center Header */}
            <Paper sx={{ p: 3, mb: 3, textAlign: 'center' }}>
              <Typography variant="h3" gutterBottom>
                🎓 AI Training Center
              </Typography>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Upload supplier pricelists to enhance AI knowledge and conversation intelligence
              </Typography>
              
              {/* Training Mode Tabs */}
              <Box sx={{ mt: 3 }}>
                <Tabs 
                  value={trainingMode} 
                  onChange={(e, newValue) => setTrainingMode(newValue)}
                  centered
                  sx={{ borderBottom: 1, borderColor: 'divider' }}
                >
                  <Tab 
                    icon={<School />} 
                    label="Standard Training" 
                    value="standard"
                  />
                  <Tab 
                    icon={<Psychology />} 
                    label="Enhanced AI Training" 
                    value="enhanced"
                    sx={{ 
                      '& .MuiTab-iconWrapper': {
                        animation: 'pulse 2s infinite'
                      }
                    }}
                  />
                </Tabs>
              </Box>
            </Paper>

            {/* Training Content */}
            <Box>
              {trainingMode === 'standard' && (
                <Box>
                  {/* Standard Training Interface */}
                  <TrainingInterface onBack={handleBackToCategories} />
                </Box>
              )}
              
              {trainingMode === 'enhanced' && (
                <Box>
                  {/* Enhanced AI Training Interface */}
                  <EnhancedUploadCenter />
                </Box>
              )}
            </Box>

            {/* Back Button */}
            <Box sx={{ textAlign: 'center', mt: 4 }}>
              <Button
                variant="outlined"
                size="large"
                onClick={handleBackToCategories}
                sx={{ minWidth: 200 }}
              >
                ← Back to Categories
              </Button>
            </Box>
          </Box>
        )}
      </Container>
    </div>
  );
}

export default App;
