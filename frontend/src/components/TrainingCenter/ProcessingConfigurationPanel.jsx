// frontend/src/components/TrainingCenter/ProcessingConfigurationPanel.jsx (COMPLETE)
import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  FormControl,
  FormLabel,
  RadioGroup,
  FormControlLabel,
  Radio,
  TextField,
  Switch,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Chip,
  Alert,
  Slider,
  Select,
  MenuItem,
  InputLabel
} from '@mui/material';
import { ExpandMore, Settings, Recommend, TuneRounded } from '@mui/icons-material';

const ProcessingConfigurationPanel = ({ recommendations, onConfigChange }) => {
  const [config, setConfig] = useState({
    pricing: {
      markup_percentage: recommendations?.pricing?.markup_percentage || 10,
      vat_rate: recommendations?.pricing?.vat_rate || 15,
      include_vat: recommendations?.pricing?.include_vat || false,
      currency: recommendations?.pricing?.currency || 'ZAR'
    },
    processing: {
      skip_invalid_prices: true,
      auto_categorize_brands: true,
      batch_size: recommendations?.processing?.batch_size || 1000,
      enable_price_validation: true
    },
    validation: {
      require_brand: true,
      require_product_code: true,
      require_price: false,
      min_price: 0,
      max_price: 1000000
    }
  });

  const handleConfigChange = (section, field, value) => {
    const newConfig = {
      ...config,
      [section]: {
        ...config[section],
        [field]: value
      }
    };
    setConfig(newConfig);
    onConfigChange(newConfig);
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMore />}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Settings sx={{ mr: 1 }} />
            <Typography variant="h6">⚙️ Processing Configuration</Typography>
          </Box>
        </AccordionSummary>
        <AccordionDetails>
          {/* Smart Recommendations Alert */}
          {recommendations && (
            <Alert severity="info" sx={{ mb: 3 }} icon={<Recommend />}>
              <Typography variant="subtitle2">🤖 Smart Recommendations Applied</Typography>
              <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                <Chip label={`Confidence: ${recommendations.processing?.confidence_score || 'Medium'}`} size="small" />
                <Chip label={`Batch Size: ${recommendations.processing?.batch_size || 1000}`} size="small" />
                <Chip label={`Currency: ${recommendations.pricing?.currency || 'ZAR'}`} size="small" />
              </Box>
            </Alert>
          )}

          <Grid container spacing={3}>
            {/* Pricing Configuration */}
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>💰 Pricing Settings</Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <Typography gutterBottom>Markup Percentage: {config.pricing.markup_percentage}%</Typography>
                      <Slider
                        value={config.pricing.markup_percentage}
                        onChange={(e, value) => handleConfigChange('pricing', 'markup_percentage', value)}
                        min={0}
                        max={100}
                        step={5}
                        marks={[
                          { value: 0, label: '0%' },
                          { value: 25, label: '25%' },
                          { value: 50, label: '50%' },
                          { value: 100, label: '100%' }
                        ]}
                        valueLabelDisplay="auto"
                      />
                    </Grid>
                    
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="VAT Rate %"
                        type="number"
                        value={config.pricing.vat_rate}
                        onChange={(e) => handleConfigChange('pricing', 'vat_rate', Number(e.target.value))}
                        inputProps={{ min: 0, max: 50 }}
                        size="small"
                      />
                    </Grid>
                    
                    <Grid item xs={6}>
                      <FormControl fullWidth size="small">
                        <InputLabel>Currency</InputLabel>
                        <Select
                          value={config.pricing.currency}
                          onChange={(e) => handleConfigChange('pricing', 'currency', e.target.value)}
                          label="Currency"
                        >
                          <MenuItem value="ZAR">🇿🇦 South African Rand (ZAR)</MenuItem>
                          <MenuItem value="USD">🇺🇸 US Dollar (USD)</MenuItem>
                          <MenuItem value="EUR">🇪🇺 Euro (EUR)</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.pricing.include_vat}
                            onChange={(e) => handleConfigChange('pricing', 'include_vat', e.target.checked)}
                          />
                        }
                        label="Include VAT in final prices"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* Processing Options */}
            <Grid item xs={12} md={6}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>⚡ Processing Options</Typography>
                  
                  <Box sx={{ space: 2 }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.processing.skip_invalid_prices}
                          onChange={(e) => handleConfigChange('processing', 'skip_invalid_prices', e.target.checked)}
                        />
                      }
                      label="Skip products with invalid prices (P.O.R, etc.)"
                    />
                    
                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.processing.auto_categorize_brands}
                          onChange={(e) => handleConfigChange('processing', 'auto_categorize_brands', e.target.checked)}
                        />
                      }
                      label="Auto-categorize products by brand"
                    />

                    <FormControlLabel
                      control={
                        <Switch
                          checked={config.processing.enable_price_validation}
                          onChange={(e) => handleConfigChange('processing', 'enable_price_validation', e.target.checked)}
                        />
                      }
                      label="Enable advanced price validation"
                    />

                    <Box sx={{ mt: 2 }}>
                      <Typography gutterBottom>Batch Size: {config.processing.batch_size}</Typography>
                      <Slider
                        value={config.processing.batch_size}
                        onChange={(e, value) => handleConfigChange('processing', 'batch_size', value)}
                        min={100}
                        max={5000}
                        step={100}
                        marks={[
                          { value: 100, label: '100' },
                          { value: 1000, label: '1K' },
                          { value: 5000, label: '5K' }
                        ]}
                        valueLabelDisplay="auto"
                      />
                      <Typography variant="caption" color="text.secondary">
                        Products to process per batch. Higher = faster, but more memory usage.
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>

            {/* Validation Rules */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>🛡️ Validation Rules</Typography>
                  
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={4}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.validation.require_brand}
                            onChange={(e) => handleConfigChange('validation', 'require_brand', e.target.checked)}
                          />
                        }
                        label="Require brand name"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={4}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.validation.require_product_code}
                            onChange={(e) => handleConfigChange('validation', 'require_product_code', e.target.checked)}
                          />
                        }
                        label="Require product code"
                      />
                    </Grid>
                    
                    <Grid item xs={12} md={4}>
                      <FormControlLabel
                        control={
                          <Switch
                            checked={config.validation.require_price}
                            onChange={(e) => handleConfigChange('validation', 'require_price', e.target.checked)}
                          />
                        }
                        label="Require valid price"
                      />
                    </Grid>
                    
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Minimum Price"
                        type="number"
                        value={config.validation.min_price}
                        onChange={(e) => handleConfigChange('validation', 'min_price', Number(e.target.value))}
                        size="small"
                        InputProps={{ startAdornment: 'R' }}
                      />
                    </Grid>
                    
                    <Grid item xs={6}>
                      <TextField
                        fullWidth
                        label="Maximum Price"
                        type="number"
                        value={config.validation.max_price}
                        onChange={(e) => handleConfigChange('validation', 'max_price', Number(e.target.value))}
                        size="small"
                        InputProps={{ startAdornment: 'R' }}
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Configuration Summary */}
          <Alert severity="info" sx={{ mt: 3 }}>
            <Typography variant="subtitle2" gutterBottom>📋 Configuration Summary</Typography>
            <Typography variant="body2">
              • Markup: {config.pricing.markup_percentage}% | VAT: {config.pricing.vat_rate}% 
              ({config.pricing.include_vat ? 'Included' : 'Excluded'})
              <br />
              • Batch Size: {config.processing.batch_size} | 
              Skip Invalid: {config.processing.skip_invalid_prices ? 'Yes' : 'No'}
              <br />
              • Validation: Brand {config.validation.require_brand ? '✓' : '✗'} | 
              Code {config.validation.require_product_code ? '✓' : '✗'} | 
              Price {config.validation.require_price ? '✓' : '✗'}
            </Typography>
          </Alert>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default ProcessingConfigurationPanel;
