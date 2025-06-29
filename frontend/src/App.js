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
  Toolbar
} from '@mui/material';
import ChatInterface from './components/ChatInterface';

const categories = [
  { id: 'restaurants', name: 'RESTAURANTS', description: 'Background music, zone control, dining atmosphere', color: '#4CAF50' },
  { id: 'home', name: 'HOME', description: 'Home theater, music systems, hi-fi setups', color: '#2196F3' },
  { id: 'office', name: 'OFFICE', description: 'Conference rooms, background music, PA systems', color: '#FF9800' },
  { id: 'gym', name: 'GYM', description: 'Fitness center audio, zone control, background music', color: '#F44336' },
  { id: 'worship', name: 'PLACE OF WORSHIP', description: 'Church sound systems, microphones, mixing', color: '#9C27B0' },
  { id: 'schools', name: 'SCHOOLS', description: 'Classroom audio, PA systems, sports facilities', color: '#E91E63' },
  { id: 'educational', name: 'EDUCATIONAL', description: 'Lecture halls, university campus, training centers', color: '#795548' },
  { id: 'tenders', name: 'TENDERS', description: 'Large projects, commercial installations', color: '#607D8B' }
];

function App() {
  const [selectedCategory, setSelectedCategory] = useState(null);

  const handleCategorySelect = (category) => {
    setSelectedCategory(category);
  };

  const handleBackToCategories = () => {
    setSelectedCategory(null);
  };

  return (
    <div className="App">
      <AppBar position="static" sx={{ bgcolor: '#1976d2' }}>
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Audico AI Audio Solutions
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        {!selectedCategory ? (
          <>
            <Box textAlign="center" mb={4}>
              <Typography variant="h3" component="h1" gutterBottom>
                Audio Solutions Quotation System
              </Typography>
              <Typography variant="h6" color="text.secondary" gutterBottom>
                Which audio system do you need assistance with?
              </Typography>
            </Box>

            <Grid container spacing={3}>
              {categories.map((category) => (
                <Grid item xs={12} sm={6} md={4} key={category.id}>
                  <Card 
                    sx={{ 
                      height: '100%', 
                      display: 'flex', 
                      flexDirection: 'column',
                      cursor: 'pointer',
                      '&:hover': {
                        transform: 'translateY(-4px)',
                        boxShadow: 4
                      },
                      transition: 'all 0.3s ease'
                    }}
                    onClick={() => handleCategorySelect(category)}
                  >
                    <CardContent sx={{ flexGrow: 1 }}>
                      <Box
                        sx={{
                          width: 60,
                          height: 60,
                          borderRadius: '50%',
                          bgcolor: category.color,
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          mb: 2,
                          mx: 'auto'
                        }}
                      >
                        <Typography variant="h6" component="div" color="white" fontSize="12px">
                          🎵
                        </Typography>
                      </Box>
                      <Typography variant="h6" component="div" textAlign="center" gutterBottom>
                        {category.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" textAlign="center">
                        {category.description}
                      </Typography>
                    </CardContent>
                    <CardActions sx={{ justifyContent: 'center', pb: 2 }}>
                      <Button size="small" variant="outlined">
                        Get Quote
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </>
        ) : (
          <ChatInterface 
            category={selectedCategory} 
            onBack={handleBackToCategories}
          />
        )}
      </Container>
    </div>
  );
}

export default App;
