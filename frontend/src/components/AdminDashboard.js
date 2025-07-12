import React from 'react';
import { Box, Typography, Grid, Card, CardContent, Button } from '@mui/material';
import { Link } from 'react-router-dom';

const AdminDashboard = ({ user }) => {
  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        👋 Welcome, {user.user.full_name}!
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Admin Dashboard - Manage your AI quoting system
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📋 Pricelist Upload
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Upload and process supplier pricelists (Excel & PDF)
              </Typography>
              <Button 
                component={Link} 
                to="/admin/upload" 
                variant="contained"
              >
                Upload Pricelists
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                🤖 AI Training
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Monitor AI training progress and product database
              </Typography>
              <Button variant="outlined" disabled>
                Coming Soon
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdminDashboard;