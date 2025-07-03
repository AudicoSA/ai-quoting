// frontend/src/components/TrainingCenter/TrainingCenterMain.jsx (NEW FILE - safe)
import React, { useState } from 'react';
import { 
  Box, 
  Tabs, 
  Tab, 
  Typography, 
  Alert,
  Paper 
} from '@mui/material';
import { School, Psychology } from '@mui/icons-material';

// Import enhanced component
import EnhancedUploadCenter from './Enhanced/EnhancedUploadCenter';

const TrainingCenterMain = () => {
  const [activeTab, setActiveTab] = useState(1); // Default to enhanced

  return (
    <Box sx={{ width: '100%' }}>
      {/* Header */}
      <Paper sx={{ p: 3, mb: 3, textAlign: 'center' }}>
        <Typography variant="h3" gutterBottom>
          🎓 AI Training Center
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Upload supplier pricelists to enhance AI knowledge and conversation intelligence
        </Typography>
      </Paper>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={activeTab} 
          onChange={(e, newValue) => setActiveTab(newValue)}
          centered
        >
          <Tab 
            icon={<School />} 
            label="Standard Upload" 
            value={0}
          />
          <Tab 
            icon={<Psychology />} 
            label="Enhanced AI Upload" 
            value={1}
          />
        </Tabs>
      </Paper>

      {/* Tab Content */}
      <Box>
        {activeTab === 0 && (
          <Alert severity="info" sx={{ m: 3 }}>
            <Typography variant="h6">Standard Upload</Typography>
            <Typography>
              Standard upload functionality - this tab can connect to your existing training center component
              if you have one, or we can build basic upload functionality here.
            </Typography>
          </Alert>
        )}
        
        {activeTab === 1 && (
          <EnhancedUploadCenter />
        )}
      </Box>
    </Box>
  );
};

export default TrainingCenterMain;