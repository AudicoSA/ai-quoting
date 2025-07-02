import React, { useState, useEffect, useRef } from 'react';
import {
  Container,
  Typography,
  Box,
  Button,
  TextField,
  Paper,
  Grid,
  Card,
  CardContent,
  Divider,
  IconButton,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import { Send, ArrowBack, Delete } from '@mui/icons-material';
import axios from 'axios';

const ChatInterface = ({ category, onBack }) => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: `I'm here to help you build the perfect audio solution for your ${category.name.toLowerCase()}. What specific audio requirements do you have?`
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [quote, setQuote] = useState({ items: [], total_amount: 0, total_savings: 0, item_count: 0 });
  const [currentQuoteId, setCurrentQuoteId] = useState(null);
  
  // Add ref for auto-scrolling
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // 🔥 NEW: Function to fetch updated quote
  const fetchQuote = async (quoteId) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/v1/quotes/${quoteId}`);
      setQuote(response.data);
      setCurrentQuoteId(quoteId);
    } catch (error) {
      console.error('Error fetching quote:', error);
    }
  };

  // 🔥 NEW: Function to remove item from quote
  const removeFromQuote = async (productId) => {
    if (!currentQuoteId) return;
    
    try {
      await axios.delete(`http://localhost:8000/api/v1/quotes/${currentQuoteId}/items/${productId}`);
      // Refresh quote after removal
      await fetchQuote(currentQuoteId);
    } catch (error) {
      console.error('Error removing item:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/chat', {
        message: inputMessage,
        category: category.id,
        quote_id: currentQuoteId // Pass current quote ID
      });

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response
      };

      setMessages(prev => [...prev, assistantMessage]);

      // 🔥 KEY FIX: Check if item was added to quote and update UI
      if (response.data.quote_id && response.data.auto_added) {
        // Fetch the updated quote to display in Live Quote panel
        await fetchQuote(response.data.quote_id);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I had trouble connecting. Please try again.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Container maxWidth="lg">
      <Box mb={3}>
        <Button
          startIcon={<ArrowBack />}
          onClick={onBack}
          variant="outlined"
          sx={{ mb: 2 }}
        >
          Back to Categories
        </Button>
        <Typography variant="h4" gutterBottom>
          {category.name} Audio Solutions
        </Typography>
        <Typography variant="subtitle1" color="text.secondary">
          Chat with our AI specialist to build the perfect audio system for your {category.name.toLowerCase()}
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Chat Interface */}
        <Grid item xs={12} md={8}>
          <Card sx={{ height: 600, display: 'flex', flexDirection: 'column' }}>
            <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column', p: 2 }}>
              <Typography variant="h6" gutterBottom>
                🤖 AI Equipment Specialist
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {/* Messages Container */}
              <Box 
                ref={chatContainerRef}
                sx={{ 
                  flex: 1, 
                  overflowY: 'auto', 
                  mb: 2,
                  bgcolor: '#f8f9fa',
                  p: 2,
                  borderRadius: 2,
                  maxHeight: '400px',
                  '&::-webkit-scrollbar': {
                    width: '8px',
                  },
                  '&::-webkit-scrollbar-track': {
                    background: '#f1f1f1',
                    borderRadius: '4px',
                  },
                  '&::-webkit-scrollbar-thumb': {
                    background: '#c1c1c1',
                    borderRadius: '4px',
                  },
                  '&::-webkit-scrollbar-thumb:hover': {
                    background: '#a8a8a8',
                  },
                }}
              >
                {messages.map((message) => (
                  <Box
                    key={message.id}
                    sx={{
                      display: 'flex',
                      justifyContent: message.role === 'user' ? 'flex-end' : 'flex-start',
                      mb: 2
                    }}
                  >
                    <Paper
                      sx={{
                        p: 2,
                        maxWidth: '85%',
                        bgcolor: message.role === 'user' ? '#1976d2' : '#fff',
                        color: message.role === 'user' ? 'white' : 'black',
                        boxShadow: message.role === 'user' ? 2 : 1
                      }}
                    >
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          whiteSpace: 'pre-line',
                          wordBreak: 'break-word'
                        }}
                      >
                        {message.content}
                      </Typography>
                    </Paper>
                  </Box>
                ))}
                {isLoading && (
                  <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <Paper sx={{ p: 2, bgcolor: '#fff' }}>
                      <Typography variant="body2">
                        🤖 AI is analyzing your requirements...
                      </Typography>
                    </Paper>
                  </Box>
                )}
                <div ref={messagesEndRef} />
              </Box>

              {/* Input */}
              <Box sx={{ display: 'flex', gap: 1 }}>
                <TextField
                  fullWidth
                  variant="outlined"
                  placeholder="Describe what audio equipment you need..."
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                  size="small"
                  multiline
                  maxRows={3}
                />
                <IconButton
                  onClick={handleSendMessage}
                  disabled={isLoading || !inputMessage.trim()}
                  color="primary"
                  sx={{ 
                    bgcolor: '#1976d2', 
                    color: 'white',
                    '&:hover': { bgcolor: '#1565c0' },
                    '&:disabled': { bgcolor: '#ccc' }
                  }}
                >
                  <Send />
                </IconButton>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 🔥 FIXED: Live Quote Panel */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: 600 }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                📋 Live Quote
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {quote.items.length === 0 ? (
                <Box 
                  sx={{ 
                    display: 'flex', 
                    flexDirection: 'column', 
                    alignItems: 'center', 
                    justifyContent: 'center',
                    flex: 1,
                    color: 'text.secondary'
                  }}
                >
                  <Typography variant="h2" sx={{ mb: 2 }}>📄</Typography>
                  <Typography variant="body2" textAlign="center">
                    No items added yet
                  </Typography>
                  <Typography variant="caption" textAlign="center">
                    Chat with AI to build your quote
                  </Typography>
                </Box>
              ) : (
                <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
                  {/* Quote Items */}
                  <Box sx={{ flex: 1, overflowY: 'auto', mb: 2 }}>
                    <List dense>
                      {quote.items.map((item, index) => (
                        <ListItem key={index} sx={{ bgcolor: '#f5f5f5', mb: 1, borderRadius: 1 }}>
                          <ListItemText
                            primary={
                              <Typography variant="subtitle2" sx={{ fontWeight: 'bold' }}>
                                {item.name}
                              </Typography>
                            }
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  Model: {item.model}
                                </Typography>
                                <Typography variant="body2" color="text.secondary">
                                  Qty: {item.quantity}
                                </Typography>
                                <Box sx={{ mt: 1 }}>
                                  {item.has_special_price ? (
                                    <Box>
                                      <Chip 
                                        label={`R${item.price.toLocaleString()}`}
                                        color="success" 
                                        size="small" 
                                        sx={{ mr: 1 }}
                                      />
                                      <Chip 
                                        label={`Save R${item.savings?.toLocaleString()}`}
                                        color="warning" 
                                        size="small"
                                      />
                                    </Box>
                                  ) : (
                                    <Chip 
                                      label={`R${item.price.toLocaleString()}`}
                                      variant="outlined" 
                                      size="small"
                                    />
                                  )}
                                </Box>
                              </Box>
                            }
                          />
                          <ListItemSecondaryAction>
                            <IconButton 
                              edge="end" 
                              onClick={() => removeFromQuote(item.product_id)}
                              size="small"
                              color="error"
                            >
                              <Delete />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                      ))}
                    </List>
                  </Box>

                  {/* Quote Summary */}
                  <Divider sx={{ mb: 2 }} />
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                      <Typography variant="body2">Items:</Typography>
                      <Typography variant="body2">{quote.item_count}</Typography>
                    </Box>
                    {quote.total_savings > 0 && (
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                        <Typography variant="body2" color="success.main">Total Savings:</Typography>
                        <Typography variant="body2" color="success.main">
                          R{quote.total_savings.toLocaleString()}
                        </Typography>
                      </Box>
                    )}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 2 }}>
                      <Typography variant="h6">Total:</Typography>
                      <Typography variant="h6" color="primary">
                        R{quote.total_amount.toLocaleString()}
                      </Typography>
                    </Box>
                    <Button variant="contained" fullWidth disabled={quote.items.length === 0}>
                      Generate Quote PDF
                    </Button>
                  </Box>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ChatInterface;
