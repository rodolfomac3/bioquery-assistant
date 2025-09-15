import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, Beaker, BookOpen, Cpu, HelpCircle, Plus } from 'lucide-react';
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
  const [currentView, setCurrentView] = useState('welcome'); // 'welcome' or 'chat'
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    // Switch to chat view if we're on welcome
    if (currentView === 'welcome') {
      setCurrentView('chat');
    }

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

  const handleNewChat = () => {
    setMessages([]);
    setCurrentView('welcome');
    setInputMessage('');
  };

  const handleLogoClick = () => {
    setCurrentView('welcome');
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

  const renderWelcomeScreen = () => (
    <div className="welcome-section">
      <div className="welcome-card">
        <div className="welcome-header">
          <Beaker className="w-6 h-6" />
          <h2>Welcome to BioQuery Assistant</h2>
        </div>
        <p>Your AI-powered research companion for molecular biology, experimental design, and scientific literature analysis.</p>
        
        <div className="features-highlight">
          <div className="feature-item">
            <Cpu className="feature-icon" />
            <span>PCR Troubleshooting</span>
          </div>
          <div className="feature-item">
            <Beaker className="feature-icon" />
            <span>Experiment Design</span>
          </div>
          <div className="feature-item">
            <BookOpen className="feature-icon" />
            <span>Literature Search</span>
          </div>
        </div>
        
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
                  <HelpCircle className="example-icon" />
                  {example}
                </button>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderChatScreen = () => (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-title">Conversation</div>
        <button className="new-chat-button" onClick={handleNewChat}>
          <Plus className="w-4 h-4" />
          New Chat
        </button>
      </div>
      <div className="messages-container">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message ${message.sender} ${message.isError ? 'error' : ''}`}
          >
            <div className="message-content">
              {message.sender === 'assistant' && message.queryType && (
                <div className="message-meta">
                  {getQueryTypeIcon(message.queryType)}
                  <span>{getQueryTypeLabel(message.queryType)}</span>
                  {message.literatureIncluded && (
                    <span className="literature-badge">Literature Included</span>
                  )}
                </div>
              )}
              <div className="message-text">
                {message.text}
              </div>
              <div className="message-timestamp">
                {message.timestamp.toLocaleTimeString()}
                {message.usage && (
                  <span className="token-usage">
                    • {message.usage.total_tokens} tokens
                  </span>
                )}
              </div>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant">
            <div className="message-content loading-message">
              <div className="loading-animation">
                <div className="dna-spinner"></div>
                <div className="loading-text">
                  <span className="loading-dots">Analyzing your query</span>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  );

  return (
    <div className="App">
      <div className="container">
        <header className="app-header">
          <div className="header-content">
            <div className="logo-section" onClick={handleLogoClick}>
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
          {currentView === 'welcome' ? renderWelcomeScreen() : renderChatScreen()}
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
                <span className="toggle-text">
                  <BookOpen className="w-4 h-4" />
                  Include recent literature
                </span>
              </label>
            </div>
            <div className="input-container">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  placeholder="Ask about PCR troubleshooting, experimental design, protocols..."
                  className="message-input"
                  disabled={isLoading || apiStatus !== 'connected'}
                />
              </div>
              <button
                type="submit"
                className="send-button"
                disabled={isLoading || !inputMessage.trim() || apiStatus !== 'connected'}
              >
                {isLoading ? (
                  <div className="spinner"></div>
                ) : (
                  <Send className="w-5 h-5" />
                )}
              </button>
            </div>
          </form>
        </footer>
      </div>
    </div>
  );
}

export default App;