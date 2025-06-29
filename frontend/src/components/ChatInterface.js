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
  IconButton
} from '@mui/material';
import { Send, ArrowBack } from '@mui/icons-material';
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
  const [quote, setQuote] = useState({ items: [], total: 0 });
  
  // Add ref for auto-scrolling
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

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
        category: category.id
      });

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response.data.response
      };

      setMessages(prev => [...prev, assistantMessage]);
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
              
              {/* Messages Container - FIXED SCROLLING */}
              <Box 
                ref={chatContainerRef}
                sx={{ 
                  flex: 1, 
                  overflowY: 'auto', 
                  mb: 2,
                  bgcolor: '#f8f9fa',
                  p: 2,
                  borderRadius: 2,
                  maxHeight: '400px', // Fixed height for scrolling
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
                          whiteSpace: 'pre-line', // Preserves line breaks
                          wordBreak: 'break-word' // Prevents overflow
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
                {/* Invisible element to scroll to */}
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

        {/* Quote Summary */}
        <Grid item xs={12} md={4}>
          <Card sx={{ height: 600 }}>
            <CardContent>
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
                    height: 300,
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
                <Box>
                  {/* Quote items will be added here */}
                  <Typography variant="body2">
                    Quote items will appear here as you chat...
                  </Typography>
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
