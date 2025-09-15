import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  Send, Beaker, BookOpen, Cpu, HelpCircle, Plus, Menu, Trash2, 
  Copy, RefreshCw, Bookmark, Zap, Calculator, Mic, Paperclip, 
  Settings, Download 
} from 'lucide-react';
import './App.css';

// Configure axios base URL
const API_BASE_URL = 'http://localhost:5002';
axios.defaults.baseURL = API_BASE_URL;

// Chat History Sidebar Component
const ChatHistorySidebar = ({ chatHistory, currentChatId, onSelectChat, onDeleteChat, isOpen, onToggle }) => {
  return (
    <div className={`chat-sidebar ${isOpen ? 'open' : 'closed'}`}>
      <div className="sidebar-header">
        <button className="toggle-sidebar" onClick={onToggle}>
          <Menu className="w-5 h-5" />
        </button>
        <h3>Chat History</h3>
      </div>
      <div className="chat-list">
        {chatHistory.map(chat => (
          <div 
            key={chat.id}
            className={`chat-item ${chat.id === currentChatId ? 'active' : ''}`}
            onClick={() => onSelectChat(chat.id)}
          >
            <div className="chat-preview">
              <div className="chat-title">{chat.title}</div>
              <div className="chat-timestamp">{chat.timestamp}</div>
            </div>
            <button 
              className="delete-chat"
              onClick={(e) => {
                e.stopPropagation();
                onDeleteChat(chat.id);
              }}
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

// Message Actions Component
const MessageActions = ({ message, onCopy, onRegenerate, onSave }) => {
  const [showActions, setShowActions] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.text);
    onCopy && onCopy(message.text);
  };

  return (
    <div 
      className="message-actions-container"
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {showActions && (
        <div className="message-actions">
          <button className="action-btn" onClick={handleCopy} title="Copy">
            <Copy className="w-4 h-4" />
          </button>
          {message.sender === 'assistant' && (
            <button className="action-btn" onClick={() => onRegenerate(message)} title="Regenerate">
              <RefreshCw className="w-4 h-4" />
            </button>
          )}
          <button className="action-btn" onClick={() => onSave(message)} title="Save">
            <Bookmark className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};

// Quick Actions Component
const QuickActions = ({ onQuickAction }) => {
  const quickActions = [
    { icon: Zap, label: "PCR Help", action: "pcr_help" },
    { icon: Beaker, label: "Protocol", action: "protocol" },
    { icon: BookOpen, label: "Literature", action: "literature" },
    { icon: Calculator, label: "Calculate", action: "calculate" }
  ];

  return (
    <div className="quick-actions">
      {quickActions.map(({ icon: Icon, label, action }) => (
        <button
          key={action}
          className="quick-action-btn"
          onClick={() => onQuickAction(action)}
          title={label}
        >
          <Icon className="w-4 h-4" />
          <span>{label}</span>
        </button>
      ))}
    </div>
  );
};

// Enhanced Input Component
// Fixed Enhanced Input Component with proper suggestions filtering

const EnhancedInput = ({ 
  value, 
  onChange, 
  onSubmit, 
  disabled, 
  suggestions = [], 
  onSuggestionClick 
}) => {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [filteredSuggestions, setFilteredSuggestions] = useState([]);

  useEffect(() => {
    console.log('Input value:', value); // Debug
    console.log('Available suggestions:', suggestions); // Debug
    
    if (value.length > 2 && suggestions.length > 0) {
      const filtered = suggestions.filter(s => {
        if (!s || typeof s !== 'string') return false;
        return s.toLowerCase().includes(value.toLowerCase());
      });
      
      console.log('Filtered suggestions:', filtered); // Debug
      setFilteredSuggestions(filtered.slice(0, 5));
      setShowSuggestions(filtered.length > 0);
    } else {
      setShowSuggestions(false);
      setFilteredSuggestions([]);
    }
  }, [value, suggestions]);

  const handleFormSubmit = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setShowSuggestions(false); // Hide suggestions on submit
    if (onSubmit && !disabled && value.trim()) {
      onSubmit(e);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setShowSuggestions(false);
    if (onSuggestionClick) {
      onSuggestionClick(suggestion);
    }
  };

  const handleInputFocus = () => {
    if (value.length > 2 && filteredSuggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  const handleInputBlur = () => {
    // Delay hiding to allow clicking on suggestions
    setTimeout(() => setShowSuggestions(false), 200);
  };

  return (
    <div className="enhanced-input-container">
      {showSuggestions && filteredSuggestions.length > 0 && (
        <div className="suggestions-dropdown">
          {filteredSuggestions.map((suggestion, index) => (
            <button
              key={index}
              type="button"
              className="suggestion-item"
              onClick={() => handleSuggestionClick(suggestion)}
              onMouseDown={(e) => e.preventDefault()} // Prevent blur on click
            >
              <HelpCircle className="w-4 h-4" />
              {suggestion}
            </button>
          ))}
        </div>
      )}
      <form onSubmit={handleFormSubmit} className="enhanced-input-form">
        <div className="input-wrapper">
          <input
            type="text"
            value={value}
            onChange={onChange}
            placeholder="Ask about PCR, cloning, Western blots..."
            className="message-input enhanced"
            disabled={disabled}
            onFocus={handleInputFocus}
            onBlur={handleInputBlur}
          />
          <div className="input-features">
            <button type="button" className="feature-btn" title="Voice Input">
              <Mic className="w-4 h-4" />
            </button>
            <button type="button" className="feature-btn" title="Attach File">
              <Paperclip className="w-4 h-4" />
            </button>
          </div>
        </div>
        <button 
          type="submit" 
          className="send-button enhanced" 
          disabled={disabled || !value.trim()}
        >
          <Send className="w-5 h-5" />
        </button>
      </form>
    </div>
  );
};

// Main App Component
function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [includeLiterature, setIncludeLiterature] = useState(false);
  const [examples, setExamples] = useState({});
  const [apiStatus, setApiStatus] = useState('checking');
  const [currentView, setCurrentView] = useState('welcome');
  
  // Enhanced features state
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [savedMessages, setSavedMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  const messagesEndRef = useRef(null);

  // Common queries for suggestions
  const commonSuggestions = [
    "My PCR isn't working, what should I check?",
    "How do I design primers for PCR?",
    "What controls should I include in my experiment?",
    "How do I optimize Western blot conditions?",
    "What's the best way to isolate RNA?",
    "How do I calculate molarity?",
    "What's the difference between qPCR and PCR?",
    "How do I troubleshoot gel electrophoresis?",
    "What are the steps for bacterial transformation?",
    "How do I design a CRISPR experiment?"
  ];

  // Export chat function
  const exportChat = (messages, title) => {
    const chatContent = messages.map(msg => 
      `${msg.sender.toUpperCase()}: ${msg.text}\nTime: ${msg.timestamp.toLocaleString()}\n\n`
    ).join('');

    const blob = new Blob([chatContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${title || 'bioquery-chat'}-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Auto-scroll to bottom
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

    // Create new chat if needed
    if (currentView === 'welcome' || !currentChatId) {
      const newChatId = createNewChat(messageText);
      setCurrentChatId(newChatId);
      setCurrentView('chat');
    }

    const userMessage = {
      id: Date.now(),
      text: messageText,
      sender: 'user',
      timestamp: new Date()
    };

    const newMessages = [...messages, userMessage];
    setMessages(newMessages);
    setInputMessage('');
    setIsLoading(true);

    // Update chat history
    if (currentChatId) {
      updateChatMessages(currentChatId, newMessages);
    }

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

      const finalMessages = [...newMessages, assistantMessage];
      setMessages(finalMessages);
      
      // Update chat history
      if (currentChatId) {
        updateChatMessages(currentChatId, finalMessages);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your request. Please make sure the backend is running and try again.',
        sender: 'assistant',
        timestamp: new Date(),
        isError: true
      };
      
      const finalMessages = [...newMessages, errorMessage];
      setMessages(finalMessages);
      
      if (currentChatId) {
        updateChatMessages(currentChatId, finalMessages);
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Chat management functions
  const createNewChat = (firstMessage) => {
    const newChat = {
      id: Date.now(),
      title: firstMessage.slice(0, 50) + (firstMessage.length > 50 ? '...' : ''),
      messages: [],
      timestamp: new Date().toLocaleString(),
      createdAt: new Date()
    };
    setChatHistory(prev => [newChat, ...prev]);
    return newChat.id;
  };

  const updateChatMessages = (chatId, messages) => {
    setChatHistory(prev => 
      prev.map(chat => 
        chat.id === chatId ? { ...chat, messages } : chat
      )
    );
  };

  const deleteChat = (chatId) => {
    setChatHistory(prev => prev.filter(chat => chat.id !== chatId));
    if (currentChatId === chatId) {
      setCurrentChatId(null);
      setMessages([]);
      setCurrentView('welcome');
    }
  };

  const selectChat = (chatId) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      setCurrentChatId(chatId);
      setMessages(chat.messages);
      setCurrentView('chat');
      setSidebarOpen(false);
    }
  };

  const saveMessage = (message) => {
    setSavedMessages(prev => [...prev, { ...message, savedAt: new Date() }]);
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
    setCurrentChatId(null);
    setInputMessage('');
  };

  const handleLogoClick = () => {
    setCurrentView('welcome');
  };

  const handleQuickAction = (action) => {
    const quickMessages = {
      pcr_help: "I'm having trouble with PCR amplification. Can you help me troubleshoot?",
      protocol: "Can you recommend a standard protocol for DNA extraction?",
      literature: "Find recent papers about CRISPR applications in gene therapy",
      calculate: "How do I calculate the molarity of a solution?"
    };
    
    if (quickMessages[action]) {
      sendMessage(quickMessages[action]);
    }
  };

  const handleRegenerateMessage = (message) => {
    // Find the user message that prompted this response
    const messageIndex = messages.findIndex(m => m.id === message.id);
    if (messageIndex > 0) {
      const userMessage = messages[messageIndex - 1];
      if (userMessage.sender === 'user') {
        sendMessage(userMessage.text);
      }
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputMessage(suggestion);
  };

  // Helper functions
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
        <div className="chat-header-left">
          <button className="toggle-sidebar" onClick={() => setSidebarOpen(!sidebarOpen)}>
            <Menu className="w-5 h-5" />
          </button>
          <div className="chat-title">Conversation</div>
        </div>
        <div className="chat-settings">
          <button className="settings-btn" onClick={() => exportChat(messages, 'bioquery-chat')} title="Export Chat">
            <Download className="w-4 h-4" />
          </button>
          <button className="settings-btn" title="Settings">
            <Settings className="w-4 h-4" />
          </button>
          <button className="new-chat-button" onClick={handleNewChat}>
            <Plus className="w-4 h-4" />
            New Chat
          </button>
        </div>
      </div>
      <div className="messages-container">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`message message-enhanced ${message.sender} ${message.isError ? 'error' : ''}`}
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
              <MessageActions 
                message={message}
                onCopy={() => {}}
                onRegenerate={handleRegenerateMessage}
                onSave={saveMessage}
              />
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant">
            <div className="message-content">
              <div className="typing-indicator">
                <span>BioQuery is thinking</span>
                <div className="typing-dots">
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
                  <div className="typing-dot"></div>
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
      <ChatHistorySidebar 
        chatHistory={chatHistory}
        currentChatId={currentChatId}
        onSelectChat={selectChat}
        onDeleteChat={deleteChat}
        isOpen={sidebarOpen}
        onToggle={() => setSidebarOpen(!sidebarOpen)}
      />
      
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
  <QuickActions onQuickAction={handleQuickAction} />
  
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
  
  <EnhancedInput 
    value={inputMessage}
    onChange={(e) => setInputMessage(e.target.value)}
    onSubmit={handleSubmit}
    disabled={isLoading || apiStatus !== 'connected'}
    suggestions={commonSuggestions}
    onSuggestionClick={handleSuggestionClick}
  />
</footer>
      </div>
    </div>
  );
}

export default App;