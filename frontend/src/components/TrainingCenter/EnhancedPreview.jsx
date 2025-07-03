// frontend/src/components/TrainingCenter/EnhancedPreview.jsx
import React from 'react';
import { 
  Box, 
  Typography, 
  Chip, 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableRow,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

const EnhancedPreview = ({ analysis }) => {
  if (!analysis) return null;

  const { structure_analysis, extraction_summary } = analysis;

  return (
    <Box>
      {/* Structure Detection Status */}
      <Alert 
        severity={structure_analysis.is_valid ? "success" : "warning"}
        sx={{ mb: 2 }}
      >
        {structure_analysis.is_valid 
          ? `✅ Structure detected: ${structure_analysis.layout_type}`
          : `⚠️ Structure detection needs review: ${structure_analysis.error || 'Unknown format'}`
        }
      </Alert>

      {/* Brands Overview */}
      <Accordion defaultExpanded>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            🏷️ Brands Detected ({structure_analysis.brands_detected.length})
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {structure_analysis.brands_detected.map((brand, index) => (
              <Chip 
                key={index} 
                label={brand} 
                color="primary" 
                variant="outlined"
              />
            ))}
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Column Mapping Details */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            🗂️ Column Mapping
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Brand</TableCell>
                <TableCell>Product Code Column</TableCell>
                <TableCell>Price Column</TableCell>
                <TableCell>Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {Object.entries(structure_analysis.column_mapping || {}).map(([brand, mapping]) => (
                <TableRow key={brand}>
                  <TableCell>{brand}</TableCell>
                  <TableCell>{mapping.product_code_column || 'Not found'}</TableCell>
                  <TableCell>{mapping.price_column || 'Not found'}</TableCell>
                  <TableCell>
                    {mapping.product_code_column && mapping.price_column ? (
                      <Chip label="✅ Ready" color="success" size="small" />
                    ) : (
                      <Chip label="❌ Incomplete" color="error" size="small" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </AccordionDetails>
      </Accordion>

      {/* Extraction Summary */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            📊 Extraction Summary
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 2 }}>
            <Box>
              <Typography variant="subtitle2">Total Products</Typography>
              <Typography variant="h4" color="primary">{analysis.total_products}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2">Successful Extractions</Typography>
              <Typography variant="h4" color="success.main">{extraction_summary.successful_extractions}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2">Failed Extractions</Typography>
              <Typography variant="h4" color="error.main">{extraction_summary.failed_extractions}</Typography>
            </Box>
            <Box>
              <Typography variant="subtitle2">Success Rate</Typography>
              <Typography variant="h4" color="info.main">
                {Math.round((extraction_summary.successful_extractions / analysis.total_products) * 100)}%
              </Typography>
            </Box>
          </Box>
        </AccordionDetails>
      </Accordion>

      {/* Sample Products */}
      <Accordion>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            🔍 Sample Products Preview
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Table>
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
              {analysis.sample_products.map((product, index) => (
                <TableRow key={index}>
                  <TableCell>
                    <Chip label={product.brand} size="small" />
                  </TableCell>
                  <TableCell>{product.product_code}</TableCell>
                  <TableCell>{product.raw_price}</TableCell>
                  <TableCell>
                    {product.parsed_price ? `R${product.parsed_price.toFixed(2)}` : '-'}
                  </TableCell>
                  <TableCell>
                    {product.parsed_price ? (
                      <Chip label="✅" color="success" size="small" />
                    ) : (
                      <Chip label="❌" color="error" size="small" />
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </AccordionDetails>
      </Accordion>
    </Box>
  );
};

export default EnhancedPreview;
