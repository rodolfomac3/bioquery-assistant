import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Send, Beaker, BookOpen, Cpu, HelpCircle } from 'lucide-react';
import './App.css';

// Configure axios base URL
const API_BASE_URL = 'http://localhost:5001';
axios.defaults.baseURL = API_BASE_URL;

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [includeLiterature, setIncludeLiterature] = useState(false);
  const [examples, setExamples] = useState({});
  const [apiStatus, setApiStatus] = useState('checking');

  // Check API health on mount
  useEffect(() => {
    checkApiHealth();
    loadExamples();
  }, []);

  const checkApiHealth = async () => {
    try {
      const response = await axios.get('/');
      if (response.data.status === 'healthy') {
        setApiStatus('connected');
      } else {
        setApiStatus('error');
      }
    } catch (error) {
      console.error('API health check failed:', error);
      setApiStatus('disconnected');
    }
  };

  const loadExamples = async () => {
    try {
      const response = await axios.get('/api/examples');
      setExamples(response.data);
    } catch (error) {
      console.error('Failed to load examples:', error);
    }
  };

  const sendMessage = async (messageText = inputMessage) => {
    if (!messageText.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post('/api/chat', {
        message: messageText,
        include_literature: includeLiterature
      });

      const assistantMessage = {
        id: Date.now() + 1,
        text: response.data.response,
        sender: 'assistant',
        timestamp: new Date(),
        queryType: response.data.query_type,
        literatureIncluded: response.data.literature_included,
        usage: response.data.usage
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your request. Please make sure the backend is running and try again.',
        sender: 'assistant',
        timestamp: new Date(),
        isError: true
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage();
  };

  const handleExampleClick = (exampleText) => {
    sendMessage(exampleText);
  };

  const getQueryTypeIcon = (queryType) => {
    switch (queryType) {
      case 'pcr_troubleshooting': return <Cpu className="w-4 h-4" />;
      case 'experimental_design': return <Beaker className="w-4 h-4" />;
      case 'literature_synthesis': return <BookOpen className="w-4 h-4" />;
      default: return <HelpCircle className="w-4 h-4" />;
    }
  };

  const getQueryTypeLabel = (queryType) => {
    switch (queryType) {
      case 'pcr_troubleshooting': return 'PCR Troubleshooting';
      case 'experimental_design': return 'Experimental Design';
      case 'literature_synthesis': return 'Literature Analysis';
      default: return 'General Biology';
    }
  };

  const getStatusColor = () => {
    switch (apiStatus) {
      case 'connected': return '#48bb78';
      case 'checking': return '#ed8936';
      case 'disconnected': 
      case 'error': 
      default: return '#f56565';
    }
  };

  return (
    <div className="App">
      <div className="container">
        <header className="app-header">
          <div className="header-content">
            <div className="logo-section">
              <Beaker className="logo-icon" />
              <div>
                <h1>BioQuery Assistant</h1>
                <p>AI-powered research assistant for molecular biology</p>
              </div>
            </div>
            <div className="status-indicator">
              <div 
                className="status-dot" 
                style={{ backgroundColor: getStatusColor() }}
              ></div>
              <span className="status-text">
                {apiStatus === 'connected' ? 'Connected' : 
                 apiStatus === 'checking' ? 'Connecting...' : 'Disconnected'}
              </span>
            </div>
          </div>
        </header>

        <main className="app-main">
          {messages.length === 0 ? (
            <div className="welcome-section">
              <div className="welcome-card">
                <h2>Welcome to BioQuery Assistant!</h2>
                <p>Get expert guidance on molecular biology techniques, experimental design, and research planning.</p>
                
                <div className="examples-grid">
                  {Object.entries(examples).map(([category, categoryExamples]) => (
                    <div key={category} className="example-category">
                      <h3>{category.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</h3>
                      {categoryExamples.slice(0, 2).map((example, index) => (
                        <button
                          key={index}
                          className="example-button"
                          onClick={() => handleExampleClick(example)}
                        >
                          {example}
                        </button>
                      ))}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="chat-container">
              <div className="messages-container">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`message ${message.sender} ${message.isError ? 'error' : ''} fade-in`}
                  >
                    <div className="message-content">
                      {message.sender === 'assistant' && message.queryType && (
                        <div className="message-meta">
                          {getQueryTypeIcon(message.queryType)}
                          <span>{getQueryTypeLabel(message.queryType)}</span>
                          {message.literatureIncluded && (
                            <span className="literature-badge">📚 Literature Included</span>
                          )}
                        </div>
                      )}
                      <div className="message-text">
                        {message.text}
                      </div>
                      <div className="message-timestamp">
                        {message.timestamp.toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="message assistant fade-in">
                    <div className="message-content">
                      <div className="message-text">
                        <span className="loading-dots">Analyzing your query</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>

        <footer className="app-footer">
          <form onSubmit={handleSubmit} className="message-form">
            <div className="form-options">
              <label className="literature-toggle">
                <input
                  type="checkbox"
                  checked={includeLiterature}
                  onChange={(e) => setIncludeLiterature(e.target.checked)}
                />
                Include recent literature
              </label>
            </div>
            <div className="input-container">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask about PCR troubleshooting, experimental design, protocols..."
                className="message-input"
                disabled={isLoading || apiStatus !== 'connected'}
              />
              <button
                type="submit"
                className="send-button"
                disabled={isLoading || !inputMessage.trim() || apiStatus !== 'connected'}
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </form>
        </footer>
      </div>
    </div>
  );
}

export default App;